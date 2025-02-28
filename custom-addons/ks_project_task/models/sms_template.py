from odoo import fields, models, api


class SMSTemplate(models.Model):
    _name = 'sms.template.custom'

    name = fields.Char('Name')
    context = fields.Text(string="Context")
