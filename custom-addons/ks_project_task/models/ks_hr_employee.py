from odoo import fields, models, api


class HREmployeeInheritBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    employee_ssn_temp_base = fields.Char("Employee SSN")
