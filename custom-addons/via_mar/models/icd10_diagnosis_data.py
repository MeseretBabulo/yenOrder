# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api


class ICD10DiagnosisData(models.Model):
    _name = "icd10.diagnosis.data"
    _rec_name = 'description'
    _description = "ICD10 Diagnosis Data"

    code = fields.Char(string="Code",
                            copy=False)
    # block = fields.Char(string="Block")
    mar_id = fields.Many2one('medical.admin.record',
                                string="MAR#",
                            copy=False)
    description = fields.Char(string="Description",
                            copy=False)
    is_imported = fields.Boolean(string="Imported?",
                            copy=False)
    # is_billable = fields.Boolean(string="Is Billable?")