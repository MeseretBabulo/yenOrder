from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    remove_project_stage_type = fields.Boolean(string="Remove Project Task Stage",
                                               related='company_id.remove_project_stage_type',
                                               readonly=False)
    # is_remove_ribbon = fields.Boolean(string="Remove Ribbon",
    #                                   related='company_id.is_remove_ribbon',
    #                                   readonly=False, config_parameter='via_crm.is_remove_ribbon')
