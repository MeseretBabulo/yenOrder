# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _


class DelayReasonWizard(models.TransientModel):
    _name = 'delay.reason.wizard'
    _description = 'Delay Reason Wizard'

    delay_reason = fields.Char('Delay Reason')

    def save_delay_reason(self):
        dict_data = self.env.context.get('kwargs')
        dict_data.update({'delay_reason': self.delay_reason})
        if self.env.context.get('create_attendance'):
            pass
            # self.env.context['partner_id'] = self.e
        return self.env['project.task'].with_context(from_delay_reason=True).timesheet_sign_in(dict_data)