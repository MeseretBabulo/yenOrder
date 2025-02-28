from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sales_approval = fields.Boolean(string='Sales Approval')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['sales_approval'] = self.env['ir.config_parameter'].sudo().get_param('sale.sales_approval', False)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('sale.sales_approval', self.sales_approval)
        # Get the custom group
        group = self.env.ref("sales_approval_settings.group_sales_approval_menu", raise_if_not_found=False)
        if group:
            if self.sales_approval:
                group.sudo().write({"users": [(4, self.env.user.id)]})  # Grant access
            else:
                group.sudo().write({"users": [(5, 0, 0)]})  # Remove all users