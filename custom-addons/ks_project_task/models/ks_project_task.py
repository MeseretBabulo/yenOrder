from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ViaAttendanceLineInherit(models.Model):
    _inherit = 'via.attendance.line'

    visit_id = fields.Char("Visited id", compute='_compute_visit_id')

    def _compute_visit_id(self):
        for record in self:
            record.visit_id = str(record.id)

    def create_attendance_update_with_id(self):
        return {
            'name': _('Create Attendance Wizard Update'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.create.attendance.update',
            'context': {
                'default_task_id': self.task_id.id,
                'default_visit_id': self.id
            }
        }


class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    reason_for_appointment = fields.Char(string='Reason for appointment')
    medical_facilities = fields.Many2one('res.partner', string='Medical facility', domain="[('is_company', '=', True)]")
    specialist = fields.Many2one('ks_project_task.specialist', string="specialist")
    medical_form = fields.Binary('Medical Form')
    medical_form_name = fields.Char(string='Medical form name')
    project_task_calender_id = fields.Many2one('project.task', string='Task',  compute="_compute_task_calender_id")
    result_recommendation = fields.Text(string='Result & Recommendation')
    next_appointment = fields.Selection([
        ('one_month', '1 months'),
        ('two_month', '2 months'),
        ('three_month', '3 months'),
        ('four_month', '4 months'),
        ('five_month', '5 months'),
        ('six_month', '6 months'),
        ('seven_month', '7 months'),
        ('eight_month', '8 months'),
        ('nine_month', '9 months'),
        ('ten_month', '10 months'),
        ('eleven_month', '11 months'),
        ('twelve_month', '12 months')
    ])
    next_appointment_date_start = fields.Datetime('Next Appointment Date')
    next_appointment_date_end = fields.Datetime('Next Appointment Date End')
    medical_appointment = fields.Boolean('medical Appointment')

    @api.onchange('next_appointment')
    def next_appointment_date_calculate(self):
        appointment_mapping = {
            'one_month': 1,
            'two_month': 2,
            'three_month': 3,
            'four_month': 4,
            'five_month': 5,
            'six_month': 6,
            'seven_month': 7,
            'eight_month': 8,
            'nine_month': 9,
            'ten_month': 10,
            'eleven_month': 11,
            'twelve_month': 12,
        }

        for rec in self:
            if rec.planned_date_begin and rec.next_appointment in appointment_mapping:
                months_to_add = appointment_mapping[rec.next_appointment]
                rec.next_appointment_date_start = rec.planned_date_begin + relativedelta(months=months_to_add)
                rec.next_appointment_date_end = rec.planned_date_end + relativedelta(months=months_to_add)

    def _compute_task_calender_id(self):
        for rec in self:
            rec.project_task_calender_id = rec.id

    def schedule_activity_medical(self):
        model_id = self.env['ir.model']._get('project.task').id
        medical_type_id = self.env['mail.activity.type'].search([('medical_type', '=', True)], limit=1).id
        if not medical_type_id:
            create_vals = {
                        'activity_type_id': medical_type_id,
                        'summary': "Appointment Verification",
                        'automated': True,
                        'note': "",
                        'res_model_id': model_id,
                        'res_id': self.id,
                        'date_deadline': fields.Date.today(),
                        'user_id': self.project_id.user_id.id or self.env.user.id
                    }
            self.env['mail.activity'].create(create_vals)
        template_id = self.env.ref('ks_project_task.email_template_verification_request')
        template_id.send_mail(self.id, force_send=True)

    def stage_move_to_verified_stage(self):
        if self.result_recommendation and self.next_appointment:
            verify_id = self.env['project.task.type'].search([('verify_stage', '=', True)]).id
            if not verify_id:
                raise ValidationError(_("There is No Verification Stage Defined please Select in Stages menu"))
            self.stage_id = verify_id
            # create new record
            vals = {
                    'name': self.name,
                    'user_ids': [(6, 0, self.user_ids.ids)],
                    'partner_id': self.partner_id.id,
                    'physician_id': self.physician_id.id,
                    'partner_phone': self.partner_phone,
                    'reason_for_appointment': self.reason_for_appointment,
                    'medical_facilities': self.medical_facilities.id,
                    'specialist': self.specialist.id,
                    'medical_form': self.medical_form,
                    'medical_form_name': self.medical_form_name,
                    'planned_date_begin': self.next_appointment_date_start,
                    'planned_date_end': self.next_appointment_date_end,
                    "medical_appointment": True,
            }
            self.env['project.task'].create(vals)
        else:
            raise ValidationError(_("Please Fill Result & Recommendation and "
                                  "Next Appointment Fields First then you can Approve. "))

    def navigate_lati_long(self):
        if self.medical_facilities and self.medical_facilities.street and self.medical_facilities.city:
            street = self.medical_facilities.street if self.medical_facilities.street else ""
            street2 = self.medical_facilities.street2 if self.medical_facilities.street2 else ""
            city = self.medical_facilities.city if self.medical_facilities.city else ""
            country = self.medical_facilities.country_id.name if self.medical_facilities.country_id else ""
            address = self._format_address(street, street2, city, country)
            origin_address = self._get_origin_address()
            url = "https://www.google.com/maps/dir/?api=1&origin=%s&destination=%s" % (origin_address, address)
        elif self.physician_id and self.physician_id.street and self.physician_id.city:
            street = self.physician_id.street if self.physician_id.street else ""
            street2 = self.physician_id.street2 if self.physician_id.street2 else ""
            city = self.physician_id.city if self.physician_id.city else ""
            country = self.physician_id.country_id.name if self.physician_id.country_id else ""
            address = self._format_address(street, street2, city, country)
            origin_address = self._get_origin_address()
            url = "https://www.google.com/maps/dir/?api=1&origin=%s&destination=%s" % (origin_address, address)
        else:
            raise ValidationError(_("There is No Latitude and Longitude"))
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def _get_origin_address(self):
        origin_street = self.partner_id.street if self.partner_id.street else ""
        origin_street2 = self.partner_id.street2 if self.partner_id.street2 else ""
        origin_city = self.partner_id.city if self.partner_id.city else ""
        origin_country = self.partner_id.country_id.name if self.partner_id.country_id else ""
        origin_address = self._format_address(origin_street, origin_street2, origin_city, origin_country)
        return origin_address

    def _format_address(self, street, street2, city, country):
        # Filter out empty values and join the remaining parts with commas
        address_parts = [part for part in [street, street2, city, country] if part]
        return ', '.join(address_parts)

