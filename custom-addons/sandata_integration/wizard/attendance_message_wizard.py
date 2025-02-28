# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models,tools, _


class AttendanceConfirmMessageWizard(models.TransientModel):
    _inherit = 'attendance.confirm.message.wizard'
    # _description = ''

    def confirm_with_term_condition(self):
        dict_data = self.env.context.get('kwargs')
        dict_data.update({'temperature': self.temperature})
        return self.env['project.task'].with_context(from_note=True).timesheet_sign_in(dict_data)
