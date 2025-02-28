from odoo import api, fields, models


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    employee_transport_allowance = fields.Float(string='Transport Allowance')
    employee_telephone_allowance = fields.Float(string='Telephone Allowance')
