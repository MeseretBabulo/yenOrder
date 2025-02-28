# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from random import randint
from odoo.exceptions import UserError, ValidationError


class ResidentialData(models.Model):
    _name = 'residential.data'
    _rec_name = 'person_support_id'

    person_support_id = fields.Many2one('res.partner', string="Name of Person Supported")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    residential_fire_drill_ids = fields.One2many('residential.fire.drill', 'residential_id',
                                                 string='Residential Fire Drill')
    residential_blood_glucose_ids = fields.One2many('residential.blood.glucose', 'residential_id',
                                                    string='Residential Blood Glucose')
    residential_intake_elimination_ids = fields.One2many('residential.intake.elimination', 'residential_id',
                                                         string='Residential intake elimination')
    residential_overnight_tracking_ids = fields.One2many('residential.overnight.tracking', 'residential_id',
                                                         string='Residential Overnight Tracking')
    residential_vital_signs_ids = fields.One2many('residential.vital.signs', 'residential_id',
                                                  string="Residential Vital Signs")
    residential_seizures_ids = fields.One2many('residential.seizures', 'residential_id', string='Residential Seizures')


class ResidentialFireDrill(models.Model):
    _name = 'residential.fire.drill'
    _rec_name = 'person_support_id'

    residential_id = fields.Many2one('residential.data', string="Residential")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    person_support_id = fields.Many2one('res.partner', related="residential_id.person_support_id", store=True,
                                        string="Name of Person Supported")
    partner_address_id = fields.Many2one('res.partner', string='Location')
    service_provider_id = fields.Many2one('res.users', string="Service Provider")
    service_received = fields.Char(string="Service/s Received")
    completed_by = fields.Many2one('res.users', string="Completed by")
    completed_datetime = fields.Datetime(string='Date Completed')
    is_sleep_hours = fields.Selection([('yes', 'Yes'),
                                       ('no', 'No')],
                                      string='Was the fire drill completed during asleep hours? Note: Asleep hours are from 11pm to 7am.')
    hypothetical_fire_location = fields.Char(string='Hypothetical Fire Location')
    exit_used = fields.Char(string='Exit Used')
    participants = fields.Char(string='List Participants')
    evacuation_time = fields.Char(string='Evacuation Time')
    designated_meeting_place = fields.Char(string='List Designated Meeting Place')
    evacuate_desig_meeting_place = fields.Selection([('yes', 'Yes'),
                                                      ('no', 'No')],
                                                     string='Did everyone evacuate to the designated meeting place within 2.5 minutes?')
    reason_for_desig_meeting = fields.Char(string='Reason for designated Meeting Place')
    place_of_alarm_sound = fields.Char(string='Where was the person supported when the alarm sounded?')
    assistance_to_evacuate = fields.Char(string='Describe any assistance needed to evacuate.')
    issue_encountered = fields.Char(string='Describe any issues encountered. Enter "None" if no issues were encountered')
    smoke_detector = fields.Char(string='List all smoke detectors by their location within the home:')
    smoke_detector_tested = fields.Selection([('yes', 'Yes'),
                                              ('no', 'No')],
                                             string='Were all smoke detectors tested?')
    smoke_detector_followup = fields.Char(string='List any smoke detectors that were not working & the follow-up required:')
    fire_extinguishers_and_lst_service_date = fields.Char(string='Enter each fire extinguishers location and date of last servicing: ')
    active_working_status = fields.Selection([('yes', 'Yes'),
                                              ('no', 'No')],
                                             string='Are all fire extinguishers currently showing "full" or active working status?')
    working_status_follow_up = fields.Char(string='If No, list any fire extinguishers that require attention & the plan for follow-up')
    fire_safety_equipment = fields.Selection([('yes', 'Yes'),
                                              ('no', 'No')],
                                             string="Does this person's home have any other fire safety equipment?")
    equipment_names = fields.Char(string='List equipment and whether it is in working order')
    water_temperature = fields.Char(string='Record the bathtub/shower water temperature. ')
    water_degree = fields.Selection([('yes', 'Yes'),
                                     ('no', 'No')],
                                    string="Is the bathtub/shower water temperature below 120 degrees?")
    water_degree_follow_up = fields.Char(string='If no, provide follow-up action plan. ')
    comment = fields.Text(string='Additional comments: ')


