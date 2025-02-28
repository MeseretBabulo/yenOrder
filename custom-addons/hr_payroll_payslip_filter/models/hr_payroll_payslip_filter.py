from odoo import api, fields, models
from odoo.osv import expression


class HrPayrollPayslip(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    work_location_id = fields.Many2many('hr.work.location')
    # employee_id = fields.Many2many('hr.employee', string="Employees")
    # work_location_id = fields.Many2one(related='employee_id.work_location_id', string='Work Location')

    # work_location_id = fields.Char(related="hr.employee.base.work_location_id", string="Work Location")
    @api.depends('work_location_id')
    def _compute_employee_ids(self):
        for wizard in self:
            domain = wizard._get_available_contracts_domain()
            if wizard.work_location_id:
                domain = expression.AND([
                    domain,
                    [('work_location_id', 'in', self.work_location_id.ids)]
                ])
            wizard.employee_ids = self.env['hr.employee'].search(domain)