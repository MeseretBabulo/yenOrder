# -*- coding: utf-8 -*-

from odoo import api, models, _
import datetime


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.model
    def _get_report_values(self, docids, data=None):
        active_id = self.env.context.get('active_id')
        print("active_id", active_id)
        payslip_ids = self.env['hr.payslip'].search([('state', '=', 'done'),('payslip_run_id','=', active_id)])
        datetime_object = datetime.datetime.strptime(str(data.get('payroll_month')), "%m")
        month_name = datetime_object.strftime("%B")
        datas = []
        for res in payslip_ids:
            if res.move_id and res.date_from.month == data.get('payroll_month'):
                move_id = res.move_id.line_ids.filtered(lambda r: r.credit)
                total = []
                account = ''
                for rec in move_id:
                    total.append(rec.credit)
                    account = rec.account_id.name
                datas.append({
                    'employee_id': res.employee_id.name,
                    'total_pay': sum(total),
                    'account': account
                })
        print(datas)

        docargs = {
            'data': datas,
            'month_name': month_name

        }
        return docargs
