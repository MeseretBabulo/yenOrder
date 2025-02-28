from odoo import fields, models, api
from odoo.exceptions import ValidationError


class TypeStageInherit(models.Model):
    _inherit = 'project.task.type'

    verify_stage = fields.Boolean('Verified stage')

    def write(self, vals):
        res = super(TypeStageInherit, self).write(vals)
        verify_stage_count = self.env['project.task.type'].search_count([('verify_stage','=',True)])
        if verify_stage_count > 1:
            raise ValidationError("Already another Verified stage is selected first "
                                  "deselect that then choose any new one.")
        return res
