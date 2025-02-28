# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
# from iteration_utilities import unique_everseen


class MedicalAdminRecord(models.Model):
    _name = "medical.admin.record"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _rec_name = 'id_number'

    resident_partner_id = fields.Many2one('res.partner',
                                string="Resident's Name")
    date_of_birth = fields.Date(string="Date of Birth")
    id_number = fields.Char(string="ID Number",
                            copy=False)
    physician_id = fields.Many2one('res.partner',
                                    string="Physician")
    allergies = fields.Char(string="Allergies")
    general_diagnoses = fields.Char(string="Diagnoses")

    company_id = fields.Many2one('res.company',
                    default=lambda self: self.env.company,
                    string="Company")
    medication_prescription_line_ids = fields.One2many('medical.prescription.line',
                                        'mar_id',
                                        string="Prescription lines")
    note = fields.Text(string="Text")
    dietary_guidelines_note = fields.Text(string="Dietary Guidelines")
    state = fields.Selection([
                                ('draft', 'Draft'),
                                ('approved', 'Approved'),
                                ('inactive', 'Inactive')],
                                default='draft',
                                tracking=1,
                                string="State")
    is_approver = fields.Boolean(compute="check_is_approver",
                                string="Is Approver?")
    approved_by_user_id = fields.Many2one('res.users',
                                string="Approved By",
                                copy=False)
    approved_date = fields.Datetime("Approve Date")
    report_date = fields.Date(string="Report Date")
    allergies_status = fields.Char(string="Allergy Status")
    drug_allergy_status = fields.Char(string="Drug Allergy Status")

    def name_get(self):
        result = []
        if self.env.context.get('from_gantt', False):
            for mar_rec in self:
                name = (mar_rec.id_number or 'NA') + ' / ' + (mar_rec.resident_partner_id and mar_rec.resident_partner_id.name or 'NA')
                result.append((mar_rec.id, name))
        return result

    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
    #     if args is None:
    #         args = []
    #     if self.env.context.get('from_gantt', False):
    #         id_num_mar_ids = [rec.id for rec in self.env['medical.admin.record'].search([('id_number', '=ilike', name)]) if rec]
    #         mar_ids = [rec.id for rec in self.env['medical.admin.record'].search([('resident_partner_id.name', 'ilike', name)]) if rec]
    #         if mar_ids or id_num_mar_ids:
    #             args.append(('id', 'in', list(set((mar_ids+id_num_mar_ids)))))
    #     return super(MedicalAdminRecord, self)._name_search(name='', args=args, operator=operator, limit=100, name_get_uid=name_get_uid)

    def action_approve(self):
        for mar_rec in self:
            active_record_counts = self.search_count([('state', '=', 'approved'),
                                                      ('resident_partner_id', '=', mar_rec.resident_partner_id.id),
                                                      ('id', '!=', mar_rec.id)])
            if active_record_counts > 0:
                raise ValidationError(_("At a Time One record can be Approved"))
            mar_rec.write({
                        'approved_by_user_id': self.env.user.id,
                        'state': 'approved',
                        'approved_date': fields.datetime.now()
                        })
        return True

    def set_to_draft(self):
        for mar_rec in self:
            mar_rec.state = 'draft'
        return True

    def set_to_done(self):
        for mar_rec in self:
            mar_rec.state = 'inactive'
        return True

    @api.onchange('resident_partner_id')
    def onchange_resident_partner_id(self):
        if self.resident_partner_id:
            self.date_of_birth = self.resident_partner_id.date_of_birth

    @api.depends()
    def check_is_approver(self):
        for mar_rec in self:
            if self.env.user.has_group('via_mar.group_mar_admin'):
                mar_rec.is_approver = True
            else:
                mar_rec.is_approver = False

    @api.constrains('id_number')
    def check_id_number(self):
        id_numbers = [data.id_number for data in self.search([
                                                ('id_number', '!=', ''),
                                                ('company_id', '=', self.env.company.id)])]
        for med_rec in self:
            if med_rec.id_number and id_numbers.count(med_rec.id_number) > 1:
                raise ValidationError(_("""ID number should be unique."""))

    #To check same medicine is not added in the other active record with the same patient.
    @api.constrains('medication_prescription_line_ids', 'resident_partner_id')
    def check_medication_prescription_line(self):
        presc_line_obj = self.env['medical.prescription.line']
        for presc_line in self.medication_prescription_line_ids:
            med_presc_lines = presc_line_obj.search([
                                ('mar_id.state', '!=', 'inactive'),
                                ('medication_id', '=', presc_line.medication_id and\
                                    presc_line.medication_id.id),
                                ('patient_id', '=', presc_line.patient_id.id)
                                ])
            if len(med_presc_lines) > 1:
                raise ValidationError(_("""Medicine %s already used in other record."""%(presc_line.medication_id and\
                                                        presc_line.medication_id.name)))

    def get_current_date_time_and_user(self):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        return {'current_time': datetime.now().astimezone(local),
                'current_user': self.env.user.name}

    def get_medical_diagnosis_initials(self, line_data):
        initials_list = []
        medical_diagnosis_list = []
        medical_diagnosis_initials_dict = {'medical_diagnosis': [], 'medical_initials': []}
        for line in line_data:
            for icd10_data in line.icd10_diagnosis_details_ids:
                medical_diagnosis_list.append({'coding_type': 'ICD-10',
                                               'code': icd10_data.diagnosis_id.code,
                                               'description': icd10_data.description,
                                               'dsm': '',
                                               'billable': ''})
            for deses_data in line.medical_doses_line_ids:
                if deses_data.medical_office_id:
                    employee_id = self.env['hr.employee'].search([('user_id', '=', deses_data.medical_office_id.id)])
                    if employee_id:
                        initials_list.append({'initials': deses_data.initials,
                                              'name': deses_data.medical_office_id.name +
                                                      (employee_id.job_id and ', ' + employee_id.job_id.name or '')})
        # initials_list = list(unique_everseen(initials_list))
        # medical_diagnosis_list = list(unique_everseen(medical_diagnosis_list))
        medical_diagnosis_initials_dict['medical_initials'] = initials_list
        medical_diagnosis_initials_dict['medical_diagnosis'] = medical_diagnosis_list
        return medical_diagnosis_initials_dict

    def get_slot_time(self, line):
        line_id = self.browse(line)
        slot_list = []
        if line_id:
            wizard_drug_doses_id = self.env['schedule.drug.doses'].sudo().search([('med_presc_id', '=', line_id.id)])
            if wizard_drug_doses_id:
                for each_drug in wizard_drug_doses_id.dose_schedule_ids:
                    slot_list.append(str(each_drug.drug_time) + ' ' + each_drug.am_pm)
        return slot_list


