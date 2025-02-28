from odoo import fields, models


class PlanningSlotInherit(models.Model):
    _inherit = "planning.slot"

    resource_id = fields.Many2one('resource.resource', 'Support Partner',
                                  domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                #   group_expand='_read_group_resource_id'
                                  )


