from odoo import fields, models, api


class PlanningSlotInherit(models.Model):
    _inherit = 'planning.slot'

    person_supported = fields.Many2one('res.partner', 'Person Supported', compute='_compute_person_supported',
                                       default=False)
    available_resource_ids = fields.Many2many('resource.resource', compute='_compute_available_resource_ids')
    contact_id = fields.Many2one('res.partner', 'Location')
    contact_ids = fields.Many2many('res.partner', string='Address')
    navigate_to_lag_lat = fields.Char('Navigate To', compute='_compute_navigate_to_lag_lat')

    @api.onchange('resource_id')
    def _onchange_resource_id(self):
        for record in self:
            if record.resource_id:
                role_ids = record.resource_id.employee_id.planning_role_ids.ids
                return {'domain': {'role_id': [('id', 'in', role_ids)]}}
            else:
                return {'domain': {'role_id': []}}

    def _compute_person_supported(self):
        for rec in self:
            if rec.project_id.partner_id:
                rec.person_supported = rec.project_id.partner_id
                rec.contact_ids = [(6, 0, rec.person_supported.child_ids.ids)]
            else:
                rec.person_supported = False

    @api.depends('available_resource_ids', 'resource_id')
    def _compute_available_resource_ids(self):
        """
        Compute function to get only employees based on selected role
        """
        if self.role_id:
            self.available_resource_ids = self.role_id.employee_ids.resource_id.ids
        else:
            all_resource_ids = self.env['resource.resource'].search([])
            self.available_resource_ids = all_resource_ids

    @api.onchange('role_id')
    def onchange_resource_id(self):
        if self.template_id and self.template_id.resource:
            employee = self.template_id.resource
            self.resource_id = employee.resource_id.id

    def name_get(self):
        result = []
        for record in self:
            if record.project_id:
                result.append((record.id, record.project_id.name))
            else:
                result.append((record.id, "Isp program is not available"))
        return result

    def _compute_navigate_to_lag_lat(self):
        for rec in self:
            url = ""
            if rec.contact_id and rec.contact_id.partner_latitude and rec.contact_id.partner_longitude:
                url = "https://www.google.com/maps/dir/?api=1&destination=%s,%s" % (
                    rec.contact_id.partner_latitude, rec.contact_id.partner_longitude)
            else:
                url = "https://www.google.com/maps/dir/?api=1&destination=%s,%s" % (
                    rec.person_supported.partner_latitude, rec.person_supported.partner_longitude)
            self.navigate_to_lag_lat = url