class MedicalPrescriptionLine(models.Model):
    _name = "medical.prescription.line"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _rec_name = 'med_code'

    mar_id = fields.Many2one('medical.admin.record',
                                    string="MAR#")
    patient_id = fields.Many2one(related='mar_id.resident_partner_id',
                                    string="Resident's Partner",
                                    store=True)
    physician_id = fields.Many2one('res.partner',
                                   string="Physician")
    medication_id = fields.Many2one('open.fda.drug.data',
                                    ondelete="restrict",
                                    string="Name of Medication")
    schedule_wiz_id = fields.Many2one('schedule.drug.doses',
                                        string="Schedule ID#")
    med_code = fields.Char(string="Medicine Code")
    date_med_started = fields.Date(string="Date Med Started",
                                       tracking=True)
    date_med_end = fields.Date(string="Date Med End",
                                   tracking=True)
    diagnosis = fields.Char(string="DIAGNOSIS/PURPOSE/CONDITION")
    strength = fields.Char(string="Strength")
    dosage_form = fields.Selection([
                            ('pills', 'Pills'),
                            ('drops', 'Drops'),
                            ('ointment', 'Ointment'),
                            ('liquid', 'Liquid'),
                            ('other', 'Other')],
                            string="Dosage Form")
    other_dosage_form = fields.Char(string="Other Dose Form")
    quantity = fields.Char("Quantity")
    dose = fields.Float(string="Dose")
    dose_unit_id = fields.Many2one('uom.uom',
                                        string="UOM")
    route_of_admin = fields.Selection([
                            ('mouth', 'Mouth'),
                            ('eye', 'Eye'),
                            ('ear', 'Ear'),
                            ('other', 'Other')],
                            string="Route Of Admin")
    other_admin_route = fields.Char(string="Other Admin Route")
    admin_frequency_id = fields.Many2one('frequency.of.admin',
                                        string="Frequency of Admin", required=True)
    prescribed_admin_times = fields.Integer(string="Prescribed admin times",
                                            default=1)
    prescribed_time = fields.Char(string="Prescribed Time")
    duration_of_prescription = fields.Char(string="Duration of Prescription")
    special_precautions = fields.Char(string="Special Precautions")
    medical_doses_line_ids = fields.One2many('medicine.doses.line',
                                            'med_presc_id',
                                            string="Medical Doses")
    icd10_diagnosis_details_ids = fields.One2many('icd10.diagnosis.details',
                                        'med_presc_id',
                                        string="Diagnosis Details")
    color = fields.Integer("Color", compute='_compute_color')
    is_dose_added = fields.Boolean(string="Dose Added",
                                   default=False,
                                   copy=False)
    is_dose_schedule = fields.Boolean(string="Dose Schedule",
                                      default=False,
                                      copy=False)
    is_prn = fields.Boolean(string="Is PRN",
                                      default=False,
                                      copy=False)
    prn_reason = fields.Text(string="PRN Reason")
    dose_instructions = fields.Text(string="Instructions")
    drug_time = fields.Float(string="Time")
    discontinued_by = fields.Many2one('res.users', string="Discontinued By")
    discontinued_date = fields.Date(string="Discontinued Date")


    @api.constrains('date_med_started', 'date_med_end')
    def _med_date_started_and_ended(self):
        for record in self:
            if not record.is_prn:
                if (record.date_med_started and record.date_med_end and record.date_med_started > record.date_med_end):
                    raise ValidationError(_("""Date Med Started cannot be greater than Date Med End."""))
                elif record.date_med_started and datetime.strptime(str(record.date_med_started), DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
                    raise ValidationError('Please select a Date Med Started equal/or greater than the current date')
                elif record.date_med_end and datetime.strptime(str(record.date_med_end), DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
                    raise ValidationError('Please select a Date Med End equal/or greater than the current date')

    @api.constrains('medication_id', 'date_med_started', 'date_med_end')
    def _medication_uni(self):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        for each_line in self:
            medicine_record_id = self.search([('medication_id', '=', each_line.medication_id.id),
                                              ('mar_id', '=', each_line.mar_id.id),
                                              ('id', '!=', each_line.id)],
                                              order='id desc',
                                              limit=1)
            if medicine_record_id:
                raise ValidationError(_("Medicine %s Already Selected!")%(each_line.medication_id and\
                                                            each_line.medication_id.name))

    # @api.model
    # def create(self, vals):
    #     res = super(MedicalPrescriptionLine, self).create(vals)
    #     if res.dose == 0.0:
    #         raise ValidationError(_("""For medicine %s, Dose value cannot be zero.""") % (res.medication_id.name))
    #     return res

    # def write(self, vals):
    #     res = super(MedicalPrescriptionLine, self).write(vals)
    #     for presc_line in self:
    #         if presc_line.dose == 0.0:
    #             raise ValidationError(
    #                 _("""For medicine %s, dose value cannot be zero.""") % (presc_line.medication_id.name))
    #     return res

    def name_get(self):
        result = []
        for presc_line in self:
            if presc_line.medication_id:
                name = (presc_line.medication_id and presc_line.medication_id.name) + '(' + (presc_line.med_code or 'NA') + ')'
                result.append((presc_line.id, name))
        return result

    @api.depends('patient_id.color')
    def _compute_color(self):
        for presc_line in self:
            presc_line.color = presc_line.patient_id.color

    @api.onchange('medication_id')
    def onchange_medication_id(self):
        if self.medication_id:
            self.med_code = self.medication_id.product_ndc


    @api.onchange('admin_frequency_id')
    def onchange_admin_frequency_id(self):
        if self.onchange_admin_frequency_id:
            self.prescribed_admin_times = self.admin_frequency_id.frequency_count
        else:
            self.prescribed_admin_times = 0

    def open_wizard_drug_doses_schedule(self):
        for presc_line in self:
            form_view_id = self.env.ref('via_mar.view_schedule_drug_doses_form').id
            return {
                'name': _('MAR'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'schedule.drug.doses',
                'view_id': form_view_id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'default_start_date':  presc_line.date_med_started and str(presc_line.date_med_started) or datetime.today(),
                            'default_end_date': presc_line.date_med_end and str(presc_line.date_med_end) or datetime.today(),
                            }
            }
        return True

    def manual_schedule_action(self):
        for presc_line in self:
            form_view_id = self.env.ref('via_mar.view_manual_drug_doses_schedule_form').id
            return {
                'name': _('MAR'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'drug.doses.schedule',
                'view_id': form_view_id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'flags': {'form': {'action_buttons': False}},
                'context': {'default_medication_id': presc_line.medication_id.id,
                            'default_strength': presc_line.strength,
                            'default_patient_id': presc_line.patient_id.id,
                            'default_medi_presc_line_id': presc_line.id,
                            }
            }
        return True



    def discontinue_action(self):
        drug_schedule_ids = self.env['drug.doses.schedule'].sudo().search([('medi_presc_line_id', '=', self.id),
                                                                           ('start_date', '>=', fields.datetime.now().date().strftime('%Y-%m-%d 00:00:00'))])
        drug_schedule_ids.unlink()
        # for drug_schedule in drug_schedule_ids:
        #     drug_schedule.is_discontinued = True

            # drug_schedule.active = False
        self.discontinued_by = self.env.user.id
        self.discontinued_date = fields.datetime.now()

    def open_medical_prescription(self):
        for presc_line in self:
            form_view_id = self.env.ref('via_mar.view_prescription_line_form').id
            return {
                'name': _('Prescription Line'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'medical.prescription.line',
                'view_id': form_view_id,
                'res_id': presc_line.id,
                'context': "{'create': 0, 'edit': 0, 'delete': 0}",
                'type': 'ir.actions.act_window',
            }
        return True

    def add_dose_line(self):
        dose_obj = self.env['medicine.doses.line']
        initials = ''
        for each_line in self:
            initials_name = self.env.user.name.title().split(' ')
            initials = ''.join([data[0] for data in initials_name if data])
            dose_id = dose_obj.create({
                            'med_presc_id': each_line.id,
                            'medical_office_id': self.env.user.id,
                            'medication_date': fields.Datetime.now(),
                            'title': 'MR.',
                            'initials': str(initials)
                            })
            dose_id.compute_day_day_time()
            each_line.is_dose_added = True
        return True


class MedicineDosesLine(models.Model):
    _name = "medicine.doses.line"
    _rec_name = 'title'

    med_presc_id = fields.Many2one('medical.prescription.line',
                                    string="Med# Prescription")
    medical_office_id = fields.Many2one('res.users',
                                    string="Medication Person")
    drug_dose_schedule_id = fields.Many2one('drug.doses.schedule', string="Dose Schedule")
    medication_date = fields.Datetime(string="Medication Date", related="drug_dose_schedule_id.administered_time", store=True)
    title = fields.Char(string="Title")
    initials = fields.Char(string="Initials")
    medication_day = fields.Selection([('sunday', 'Sunday'),
                            ('monday', 'Monday'),
                            ('tuesday', 'Tuesday'),
                            ('wednesday', 'Wednesday'),
                            ('thursday', 'Thursday'),
                            ('friday', 'Friday'),
                            ('saturday', 'Saturday')],
                            string="Medication Day")
    day_time = fields.Selection([('am', 'AM'),
                            ('md', 'MD'),
                            ('pm', 'PM'),
                            ('ev', 'EV')],
                            string="Day Time")
    comment = fields.Text(string="Comment")
    dose_time = fields.Float()
    initials_id = fields.Many2one('drug.initials', string="Drug Not Administered")

    @api.onchange('medication_date')
    def compute_day_day_time(self):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        for dose_line in self:
            if dose_line.medication_date:
                dose_line.medication_day = dose_line.medication_date.strftime("%A").lower()
                medication_date_utc = datetime.strftime(pytz.utc.localize(datetime.strptime(dose_line.medication_date.strftime("%Y-%m-%d %H:%M:%S"),
                    DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")
                medication_date_utc = datetime.strptime(medication_date_utc, "%Y-%m-%d %H:%M:%S")
                if medication_date_utc.hour <= 5 and medication_date_utc.minute <= 59 and medication_date_utc.second <= 59:
                    dose_line.day_time = 'am'
                elif medication_date_utc.hour <= 11 and medication_date_utc.minute <= 59 and medication_date_utc.second <= 59:
                    dose_line.day_time = 'md'
                elif medication_date_utc.hour <= 17 and medication_date_utc.minute <= 59 and medication_date_utc.second <= 59:
                    dose_line.day_time = 'pm'
                elif medication_date_utc.hour <= 23 and medication_date_utc.minute <= 59 and medication_date_utc.second <= 59:
                    dose_line.day_time = 'ev'
                else:
                    dose_line.day_time = ''
            else:
                dose_line.medication_day = ''
                dose_line.day_time = ''


class ICD10DiagnosisDetails(models.Model):
    _name = "icd10.diagnosis.details"
    _description = "ICD10 Diagnosis Details"

    diagnosis_id = fields.Many2one('icd10.diagnosis.data',
                                ondelete="restrict",
                                string="Diagnosis Description")
    diagnosis_description = fields.Char(string="Diagnosis")
    description = fields.Char(string="Description")
    med_presc_id = fields.Many2one('medical.prescription.line',
                                string="Prescription Line#")
    # is_billable = fields.Boolean(string="Is Billable?")

    @api.onchange('diagnosis_id')
    def onchange_diagnosis_id(self):
        if self.diagnosis_id:
            self.diagnosis_description = self.diagnosis_id.code
        else:
            self.diagnosis_description = ''


class VIADiagnosisDetails(models.Model):
    _name = "via.diagnosis.details"
    _description = "VIA Diagnosis Details"

    diagnosis_id = fields.Many2one('icd10.diagnosis.data',
                                ondelete="restrict",
                                string="Diagnosis Description")
    diagnosis_description = fields.Char(string="Diagnosis")
    description = fields.Char(string="Description")
    partner_id = fields.Many2one('res.partner',
                                string="Person Supported",
                                default=lambda self:
                                self.env.context.get('active_id') or
                                False)
    mci_number = fields.Char(string="MedicaidID Number",
                                 copy=False)

    @api.model
    def create(self, vals):
        if vals.get('mci_number'):
            partner_id = self.env['res.partner'].search([('mci_number', '=', vals.get('mci_number'))],
                limit=1)
            if partner_id:
                vals.update({'partner_id': partner_id.id})
        res = super(VIADiagnosisDetails, self).create(vals)
        return res

    @api.onchange('diagnosis_id')
    def onchange_diagnosis_id(self):
        if self.diagnosis_id:
            self.diagnosis_description = self.diagnosis_id.code
        else:
            self.diagnosis_description = ''

    @api.onchange('mci_number')
    def onchange_mci_number(self):
        if self.mci_number:
            partner_id = self.env['res.partner'].search(
                [('mci_number', '=', self.mci_number)],
                limit=1)
            if partner_id:
                self.partner_id = partner_id.id
            else:
                self.partner_id = False


class FrequencyOfAdmin(models.Model):
    _name = "frequency.of.admin"
    _description = "Frequency Of Admin"

    name = fields.Char(string="Name")
    frequency_count = fields.Integer(string="Frequency")
