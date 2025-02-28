# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SalesApprovalSteps(models.Model):
    _name = "sales_approval.sales_approval_steps"
    _description = "Sales Approval Steps"
    _order = "sequence"

    company = fields.Many2one(
        'res.company',
        string="Company",
        required=True
    )
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='draft', required=True)
    active = fields.Boolean(default=True)
    employee_line_ids = fields.One2many('employee.line', 'sales_approvers', string="Employee Lines")
    
    def action_activate(self):
        records = self.env['sales_approval.sales_approval_steps'].search([])
        current_company = self.company 
        other_exist = False
        for record in records:
            if current_company == record.company:
                if int(self.id) != int(record.id):
                    if record.state == "active":
                        other_exist = True
        if other_exist:
            raise UserError(
                _(
                    "Another Active Approval Step exists.\n"
                    "Cancel that before making another approval step active"
                ))
        else:
            self.write({'state': 'active'})

    def action_deactivate(self):
        self.write({'state': 'inactive'})
    
class EmployeeLine(models.Model):
    _name = 'employee.line'
    _description = 'Employee Line'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    users_id = fields.Many2one('res.users', string="Users", required=True)
    sales_approvers = fields.Many2one('sales_approval.sales_approval_steps', string="Sales Step", ondelete='cascade')
   
SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('waiting_approval', 'Waiting for Approval'),
    ('sent', "Quotation Sent"),
    ('sale', "Sales Order"),
    ('cancel', "Cancelled"),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_approval_status = fields.Char(
        string="Sales Approval Status",
        compute="_compute_sales_approval_status",
        store=False  # Ensures it's always computed dynamically
    )

    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    
    current_approver_id = fields.Many2one('res.users', string='Current Approver')

    approval_history_ids = fields.One2many('sale.approval.history', 'sale_id', string='Approval History')
    
    is_current_user_approver = fields.Boolean(
        string="Is Current User Approver?",
        compute="_compute_is_current_user_approver",
        store=False  # Ensures it updates dynamically without being stored in the database
    )


    @api.model
    def default_get(self,fields_list):
        res = super(SaleOrder,self).default_get(fields_list)
        self._compute_sales_approval_status()
        self._compute_is_current_user_approver()
        return res

    @api.depends_context("uid")
    def _compute_is_current_user_approver(self):
        """Check if the logged-in user is the current approver."""
        for record in self:
            record.is_current_user_approver = record.current_approver_id.id == self.env.uid

    @api.depends_context("uid")  # Ensures recalculation when viewed
    def _compute_sales_approval_status(self):
        """Dynamically fetches the Sales Approval setting"""
        param_value = self.env["ir.config_parameter"].sudo().get_param("sale.sales_approval", "False")
        for record in self:
            record.sales_approval_status = param_value
            
    @api.onchange("sales_approval_status")
    def _onchange_sales_approval_status(self):
        """Trigger UI update when Sales Approval Status changes."""
        return {"value": {"sales_approval_status": self.sales_approval_status}}


    def action_request_approval(self):
        approval_steps = self.env['sales_approval.sales_approval_steps'].search([
            ('company', '=', self.company_id.id),
            ('state', '=', 'active')
        ], limit=1)
        
        if not approval_steps or not approval_steps.employee_line_ids:
            raise UserError(_("No active approval process found for this company."))

        first_approver = approval_steps.employee_line_ids.sorted('sequence')[0]
        self.write({
            'state': 'waiting_approval',
            'current_approver_id': first_approver.users_id.id
        })
        
        # Create first approval history record
        self.env['sale.approval.history'].create({
            'sale_id': self.id,
            'approver_id': first_approver.users_id.id,
            'state': 'pending',
            'sequence': first_approver.sequence
        })

    def action_approve(self):
        if self.env.user.id != self.current_approver_id.id:
            raise UserError(_("You are not authorized to approve at this stage."))

        approval_steps = self.env['sales_approval.sales_approval_steps'].search([
            ('company', '=', self.company_id.id),
            ('state', '=', 'active')
        ], limit=1)

        current_approval = self.approval_history_ids.filtered(
            lambda r: r.approver_id.id == self.env.user.id and r.state == 'pending'
        )
        current_approval.write({
            'state': 'approved',
            'approval_date': fields.Datetime.now()
        })

        # Find next approver
        approved_sequences = self.approval_history_ids.filtered(
            lambda r: r.state == 'approved').mapped('sequence')
        next_approvers = approval_steps.employee_line_ids.filtered(
            lambda r: r.sequence not in approved_sequences
        ).sorted('sequence')

        if next_approvers:
            next_approver = next_approvers[0]
            self.write({'current_approver_id': next_approver.users_id.id})
            self.env['sale.approval.history'].create({
                'sale_id': self.id,
                'approver_id': next_approver.users_id.id,
                'state': 'pending',
                'sequence': next_approver.sequence
            })
        else:
            self.write({
                'state': 'sale',
                'current_approver_id': False
            })

    def action_reject(self):
        if self.env.user.id != self.current_approver_id.id:
            raise UserError(_("You are not authorized to reject at this stage."))

        current_approval = self.approval_history_ids.filtered(
            lambda r: r.approver_id.id == self.env.user.id and r.state == 'pending'
        )
        current_approval.write({
            'state': 'rejected',
            'approval_date': fields.Datetime.now()
        })
        self.write({
            'state': 'draft',
            'current_approver_id': False
        })
        
    def action_activate(self):
        res = super(SaleOrder, self).action_activate()
        
        # Get all approval steps
        approval_steps = self.env['sales.approval.steps'].search([
            ('active', '=', True)
        ], order='sequence')

        # Create approval history records
        for step in approval_steps:
            self.env['sale.approval.history'].create({
                'sequence': step.sequence,
                'sale_id': self.id,
                'step_id': step.id,
                'approver_id': step.approver_id.id,
                'state': 'pending'
            })
        
        return res

class SaleApprovalHistory(models.Model):
    _name = 'sale.approval.history'
    _description = 'Sale Approval History'
    _rec_name = 'sequence'
    _order = 'sequence'

    sale_id = fields.Many2one('sale.order', string='Sale Order')
    sequence = fields.Integer(string='Sequence')
    # sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    step_id = fields.Many2one('sales.approval.steps', string='Approval Step')
    approver_id = fields.Many2one('res.users', string='Approver')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', readonly=True)
    approval_date = fields.Datetime('Approval Date', readonly=True)
    comments = fields.Text('Comments', readonly=True)

    _sql_constraints = [
        ('unique_sequence_per_sale_order', 
         'unique(sale_id, sequence)', 
         'Sequence must be unique per sale order!')
    ]