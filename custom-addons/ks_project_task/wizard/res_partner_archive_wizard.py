# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResPartnerArchiveWizard(models.TransientModel):
    _name = 'res.partner.archive.wizard'
    _description = 'Res Partner Archive Wizard'

    reason_of_leaving = fields.Many2one('res.partner.leaving.reason', string='Why they are leaving')
    logged_in_user = fields.Many2one('res.users', string='Who archived the person', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    date = fields.Date(string='Date', default=fields.Datetime.now)

    def action_archive(self):
        self.ensure_one()
        self.partner_id.write({'active': False})
        return {'type': 'ir.actions.act_window_close'}

