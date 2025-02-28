from datetime import date

import werkzeug
from odoo import fields, models, api
from odoo.exceptions import UserError


class SurveyUserInputInherit(models.Model):
    _inherit = ['survey.user_input', 'mail.thread', 'mail.activity.mixin']
    _name = 'survey.user_input'

    state = fields.Selection([
        ('new', 'Pending Correction'),
        ('in_progress', 'To Submit'),
        ('done', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled'),], string='Status', default='new', readonly=True, tracking=True)

    cancel_state = fields.Selection([('cancel', 'Cancel')])
    mobile = fields.Char('Mobile')
    survey_evv = fields.Boolean('Survey EVV', compute='_compute_survey_evv')

    name_of_person_supported = fields.Many2one('res.partner', string="Name of person supported")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    ma_number = fields.Char("MA#")
    mci_number = fields.Char("MCI#")
    start_date_time = fields.Datetime("Start Date/Time", compute='_compute_date_time')
    end_date_time = fields.Datetime("END Date/Time", compute='_compute_date_time')
    analytic_line_id = fields.Many2one("account.analytic.line", "Analytic line id")
    child_line_location = fields.Many2one('res.partner', string="Location", compute='_compute_date_time')
    approved_date = fields.Date("Approved date")
    project_manager = fields.Many2one('res.users', 'Validation Manager')
    ks_sms = fields.Integer('ks SMS', default=0)
    ks_billable = fields.Boolean('Billable', default=False)

    @api.constrains('state')
    def _onchange_state(self):
        if self.state == 'done':
            # email for approval that new survey is added
            template_id = self.env.ref('ks_project_task.survey_order_approval_email_new')
            email_values = {
                'email_to': self.project_manager.login,
                'email_from': self.env.ref('base.user_admin').email,
            }
            template_id.send_mail(self.id, email_values=email_values, force_send=True)

        if self.state == 'approved':
            if not self.employee_id.work_email:
                message = f"<b>{self.employee_id.name} has No Email Address</b>"
                self.message_post(body=message)
            else:
                template_id = self.env.ref('ks_project_task.survey_order_approved_email')
                email_values = {
                    'email_to': self.employee_id.work_email,
                    'email_from': self.env.ref('base.user_admin').email,
                }
                template_id.send_mail(self.id, email_values=email_values, force_send=True)

    @api.model
    def create(self, vals):
        time_sheet_id = self.env['account.analytic.line'].search([], order="create_date desc", limit=1)
        valss = {
            # 'start_date_time': time_sheet_id.check_in_time,
            # 'end_date_time': time_sheet_id.check_out_time,
            'analytic_line_id': time_sheet_id.id,
            'name_of_person_supported': time_sheet_id.project_id.partner_id.id,
            'employee_id': time_sheet_id.employee_id.id,
            'project_manager': time_sheet_id.project_id.user_id.id,
        }
        vals.update(valss)

        return super(SurveyUserInputInherit, self).create(vals)

    def _compute_date_time(self):
        for rec in self:
            if rec.analytic_line_id:
                rec.start_date_time = rec.analytic_line_id.check_in_time
                rec.end_date_time = rec.analytic_line_id.check_out_time
                if rec.analytic_line_id.child_line_location:
                    rec.child_line_location = rec.analytic_line_id.child_line_location
                else:
                    rec.child_line_location = None
            else:
                rec.start_date_time = None
                rec.end_date_time = None
                rec.child_line_location = None

    def _compute_survey_evv(self):
        self.survey_evv = self.survey_id.evv

    def cancel_btn(self):
        self.write({'state': 'cancel'})

    def approve_btn(self):
        self.write({'state': 'approved'})
        today_date = date.today()
        self.write({'approved_date': today_date})

    def reset_to_approve(self):
        self.write({'state': 'in_progress'})

    def to_approve_btn(self):
        self.write({'state': 'done'})

    def submit_button(self):
        self.write({'state': 'in_progress'})

    def send_message(self):
        if not self.employee_id and not self.employee_id.mobile_phone:
            raise UserError("Emplyee is not selected or Mobile Number is not set")
        self.ks_sms += 1
        phone_number = self.employee_id.work_phone
        if not phone_number:
            phone_number = self.employee_id.mobile_phone
        self.write({'state': 'new'})
        return {
            'type': 'ir.actions.act_window',
            'name': "Send SMS Text Message",
            'res_model': 'sms.composer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_recipient_single_description': self.employee_id.name,
                'default_recipient_single_number_itf': phone_number,
                'default_res_model': 'survey.user_input',
                'default_mass_keep_log': True,
                'default_sms_template_checker': True,
                'default_number_field_name': 'mobile',
            }
        }

    def ks_send_message(self):
        if not self.employee_id and not self.employee_id.mobile_phone:
            raise UserError("Emplyee is not selected or Mobile Number is not set")
        phone_number = self.employee_id.work_phone
        if not phone_number:
            phone_number = self.employee_id.mobile_phone
        return {
            'type': 'ir.actions.act_window',
            'name': "Send SMS Text Message through Action",
            'res_model': 'sms.composer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_id': self.id,
                'default_recipient_single_description': self.employee_id.name,
                'default_recipient_single_number_itf': phone_number,
                'default_res_model': 'survey.user_input',
                'default_mass_keep_log': True,
                'default_sms_template_checker': True,
                'default_number_field_name': 'mobile',
            }
        }

    def ks_incomplete_survey_emails_data(self):
        pending_surveys = self.env['survey.user_input'].search([('state', '=', 'in_progress')])
        # email for doing survey which are in pending state
        for rec in pending_surveys:
            template_id = rec.env.ref('ks_project_task.survey_order_to_complete_email')
            email_values = {
                'email_to': rec.employee_id.work_email,
                'email_from': rec.env.ref('base.user_admin').email,
            }
            template_id.send_mail(rec.id, email_values=email_values, force_send=True)

    def get_survey_url_mail(self):
        url = werkzeug.urls.url_join(self.survey_id.get_base_url(), self.survey_id.get_start_url()) if self.survey_id else False
        return url
