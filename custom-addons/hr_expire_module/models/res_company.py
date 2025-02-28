from odoo import api, fields, models

class Company(models.Model):
    _inherit = 'res.company'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)    
    additional_phone = fields.Char(related='partner_id.additional_phone',store=True, readonly=False, translate=True)
    additional_website = fields.Char(related='partner_id.additional_website', store=True, readonly=False, translate=True)
    building = fields.Char(related='partner_id.building', store=True, readonly=False, translate=True)
    floor = fields.Integer(related='partner_id.floor', store=True, readonly=False)
    whatsapp = fields.Char(related='partner_id.whatsapp', store=True, readonly=False, translate=True)

