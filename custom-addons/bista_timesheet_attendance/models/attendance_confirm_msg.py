from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AttendanceConfirmMessage(models.Model):
    _name = "attendance.confirm.message"

    name = fields.Char("Name", required=True)
    confirm_message = fields.Html(string='Message')
    active = fields.Boolean("Active", copy=False, default=True)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    @api.constrains('active')
    def check_id_number(self):
        active_record_counts = self.search_count([('active', '=', True),
                                                 ('company_id', '=', self.env.company.id),
                                                 ('id', '!=', self.id)])
        if active_record_counts > 0:
            raise ValidationError(_("At a Time One Terms & conditions Activated"))
