from odoo import fields, models, api


class LinkProjectSurvey(models.Model):
    _name = "link.project.survey"
    _rec_name = "program_type"

    program_type = fields.Selection([('support_brokering', 'Supports Brokering'),
                                     ('htts', 'Housing Transistion & Tenancy Sustaining Service'),
                                     ('ihcs', 'In-Home & Community Supports'),
                                    #  ('ihcs_e', 'In-Home & Community Supports Enhanced'),
                                     ('ihcs_2_1', 'In-Home & Community Supports 2x1 (Two staff to One presenter)'),
                                     ('ihcs_e', 'In-Home & Community Supports Enhanced'),
                                     ('companion', 'Companion'),
                                     ('cps', 'Community Participation Support'),
                                     ('cpse', 'Community Participation Support Enhanced'),
                                     ('ci', 'Community Integration'),
                                     ('residential', 'Residential')],
                                    string="Program Type")

    survey_template = fields.Many2one("survey.survey", "Survey Template")

    _sql_constraints = [
        ('unique_name', 'unique (program_type)', 'records with duplicate program type is not allowed'),
    ]
