# -*- coding: utf-8 -*-

from odoo import api, models, _
import datetime



class bank_payroll_report(models.Model):
    _name = 'bank.payroll.report'
    _inherit = 'hr.payslip.run'


    @api.model
    def _get_report_values(self, docids, data=None):
        payslip_ids = self.env['hr.payslip'].search([])
        print(payslip_ids)
        payroll_header_content = self.env['payroll.header'].search([('isActive', '=', True)])
        return payslip_ids
