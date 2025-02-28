# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class CrmTeam(models.Model):
    _inherit = "crm.team"

    crm_member_ids = fields.Many2many(
        'res.users', string='Salespersons')

    @api.depends('crm_team_member_ids.active')
    def _compute_member_ids(self):
        for team in self:
            team.member_ids = team.crm_team_member_ids.user_id
            team.crm_member_ids = team.crm_team_member_ids.user_id
