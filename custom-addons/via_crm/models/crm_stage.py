# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models


class CrmStage(models.Model):
    _inherit = "crm.stage"

    stage_type = fields.Selection([
                                        ('introduction', 'Introduction'),
                                        ('discussion', 'Discussion'),
                                        ('activation', 'Activation'),
                                        ]
                            ,string="Type",
                            copy=False)
