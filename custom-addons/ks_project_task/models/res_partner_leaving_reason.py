from odoo import fields, models, api


class ResPartnerLeavingReason(models.Model):
    _name = 'res.partner.leaving.reason'
    _description = 'Res Partner Leaving Reason'

    name = fields.Char(string="Name")
