# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _


class DrugInitials(models.Model):
    _name = 'drug.initials'

    name = fields.Char('Name')
    code = fields.Char('Code')
