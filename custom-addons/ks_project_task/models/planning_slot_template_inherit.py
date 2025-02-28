from odoo import fields, models, api


class PlanningTemplate(models.Model):
    _inherit = 'planning.slot.template'

    resource = fields.Many2one('hr.employee',string="Resource")

    @api.onchange('resource')
    def _onchange_resource(self):
        if self.resource:
            planning_role_ids = self.resource.planning_role_ids.ids
            return {
                'domain': {
                    'role_id': [('id', 'in', planning_role_ids)]
                }
            }
        else:
            return {
                'domain': {'role_id': []}
            }

    @api.onchange('role_id')
    def _onchange_role_id(self):
        if self.role_id:
            employees = self.env['hr.employee'].search([('planning_role_ids', 'in', [self.role_id.id])])
            employee_ids = employees.ids
            return {
                'domain': {
                    'resource': [('id', 'in', employee_ids)]
                }
            }
        else:
            return {
                'domain': {
                    'resource': []
                }
            }