class ResidentialBloodGlucose(models.Model):
    _name = 'residential.blood.glucose'
    _rec_name = 'person_support_id'

    residential_id = fields.Many2one('residential.data', string="Residential")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    person_support_id = fields.Many2one('res.partner', related="residential_id.person_support_id", store=True,
                                        string="Name of Person Supported")
    service_received = fields.Char(string="Service/s Received")
    reported_by = fields.Many2one('res.users', string="Reported by")
    report_datetime = fields.Datetime(string='Date of Reading')
    value = fields.Integer(string='Value')
    notification_level = fields.Selection([('low', 'Low'),
                                           ('medium', 'Medium'),
                                           ('high', 'High')], string="Notification level")
    method_used = fields.Selection([('manual', 'Manual'),
                                    ('machine', 'Machine'),
                                    ('laboratory', 'Laboratory')], string="Method Used")
    fasting = fields.Selection([('yes', 'Yes'),
                                ('no', 'No')], string="Fasting?")
    time_since_last_meal = fields.Char(string='Time Since Last Meal ')
    insulin_given = fields.Selection([('yes', 'Yes'),
                                      ('no', 'No')], string="Insulin Given")
    nurse_or_doctor = fields.Selection([('yes', 'Yes'),
                                        ('no', 'No')], string="Nurse/Doctor Notified?")
    treatment_type = fields.Selection([('medication', 'Medication'),
                                       ('food', 'Food'),
                                       ('drink', 'Drink'),
                                       ('other', 'Other')], string="Treatment Type")
    other_treatment = fields.Char('Other treatment')
    residential_blood_glucose_medication_ids = fields.One2many('residential.blood.glucose.medication',
                                                               'residential_blood_glucose_id',
                                                              string='Blood Glucose Medication')
    comment = fields.Text(string='Comments')

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.notification_level == 'high':
            template_id = self.env.ref('via_mar.blood_glucose_notification_template')
            template_id.send_mail(res.id, force_send=True)
        return res

    def write(self, vals):
        if vals.get('notification_level') and vals.get('notification_level') == 'high':
            template_id = self.env.ref('via_mar.blood_glucose_notification_template')
            template_id.send_mail(self.id, force_send=True)
        return super().write(vals)

    def get_blood_glucose_data_url(self):
        blood_glucose_link = ''
        for blood_glucose_id in self:
            blood_glucose_link = "%s/web?db=%s#id=%s&menu_id=%s&action=%s&model=residential.data&view_type=form" % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                self.env.cr.dbname,
                blood_glucose_id.residential_id.id,
                self.env.ref('via_mar.menu_residential').id or False,
                self.env.ref('via_mar.action_residential_data').id or False)
        return blood_glucose_link

class ResidentialBloodGlucoseMedication(models.Model):
    _name = 'residential.blood.glucose.medication'

    residential_blood_glucose_id = fields.Many2one('residential.blood.glucose', string='Blood Glucose')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    person_support_id = fields.Many2one('res.partner',
                                        related="residential_blood_glucose_id.residential_id.person_support_id",
                                        store=True, string='Name of Person Supported')
    quantity = fields.Char(string='Give Amount/Quantity')
    route = fields.Char(string='Route')
    frequency = fields.Char(string='Frequency')


class ResidentialIntakeElimination(models.Model):
    _name = 'residential.intake.elimination'

    residential_id = fields.Many2one('residential.data', string="Residential")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    person_support_id = fields.Many2one('res.partner', related="residential_id.person_support_id", store=True,
                                        string="Name of Person Supported")
    service_received = fields.Char(string="Service/s Received")
    intake_elimination_date = fields.Datetime(string='Date')
    fluid_intake = fields.Char(string='Fluid intake (ml)')
    route = fields.Selection([('gt', 'G-tude'),
                              ('iv', 'IV'),
                              ('jt', 'J-tube'),
                              ('or', 'Oral'),
                              ('su', 'Supplement')], string="Route")
    meal_eaten = fields.Char(string='% of Meal Eaten')
    calorie_intake = fields.Char(string='Calorie Intake')
    fluid_void = fields.Char(string='Fluid Void (ml)')
    bowel_movement = fields.Selection([('0', '0'),
                                       ('1', '1'),
                                       ('2', '2'),
                                       ('3', '3'),
                                       ('4', '4'),
                                       ('5', '5'),
                                       ('6', '6'),
                                       ('7', '7'),
                                       ('8', '8'),
                                       ('9', '9')], string='Bowel Movement (BM)')
    bowel_aids = fields.Selection([('enema', 'Enema'),
                                   ('laxative', 'Laxative'),
                                   ('suppository', 'Suppository'),
                                   ('other', 'Other')], string='Bowel Aids')
    bowel_comment = fields.Text(string="Comment")
    reported_by = fields.Many2one('hr.employee', string="Reported by")
    entered_by = fields.Many2one('res.users', string="Entered By:")


