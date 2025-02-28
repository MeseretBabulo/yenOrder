from odoo import models, fields, _, api
from odoo.exceptions import UserError
from num2words import num2words
import logging
_logger  = logging.getLogger(__name__)

SALE_ORDER_STATE = [
        ('draft', 'Quotation'),
        ('contract_sent', 'Contract Sent'),
        ('sent', "Contract Sent"),
        ('sale', 'Customer Approved'),
        ('lc_opened', 'LC Opened'),
        ('preparation', 'Preparation'),
        ('certified', 'Certified'),
        ('shipped', 'Shipped to Djibouti'),
        ('docs_submitted', 'Documents Submitted'),
        ('payment_processed', 'Payment Processed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Boolean field to enable container calculation
    enable_container_calculation = fields.Boolean(string="Enable Container Calculation", default=False)
    
    # Container capacity (configurable, defaults to 18,000 KG)
    container_capacity = fields.Float(string="Container Capacity (KG)", default=18000.0)
    
    # Computed field for total required containers
    # required_containers = fields.Integer(string="Required Containers", compute="_compute_required_containers", store=True)
    is_direct_sales = fields.Boolean(string="Is Direct Sale", default=True)
    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=True,
        default='draft')

    # LC Fields
    lc_reference = fields.Char(string="LC Reference")
    customer_bank_id = fields.Many2one('res.bank', string="Customer's Bank")
    our_bank_id = fields.Many2one('res.bank', string="Our Bank")

    # Button Actions
    def action_send_contract(self):
        self.write({'state': 'contract_sent'})

    def action_customer_approve(self):
        self.write({'state': 'sale'})

    def action_lc_open(self):
        self.write({'state': 'lc_opened'})

    def action_prepare_shipment(self):
        self.write({'state': 'preparation'})

    def action_obtain_certificate(self):
        self.write({'state': 'certified'})

    def action_ship_djibouti(self):
        self.write({'state': 'shipped'})

    def action_submit_docs(self):
        """
        Opens a window to compose an email with the "Submit Docs to Bank" template loaded by default.
        """
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data._xmlid_lookup('sales_export.email_template_submit_docs')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'sale.order',
            'default_res_ids': self.ids,
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
        })

        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Sale Order Documents Submitted to Bank')
        self.write({'state': 'docs_submitted'})

        return {
            'name': _('Compose Email to Bank'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_process_payment(self):
        self.write({'state': 'payment_processed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_unlock(self):
        self.write({'state': 'draft'})
    # @api.depends('order_line.product_uom_qty', 'container_capacity', 'enable_container_calculation')
    # def _compute_required_containers(self):
    #     for order in self:
    #         if order.enable_container_calculation:
    #             total_weight = sum(line.product_uom_qty for line in order.order_line)
    #             if total_weight > 0 and order.container_capacity > 0:
    #                 order.required_containers = (total_weight // order.container_capacity) + (1 if total_weight % order.container_capacity > 0 else 0)
    #             else:
    #                 order.required_containers = 0
    #         else:
    #             order.required_containers = 0
                

    # @api.depends('order_line.product_uom_qty')
    # def _compute_containers(self):
    #     for order in self:
    #         weight_per_container = float(self.env['ir.config_parameter'].sudo().get_param('coffee_export.weight_per_container', 18000))
    #         total_weight = sum(order.order_line.mapped('product_uom_qty'))
    #         order.container_count = -(-total_weight // weight_per_container)  # Ceiling division

    

# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'

#     # Container number for each line (computed based on total weight)
#     container_number = fields.Integer(string="Container Number", compute="_compute_container_number", store=True)

#     @api.depends('product_uom_qty', 'order_id.container_capacity', 'order_id.enable_container_calculation')
#     def _compute_container_number(self):
#         for line in self:
#             if line.order_id.enable_container_calculation and line.order_id.container_capacity > 0:
#                 # Calculate cumulative weight and assign container numbers
#                 cumulative_weight = 0
#                 container_number = 1
#                 for record in line.order_id.order_line.sorted(key=lambda r: r.sequence):
#                     cumulative_weight += record.product_uom_qty
#                     if cumulative_weight > line.order_id.container_capacity:
#                         container_number += 1
#                         cumulative_weight = record.product_uom_qty
#                     record.container_number = container_number
#             else:
#                 line.container_number = 0