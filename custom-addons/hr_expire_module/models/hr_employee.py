from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_bank_account = fields.Many2one('account.journal', domain=[('type', '=', 'bank')],
                                            string='Employee Bank Account')
    emp_acc = fields.Char(string='Bank Account ', translate=True)