class ResidentialOvernightTracking(models.Model):
    _name = 'residential.overnight.tracking'

    residential_id = fields.Many2one('residential.data', string="Residential")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    person_support_id = fields.Many2one('res.partner', related="residential_id.person_support_id", store=True,
                                        string="Name of Person Supported")
    overnight_tracking_date = fields.Date(string='Date')
    residential_overnight_tracking_question_ids = fields.One2many('residential.overnight.tracking.question',
                                                                  'residential_overnight_tracking_id',
                                                                  string='Overnight tracking Question')


class ResidentialOvernightTrackingQuestion(models.Model):
    _name = 'residential.overnight.tracking.question'

    residential_overnight_tracking_id = fields.Many2one('residential.overnight.tracking', string="Overnight Tracking")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    question = fields.Float(string='Question')
    am_pm = fields.Selection([('am', 'AM'),
                              ('pm', 'PM')], string="AM/PM")
    time_tracking_type = fields.Selection([('awake', 'Awake'),
                                           ('asleep', 'Asleep')], string='Time Tracking Type')

    @api.onchange('question')
    def onchange_question(self):
        if (self.question and self.question < 0.0 or self.question > 12.0):
            raise ValidationError(_("""Time should be between 00:01 to 11:59"""))


class ResidentialVitalSigns(models.Model):
    _name = 'residential.vital.signs'

    residential_id = fields.Many2one('residential.data', string="Residential")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    person_support_id = fields.Many2one('res.partner', related="residential_id.person_support_id", store=True,
                                        string="Name of Person Supported")
    service_received = fields.Char(string="Service/s Received")
    reported_by = fields.Many2one('res.users', string="Reported by")
    report_date = fields.Date(string='Date of Reading')
    notification_level = fields.Selection([('low', 'Low'),
                                           ('medium', 'Medium'),
                                           ('high', 'High')], string="Notification Level")
    temperature_value = fields.Char('Temperature Value')
    temperature_time = fields.Float('Time')
    temperature_am_pm = fields.Selection([('am', 'AM'),
                                          ('pm', 'PM')], string="AM/PM")
    temperature_site = fields.Selection([('axillary', 'Axillary'),
                                         ('nit', 'Non-invasive thermometer'),
                                         ('oral', 'Oral'),
                                         ('rectal', 'Rectal'),
                                         ('temporal', 'Temporal'),
                                         ('tympanic', 'Tympanic')], string='Site')
    pulse_value = fields.Char('Pulse Value')
    oxygen_saturation = fields.Char('Oxygen Saturation')
    pulse_time = fields.Float('Pulse Time')
    pulse_am_pm = fields.Selection([('am', 'AM'),
                                    ('pm', 'PM')], string="AM/PM")
    rhythm = fields.Selection([('irregular', 'Irregular'),
                               ('regular', 'Regular')], string='Rhythm')
    force = fields.Selection([('bounding', 'Bounding'),
                              ('normal', 'Normal'),
                              ('thready', 'Thready'),
                              ('weak', 'Weak')], string='Force')
    method_used = fields.Selection([('machine', 'Machine'),
                                    ('manual', 'Manual')], string='Method Used')
    respiration_value = fields.Char('Respiration Value')
    respiration_time = fields.Float('Respiration Time')
    respiration_am_pm = fields.Selection([('am', 'AM'),
                                          ('pm', 'PM')], string="AM/PM")
    lung_sound = fields.Selection([('clear', 'Clear'),
                                   ('rales', 'Rales'),
                                   ('phonchi', 'Phonchi'),
                                   ('wheeze', 'Wheeze'),
                                   ('other', 'Other')], string='Lung Sound')
    other_lung_sound = fields.Char('Other Lung Sound')
    systolic = fields.Char('Systolic')
    diastolic = fields.Char('Diastoloc')
    blood_pressure_time = fields.Float('Blood Pressure Time')
    blood_am_pm = fields.Selection([('am', 'AM'),
                              ('pm', 'PM')], string="AM/PM")
    blood_pressure_method_used = fields.Selection([('machine', 'Machine'),
                                                   ('manual', 'Manual')], string='Method Used')
    reaction = fields.Selection([('cooperative', 'Cooperative'),
                                 ('declined', 'Declined'),
                                 ('resisted', 'Resisted (Uncooperative)')], string='Reaction')
    comment = fields.Text(string='Comments')

    @api.onchange('temperature_time', 'pulse_time', 'respiration_time', 'blood_pressure_time')
    def onchange_time_value(self):
        if (self.temperature_time and self.temperature_time < 0.0 or self.temperature_time > 12.0) or \
                (self.pulse_time and self.pulse_time < 0.0 or self.pulse_time > 12.0) or \
                (self.respiration_time and self.respiration_time < 0.0 or self.respiration_time > 12.0) or \
                (self.blood_pressure_time and self.blood_pressure_time < 0.0 or self.blood_pressure_time > 12.0):
            raise ValidationError(_("""Time should be between 00:01 to 11:59"""))


