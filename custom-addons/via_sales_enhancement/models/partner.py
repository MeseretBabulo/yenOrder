# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    via_service_note_count = fields.Integer(compute='_compute_service_note_count', string='# Service Notes')
    analytic_account_id = fields.Many2one('account.analytic.account',
                                string='Analytic Account')


    def _compute_service_note_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        for partner in self:
            task_data = self.env['via.service.note'].search_count([('partner_id', '=', partner.id),
                                                                   ('company_id', '=', self.env.company.id)])
            partner.via_service_note_count = task_data
