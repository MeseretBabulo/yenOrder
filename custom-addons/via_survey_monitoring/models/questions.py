# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import models, fields, api, _, exceptions

import logging
_logger = logging.getLogger(__name__)


class VIAMonitoringTemplate(models.Model):
    _name = 'via.monitoring.template'
    _description = "Monitoring Template"
    _rec_name = 'name'

    name = fields.Char("Template Name")
    partner_id = fields.Many2one('res.partner', string='Person Supported')
    question_and_page_ids = fields.One2many('via.monitoring.question', 'monitoring_question_survey_id',
                                            string='Sections and Questions', copy=True)
    scoring_type = fields.Selection([
        ('no_scoring', 'No scoring'),
        ('scoring_with_answers', 'Scoring with answers at the end'),
        ('scoring_without_answers', 'Scoring without answers at the end')],
        string="Scoring", required=True, default='no_scoring')
    questions_selection = fields.Selection([
        ('all', 'All questions'),
        ('random', 'Randomized per section')],
        string="Selection", required=True, default='all',
        help="If randomized is selected, add the number of random questions next to the section.")
    description = fields.Html("Description", translate=True,
                              help="The description will be displayed on the home page of the asset survey. You can use this to give the purpose and guidelines to your candidates before they start it.")

