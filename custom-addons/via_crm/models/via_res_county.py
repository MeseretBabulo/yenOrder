# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class VIAResCounty(models.Model):
    _name = "via.res.county"

    name = fields.Char(string="Name")
    state_id = fields.Many2one('res.country.state', 'State', required=True)