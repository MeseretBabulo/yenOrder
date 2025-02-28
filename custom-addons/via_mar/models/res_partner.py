# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from random import randint


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_default_color(self):
        return randint(1, 17)

    color = fields.Integer("Color", default=_get_default_color)
    medication_prescription_line_ids = fields.One2many('medical.prescription.line',
                                        'patient_id',
                                        string="Prescription lines")
    via_drug_schedule_count = fields.Integer(compute='_compute_drug_schedule_count', string='# Drug Schedule')
    diagnoses_count = fields.Integer(
        compute='_compute_diagnoses_count',
        string='Diagnoses')

    def _compute_drug_schedule_count(self):
        for partner in self:
            drug_schedule_data = self.env['drug.doses.schedule'].search_count([('patient_id', '=', partner.id)])
            partner.via_drug_schedule_count = drug_schedule_data

    def _compute_diagnoses_count(self):
        for partner in self:
            diangoses_count = self.env['via.diagnosis.details'].search_count([
                    ('partner_id', '=', partner.id)])
            partner.diagnoses_count = diangoses_count

    def open_schedule_dose(self):
        if self.env.context.get('patient_id'):
            return {
                    'name': _('MAR'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'drug.doses.schedule',
                    'view_mode': 'calendar,tree,form',
                    'domain': [('patient_id', '=', self.env.context.get('patient_id'))]
            }

    def open_diagnosis_details(self):
        for partner in self:
            return {
                    'name': _('Diagnosis Details'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'via.diagnosis.details',
                    'view_mode': 'tree',
                    'context': {'new_partner_id': partner.id},
                    'domain': [('partner_id', '=', partner.id)]
            }