from odoo import models, fields, api

class ContactInfo(models.Model):
    _name = 'contact.info'
    _description = 'Contact Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    message = fields.Text(string='Message')
    partner_id = fields.Many2one('res.partner', string='Contact')
    
    def action_view_odoobot_messages(self):
        return {
            'name': 'OdooBot Messages',
            'type': 'ir.actions.act_window',
            'res_model': 'mail.mail',
            'view_mode': 'list,form',
            'domain': [('author_id.name', '=', 'OdooBot')],
            'context': {'search_default_message_type': 'email'},
        } 