class ResidentialSeizuresDesc(models.Model):
    _name = 'residential.seizures.desc'

    name = fields.Char('Name')


class ResidentialSeizuresBehaviour(models.Model):
    _name = 'residential.seizures.behaviour'

    name = fields.Char('Name')


class ResidentialSeizuresStaffAction(models.Model):
    _name = 'residential.seizures.staff.action'

    name = fields.Char('Name')


class ResidentialSeizures(models.Model):
    _name = 'residential.seizures'

    residential_id = fields.Many2one('residential.data', string="Residential")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    person_support_id = fields.Many2one('res.partner', related="residential_id.person_support_id", store=True,
                                        string="Name of Person Supported")
    service_received = fields.Char(string="Service/s Received")
    reported_by = fields.Many2one('res.users', string="Reported by")
    report_date = fields.Date(string='Date of Reading')
    notification_level = fields.Selection([('low', 'Low'),
                                           ('medium', 'Medium'),
                                           ('high', 'High')], string="Notification Level")
    seizure_occurred = fields.Selection([('yes', 'Yes'),
                                         ('no', 'No')], string='Seizure Occurred')
    location = fields.Selection([('community', 'Community'),
                                 ('familyvisit', 'Family Visit'),
                                 ('home', 'Home'),
                                 ('program', 'Program'),
                                 ('rl', 'Recreation / Leisure'),
                                 ('school', 'School'),
                                 ('unknown', 'Unknown'),
                                 ('vehicle', 'Vehicle'),
                                 ('work', 'Work'),
                                 ('other', 'Other')], string='Location')
    other_location = fields.Char('Other Location')
    begin_time = fields.Float('Begin Time')
    seizures_am_pm = fields.Selection([('am', 'AM'),
                                      ('pm', 'PM')], string="AM/PM")
    seizure_duration = fields.Char('Seizure Duration')
    description_ids = fields.Many2many("residential.seizures.desc", "seizures_desc_rel",
                                       "seizures_id", "seizures_desc_id", string="Description")
    behaviour_ids = fields.Many2many("residential.seizures.behaviour", 'seizures_behaviour_rel', 'seizures_id',
                                     'seizures_behaviour_id', string="Behaviour After Seizures")
    staff_action_ids = fields.Many2many("residential.seizures.staff.action", 'seizures_staff_action_rel', 'seizures_id',
                                        'seizures_staff_action_id', string="Staff Action")
    precipitating_factors = fields.Char('Precipitating Factors')
    resulting_injuries = fields.Char('Resulting Injuries')
    comment = fields.Text(string='Comments')

    @api.onchange('begin_time')
    def onchange_begin_time(self):
        if (self.begin_time and self.begin_time < 0.0 or self.begin_time > 12.0):
            raise ValidationError(_("""Time should be between 00:01 to 11:59"""))
