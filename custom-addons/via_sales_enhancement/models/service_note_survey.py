# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _


class ViaServiceNoteSurvey(models.Model):
    _name = 'via.service.note.survey'
    _description = "Via Service Note Survey"

    name = fields.Char("Name")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
