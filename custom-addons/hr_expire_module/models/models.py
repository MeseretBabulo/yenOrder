# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime as dt, date
from datetime import timedelta


class hr_expire_module(models.Model):
    _inherit = "hr.contract"

    @api.onchange('state')
    def _onchange_type_id(self):
        # if self.state == 'close':
        if self.state == 'verify':
            self.kanban_state = 'blocked'

    @api.model
    def probation_notification(self):
        contracts = self.env['hr.contract'].search([])
        for emp in contracts:
            if emp.trial_date_end:
                expire_notify_date = emp.trial_date_end - timedelta(days=10)
                if expire_notify_date == date.today():
                    body = "<p>Dear Sir/Madam,</p><p>This is to notify that the probationary period of <b> %s </b>expires with in 10 days. </p>" % (
                        emp.employee_id.name)
                    mail_values = {'subject': _('END OF PROBATION'),
                                   'body_html': body,
                                   'author_id': emp.env.user.partner_id.id,
                                   'email_from': emp.env.user.partner_id.email,
                                   'email_to': emp.employee_id.parent_id.work_email,
                                   }
                    self.env['mail.mail'].create(mail_values).send()

            probation_start_date = emp.date_start + timedelta(days=5)

