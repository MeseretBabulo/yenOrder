# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    team_id = fields.Many2one('crm.team', string="Team")
    type = fields.Selection(selection_add=[('opportunity', 'Opportunity')], ondelete={'opportunity': 'cascade'})
    stage_id = fields.Many2one('crm.stage', string='Stage', copy=False, ondelete='restrict')

