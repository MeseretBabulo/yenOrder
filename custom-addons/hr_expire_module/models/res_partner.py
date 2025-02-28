from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    additional_phone = fields.Char(string='Additional Phone', translate=True)
    additional_website = fields.Char(string='Additional Website', translate=True)
    building = fields.Char(string='Currently working Building', translate=True)
    floor = fields.Integer(string='Floor')
    whatsapp = fields.Char(string='Whatsapp Number', translate=True)

