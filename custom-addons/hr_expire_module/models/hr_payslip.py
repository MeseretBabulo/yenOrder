from odoo import api, fields, models


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    perpared = fields.Many2one('res.users', string="Prepared by")
    checked = fields.Many2one('res.users', string="Checked by")
    approved = fields.Many2one('res.users', string="Approved by")
    subject = fields.Text(string='subject', widget="text")
    body = fields.Html(string='Body',  sanitize_attributes=False)
    to = fields.Many2one('res.partner', string='To')
    ref = fields.Char(string='Reference')
    print_date = fields.Date(string='print Date')


