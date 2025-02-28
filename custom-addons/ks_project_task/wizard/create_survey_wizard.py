from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CreateSurveyWizard(models.TransientModel):
    _name = 'create.survey.wizard'

    name = fields.Many2one("survey.survey","Survey")