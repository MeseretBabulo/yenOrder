# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################
import datetime
import pytz
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class DrugDosesSchedule(models.Model):
    _name = "drug.doses.schedule"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Drug Doses Schedule"
    _rec_name = 'medication_id'
    _order = "id desc"

    active = fields.Boolean(string="Active",
                                default=True)
    medi_presc_line_id = fields.Many2one('medical.prescription.line',
        string="Medical Prescription Line#")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    patient_id = fields.Many2one(related="medi_presc_line_id.patient_id",
                                store=True)
    medication_id = fields.Many2one(related="medi_presc_line_id.medication_id",
                                store=True)
    color = fields.Integer("Color", compute='_compute_color')
    medical_officer_id = fields.Many2one('res.users',
                                    string="Medication Person",
                                    tracking=1)
    is_dose_added = fields.Boolean(string="Dose Added",
                                    default=False,
                                    copy=False)
    is_prn = fields.Boolean(string="Is PRN", related="medi_presc_line_id.is_prn",
                                  default=False,
                                  copy=False)
    prn_reason = fields.Text(string="PRN Reason")
    administered_time = fields.Datetime(string="Administered Time", track_visibility="onchange")
    instructions = fields.Text(string="Instructions")
    comment = fields.Text(string="Comment", tracking=1)
    drug_dose_id = fields.Many2one('medicine.doses.line',
                                string="Drug Dose")
    # dose = fields.Float(string="Give Amount/Quantity")
    team_id = fields.Many2one('crm.team',
                                    string="Team")
    user_id = fields.Many2one('res.users',
                    default=lambda self: self.env.user,
                    string="User")
    strength = fields.Char(string="Strength")
    drug_time = fields.Float(string="Time")
    is_discontinued = fields.Boolean(string="Is Discontinued")
    initials_select = fields.Selection([('ma', 'Medical Assistant'),
                                        ('pa', 'Physician Assistant')], String="Initials", tracking=1)
    initials_id = fields.Many2one('drug.initials', string="Drug Not Administered")
    # am_pm = fields.Selection([
    #                         ('am', 'AM'),
    #                         ('pm', 'PM')
    #                         ],
    #                         string="AM/PM")

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        args = args or []
        if self.env.user.sale_team_id:
            if self.env.user.has_group('base.group_system'):
                args += []
            else:
                args += [('team_id', '=', self.env.user.sale_team_id.id)]
        else:
            args += [('team_id', 'in', [])]
        return super(DrugDosesSchedule, self).search(args, offset, limit, order, count=count)

    def unlink(self):
        if self.medical_officer_id:
            raise ValidationError(_("You cannot delete a record which is already administered"))
        return super(DrugDosesSchedule, self).unlink()

    def name_get(self):
        result = []
        for drug_dose in self:
            if drug_dose.medication_id and drug_dose.patient_id:
                name = (drug_dose.medication_id and drug_dose.medication_id.name) +  \
                       (drug_dose.medication_id and ' - ' + drug_dose.medication_id.product_ndc) + \
                       '(' + (drug_dose.patient_id and drug_dose.patient_id.name) + ')'
                result.append((drug_dose.id, name))
        return result

    # def action_drug_dose_schedule(self):
    #     self.env.cr.execute("""select dds.id from medical_prescription_line mpl 
    #                         left join medical_admin_record mar on mpl.mar_id=mar.id 
    #                         left join drug_doses_schedule dds on mpl.id=dds.medi_presc_line_id
    #         where mar.state != 'inactive' and mpl.date_med_end IS NULL""")
    #     drug_dose_schedule_ids = [data[0] for data in self.env.cr.fetchall() if data]
    #     return True

    def add_dose_line(self,  comment='', initial_id=False):
        dose_obj = self.env['medicine.doses.line']
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        initials = ''
        for drug_dose in self:
            if drug_dose.is_dose_added:
                raise ValidationError(_("""Dose already administered to the patient."""))
            if drug_dose.start_date.astimezone(local).date() > fields.Date.today():
                raise ValidationError(_("""Dose not Given Before Dose Date."""))
            start_time = drug_dose.start_date.astimezone(local) - timedelta(hours=1)
            end_time = drug_dose.end_date.astimezone(local) + timedelta(hours=1)
            is_mar_admin = self.env.user.has_group('via_mar.group_mar_admin')
            if not self.is_prn and not is_mar_admin and not (start_time < fields.Datetime.now().astimezone(local) and \
                    fields.Datetime.now().astimezone(local) < end_time):
                raise ValidationError(_("You cannot administer a dose outside the specified timing window, Please contact to Administrator"))
                # raise ValidationError(_("You can not able to dose administered, Please contact to Administrator"))
            # if not (fields.Datetime.now().astimezone(local) > start_time and \
            #     fields.Datetime.now().astimezone(local) < start_time) or \
            #         (drug_dose.start_date.astimezone(local) < end_time and \
            #                 drug_dose.start_date.astimezone(local) > end_time):

            if drug_dose.is_discontinued:
                raise ValidationError(_("""Current Dose is discontinued"""))
            initials_name = self.env.user.name.title().split(' ')
            if initial_id:
                initial_id = self.env['drug.initials'].browse(int(initial_id))
                initials = initial_id.code
            else:
                initials = ''.join([data[0] for data in initials_name if data])
            dose_id = dose_obj.create({
                            'med_presc_id': drug_dose.medi_presc_line_id.id,
                            'drug_dose_schedule_id': self.id,
                            'medical_office_id': self.env.user.id,
                            # 'medication_date': fields.Datetime.now(),
                            'title': 'MR.',
                            'initials': str(initials),
                            'comment': drug_dose.comment,
                            'dose_time': drug_dose.drug_time,
                            'initials_id': initial_id.id if initial_id else False
                            })
            drug_dose.medical_officer_id = self.env.user.id
            drug_dose.administered_time = fields.Datetime.now()
            drug_dose.drug_dose_id = dose_id
            drug_dose.comment = comment if comment else ''
            drug_dose.initials_id = initial_id.id if initial_id else False
            dose_id.compute_day_day_time()
            drug_dose.is_dose_added = True
        return True

    def _compute_color(self):
        for drug_dose in self:
            if drug_dose.initials_id:
                drug_dose.color = 31
            elif drug_dose.drug_dose_id:
                drug_dose.color = 22
            else:
                drug_dose.color = drug_dose.patient_id.color or 2

    @api.onchange('comment')
    def onchange_comment(self):
        if self.drug_dose_id:
            self.drug_dose_id.comment = self.comment

    @api.onchange('patient_id')
    def onchange_patient(self):
        for drug_dose_id in self:
            medication_record_id = self.env['medical.admin.record'].sudo().search([('resident_partner_id', '=', drug_dose_id.patient_id.id),
                                                                                   ('state', '=', 'approved')], limit=1)
            if medication_record_id and medication_record_id.medication_prescription_line_ids:
                medication_ids = medication_record_id.medication_prescription_line_ids.filtered(lambda line: line.is_prn == True).mapped('medication_id').ids
                return {'domain': {'medication_id': [('id', 'in', medication_ids)]}}
            else:
                return {'domain': {'medication_id': [('id', 'in', [])]}}

    @api.model
    def create(self, vals):
        if 'patient_id' in vals and 'medication_id' in vals and not 'medi_presc_line_id' in vals:
            if 'start_date' in vals:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                current_date = fields.Datetime.now().astimezone(local).date()
                start_date = datetime.strptime(vals.get('start_date'), '%Y-%m-%d %H:%M:%S').astimezone(local).date()
                if start_date > current_date or start_date < current_date:
                    raise ValidationError(_("For PRN Medication You Can not create Future and Past Record"))
            medication_record_id = self.env['medical.admin.record'].sudo().search(
                [('resident_partner_id', '=', vals.get('patient_id')),
                 ('state', '=', 'approved')], limit=1)
            prescription_line_id = medication_record_id.medication_prescription_line_ids.filtered(
                lambda line: line.is_prn == True and line.medication_id.id == vals.get('medication_id'))
            if prescription_line_id:
                vals.update({'medi_presc_line_id': prescription_line_id.id})
        return super(DrugDosesSchedule, self).create(vals)

    def write(self, vals):
        if self.start_date and 'start_date' in vals:
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            start_date = datetime.strptime(vals.get('start_date'), '%Y-%m-%d %H:%M:%S').astimezone(local).date()
            old_start_date = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').astimezone(local).date()
            if old_start_date > start_date or old_start_date < start_date:
                raise ValidationError(_("You can not change the date of the record"))
        return super(DrugDosesSchedule, self).write(vals)

