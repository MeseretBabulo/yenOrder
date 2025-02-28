# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    via_company_type = fields.Selection([
                                ('pa', 'PA'),
                                ('nj', 'NJ')],
                                string="Company Type",
                                copy=False)
    remove_project_stage_type = fields.Boolean(string="Remove Project Task Stage")
    # is_remove_ribbon = fields.Boolean(string="Remove Ribbon")
