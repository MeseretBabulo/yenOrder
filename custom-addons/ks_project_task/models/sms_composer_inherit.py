from odoo import fields, models, api


class SMSComposerInherit(models.TransientModel):
    _inherit = 'sms.composer'

    sms_template_checker = fields.Boolean('SMS template Checker', default=False)
    ks_template = fields.Many2one('sms.template', 'SMS template')

    @api.onchange('ks_template')
    def _on_change_ks_template(self):
        self.body = self.ks_template.body


