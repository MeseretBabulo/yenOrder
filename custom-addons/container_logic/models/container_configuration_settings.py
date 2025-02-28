from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResConfigContainerSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    container_measurement_logic = fields.Boolean(string='Enable Configuration Container Measurement Logic')
    

    @api.model
    def get_values(self):
        res = super(ResConfigContainerSettings, self).get_values()
        res['container_measurement_logic'] = self.env['ir.config_parameter'].sudo().get_param('sale.container_measurement_logic', False)
        return res

    def set_values(self):
        super(ResConfigContainerSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('sale.container_measurement_logic', self.container_measurement_logic)
        # Get the custom group
        group = self.env.ref("container_logic.group_weight_of_container", raise_if_not_found=False)
        if group:
            if self.container_measurement_logic:
                group.sudo().write({"users": [(4, self.env.user.id)]})  # Grant access
            else:
                group.sudo().write({"users": [(5, 0, 0)]})  # Remove all users