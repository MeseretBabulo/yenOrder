# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ViaServiceNotes(models.Model):
    _name = 'via.service.note'
    _description = 'Via Service Note'
    _rec_name = 'project_id'
    _inherit = 'mail.thread'
    _order = 'id desc'

    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string="Task")
    via_attendance_line_id = fields.Many2one('via.attendance.line', string="Attendance Line")
    partner_id = fields.Many2one('res.partner', string="Customer")
    note = fields.Text("Notes")
    outcome_phrase = fields.Html('Outcome Phrase')
    reason_for_outcome = fields.Text(string="Reason for Outcome")
    outcome_statement = fields.Text(string="Outcome Statement")
    actions_taken = fields.Text(string="Actions")
    progress_status = fields.Text(string="Progress")
    survey_answer = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('maintaining', 'Maintaining')], string="Answer")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    isp_id = fields.Many2one('via.isp', string="ISP")
    user_id = fields.Many2one('res.users', string="User")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,
                                  ondelete='cascade', index=True)
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')], default='draft', tracking=1,
                             string="State", track_visibility="onchange")
    project_manager_id = fields.Many2one(related="project_id.user_id", store=True, string="Project")
    # current_user = fields.Many2one('res.users', compute='_get_current_user')
    is_current_manager_user = fields.Boolean('User', compute="_get_current_user")
    account_analytic_line_id = fields.Many2one('account.analytic.line', string="Analytic Line")
    # approve by user store fields
    person_support_id = fields.Many2one('res.partner', string="Name of Person Supported")
    ma_number = fields.Char(string="MA#", related="partner_id.ma_number", copy=False)
    mci_number = fields.Char(string="MCI#", related="partner_id.mci_number", copy=False)
    service_delivery_date = fields.Date('Date of Service Delivery')
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')
    approved_date = fields.Datetime('Approved Date')
    approved_by = fields.Many2one('res.users', string="Approved By")
    location = fields.Char('Location')
    identity_proof = fields.Binary('Degree/license/certificate of person', compute='_compute_emp_certificate', store=True)
    identity_name = fields.Char('Degree/license/certificate of person', compute='_compute_emp_certificate', store=True)
    signature = fields.Binary(related="employee_id.user_id.sign_signature", string="Signature")
    score = fields.Selection([('yes', 'Yes'),
                              ('no', 'No'),
                              ('maintaining', 'Maintaining')], string='Score')
    description_of_activities = fields.Text('Description of Activities')
    comment = fields.Text('Comments')
    billable = fields.Selection([('yes', 'Yes'),
                                 ('no', 'No')], string='Billable/approved')

    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.update({'is_current_manager_user': False})
            if rec.project_id.user_id.id == self.env.user.id:
                rec.update({'is_current_manager_user': True})

    @api.depends('employee_id')
    def _compute_emp_certificate(self):
        for rec in self:
            rec.identity_proof = rec.employee_id.emp_certificate
            rec.identity_name = rec.employee_id.emp_certificate_name

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

    def service_note_action_approve(self):
        for note_rec in self:
            note_rec.write({'state': 'approved',
                            'approved_by': self.env.user.id,
                            'approved_date': fields.datetime.now()})
        return True
