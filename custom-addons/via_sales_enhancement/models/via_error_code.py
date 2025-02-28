# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _


class ViaErrorCode(models.Model):
    _name = 'via.error.code'
    _description = "Via Error Code"

    name = fields.Char("Code")
    description = fields.Char("Description")
