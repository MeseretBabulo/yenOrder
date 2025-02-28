from odoo import fields, models, api


class MailActivityTypeInherit(models.Model):
    _inherit = 'mail.activity.type'

    medical_type = fields.Boolean('Medical Type')
