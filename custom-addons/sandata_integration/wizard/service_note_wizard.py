# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ViaServiceNotesWizard(models.TransientModel):
    _name = 'via.service.note.wizard'
    _description = 'Via Service Note Wizard'

    note = fields.Char('Notes')
    service_note_survey_ids = fields.One2many('via.service.note.survey.wizard', 'service_note_wizard_id')

    def save_note(self):
        if self.env.context.get('manual_timesheet_note'):
            if self.env.context.get('tasks') == None:
                account_analytic_line_id = self.env['account.analytic.line'].browse(self.env.context.get('default_account_analytic_line_id'))
                task_id = account_analytic_line_id.sudo().task_id
            else:
                task_id = self.env['project.task'].browse(int(self.env.context.get('tasks')))
            via_service_note_obj = self.env['via.service.note']
            if task_id:
                for survey in self.service_note_survey_ids:
                    via_service_note_id = via_service_note_obj.sudo().create({'project_id': task_id.project_id.id,
                                                                              'task_id': task_id.id,
                                                                              'partner_id': task_id.partner_id.id or False,
                                                                              'outcome_phrase': survey.outcome_phrase or '',
                                                                              'reason_for_outcome': survey.reason_for_outcome or '',
                                                                              'outcome_statement': survey.outcome_statement or '',
                                                                              'actions_taken': survey.actions_taken or '',
                                                                              'progress_status': survey.progress_status or '',
                                                                              'survey_answer': survey.survey_answer or '',
                                                                              'start_time': survey.start_time or 0,
                                                                              'end_time': survey.end_time or 0,
                                                                              'service_delivery_date': survey.service_delivery_date or False,
                                                                              'description_of_activities': survey.note or '',
                                                                              'note': survey.note or '',
                                                                              'isp_id': survey.isp_id.id,
                                                                              'account_analytic_line_id': self.env.context.get('default_account_analytic_line_id'),
                                                                              'employee_id': int(self.env.context.get('employee_id')),
                                                                              'user_id': self.env.user.id})
                    if via_service_note_id and via_service_note_id.account_analytic_line_id:
                        via_service_note_id.account_analytic_line_id.sudo().is_service_note = True

        else:
            dict_data = self.env.context.get('kwargs')
            dict_data['isp_data'] = []
            if self.service_note_survey_ids:
                for survey in self.service_note_survey_ids:
                    dict_data['isp_data'].append({'outcome_phrase': survey.outcome_phrase,
                                                  'reason_for_outcome': survey.reason_for_outcome or '',
                                                  'outcome_statement': survey.outcome_statement or '',
                                                  'actions_taken': survey.actions_taken or '',
                                                  'progress_status': survey.progress_status or '',
                                                  'isp_id': survey.isp_id.id,
                                                  'note': survey.note,
                                                  'start_time': survey.start_time or 0,
                                                  'end_time': survey.end_time or 0,
                                                  'service_delivery_date': survey.service_delivery_date or False,
                                                  'survey_answer': survey.survey_answer})

            return self.env['project.task'].with_context(from_note=True).timesheet_sign_out(dict_data)


class ViaServiceNoteSurveyWizard(models.TransientModel):
    _name = 'via.service.note.survey.wizard'
    _description = 'Via Service Note Survey Wizard'

    outcome_phrase = fields.Html('Outcome Phrase')
    note = fields.Text('Notes')
    survey_id = fields.Many2one('via.service.note.survey')
    isp_id = fields.Many2one('via.isp')
    survey_answer = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('maintaining', 'Maintaining')], string="Answer")
    service_note_wizard_id = fields.Many2one('via.service.note.wizard')
    account_analytic_line_id = fields.Many2one('account.analytic.line', string="Analytic Line")
    reason_for_outcome = fields.Text(string="Reason for Outcome")
    outcome_statement = fields.Text(string="Outcome Statement")
    actions_taken = fields.Text(string="Actions")
    progress_status = fields.Text(string="Progress")
    service_delivery_date = fields.Date('Date of Service Delivery')
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')

    @api.onchange('start_time')
    def onchange_start_time(self):
        if (self.start_time and self.start_time < 0.0 or self.start_time > 24.0):
            raise ValidationError(_("""Start time should be between 00:01 to 23:59"""))

    @api.onchange('end_time')
    def onchange_end_time(self):
        if (self.start_time and self.end_time and self.end_time < self.start_time):
            raise ValidationError(_("""End time Should be greater than start time"""))
        if (self.end_time and self.end_time < 0.0 or self.end_time > 24.0):
            raise ValidationError(_("""End time should be between 00:01 to 23:59"""))