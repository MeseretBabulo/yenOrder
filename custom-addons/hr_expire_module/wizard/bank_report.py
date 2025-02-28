from odoo import models, fields, api, _


class BankPayroll(models.TransientModel):
    _name = 'bank.payroll'
    _description = "Bank Payroll"


    payroll_month = fields.Date(string="Payroll Month")

    def action_print(self):
        data = {
            'payroll_month': self.payroll_month.month
        }
        return self.env.ref('hr_expire_module.action_report_bank_payroll').report_action(self, data=data)
