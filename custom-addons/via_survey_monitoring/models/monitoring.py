# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


import logging
import re
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ViaMonitoring(models.Model):
    _name = 'via.monitoring'
    _description = "VIA Monitoring"

    name = fields.Char('Name')
    is_broken = fields.Boolean('Is Broken', default=False)
    partner_id = fields.Many2one('res.partner', 'Person supported')
    template_id = fields.Many2one('via.monitoring.template', )
    monitoring_question_ids = fields.One2many('via.monitoring.question', 'question_id',
                                              string='Asset Question')
    # asset_question_ids = fields.One2many('via.monitoring.question', 'question_id', string='Asset Question')
    # asset_question_answer_ids = fields.One2many('questions.answers', 'monitoring_question_id', string='Question Answers')
    question_answer_ids = fields.One2many('questions.answers', 'monitoring_question_id',
                                          string='Question Answers')
    ans_total = fields.Float('Total',
                             compute='_compute_ans_total',
                             store=True,
                             readonly=1)
    ques_score = fields.Float('Question Total',
                              compute='_compute_ques_total',
                              store=True,
                              readonly=1)

    @api.onchange('template_id')
    def _onchange_template(self):
        self.question_answer_ids = [(5, 0, 0)]
        questions = []
        vals = {}
        list_of_words = ['DDD ID', 'DDD ID#', 'DDD ID #', 'ddd id#', 'ddd ID#', 'ddd id', 'ddd id #']
        words_re = re.compile("|".join(list_of_words))
        for rec in self.template_id.question_and_page_ids:
            if rec.is_page:
                vals = {'is_page': rec.is_page,
                        'name': rec.title,
                        'display_type': rec.display_type if rec.display_type else 'line_section',
                        'sequence': rec.sequence}
            else:
                vals = {
                    'question_id': rec.id,
                    'name': rec.title,
                    'answer_type': rec.question_type,
                    'skipped': rec.skipped,
                    'answer_char': self.partner_id.mci_number if words_re.search(rec.title) and rec.question_type == 'textbox' else '',
                    'sequence': rec.sequence
                }
            questions.append((0, 0, vals))
        self.question_answer_ids = questions
