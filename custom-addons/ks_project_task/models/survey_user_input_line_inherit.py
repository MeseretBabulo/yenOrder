from odoo import fields, models, api


class SurveyInherit(models.Model):
    _inherit = "survey.user_input.line"

    comment = fields.Char(string="Comment")
    remark = fields.Char(string="Remark")
