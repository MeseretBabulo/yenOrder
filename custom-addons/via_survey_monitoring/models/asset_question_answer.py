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


class SurveyLabel(models.Model):
    _name = 'survey.label'
    _rec_name = 'value'

    monitoring_question_id = fields.Many2one('via.monitoring.question', string='Question', ondelete='cascade')
    monitoring_question_id_2 = fields.Many2one('via.monitoring.question', string='Question 2', ondelete='cascade')
    sequence = fields.Integer('Label Sequence order', default=10)
    value = fields.Char('Suggested value for multiple', translate=True)
    is_correct = fields.Boolean('Is a correct answer')
    answer_score = fields.Float('Score for this choice',
                                help="A positive score indicates a correct choice; a negative or null score indicates a wrong answer")

    allowed_question = fields.One2many('via.monitoring.question', string="Allowed questions", compute="_compute_questions")
    answer_char = fields.Char('Suggested value Char')
    answer_float = fields.Float('Suggested value Float')
    answer_date = fields.Date('Suggested value Date')
    answer_type = fields.Selection(related='monitoring_question_id.question_type', string='Answer Type')
    answer_textbox = fields.Text('Multi line Textbox')


class VIAMonitoringQuestion(models.Model):
    _name = 'via.monitoring.question'
    _rec_name = 'title'

    sequence = fields.Integer('Sequence', default=10)
    is_page = fields.Boolean('Is a page?', default=False)
    # question_survey_id = fields.Many2one('asset.questionnaire', string='Survey')
    monitoring_question_survey_id = fields.Many2one('via.monitoring.template', string='Survey')
    partner_id = fields.Many2one('res.partner', "Company", related="monitoring_question_survey_id.partner_id")
    title = fields.Char('Title', required=True, translate=True)
    question = fields.Char('Question', related="title")
    description = fields.Html('Description', help="Use this field to add additional explanations about your question",
                              translate=True)
    question_type = fields.Selection([
        ('number', 'Numerical Value'),
        ('simple_choice', 'Multiple choice: only one answer'),
        ('textbox', 'Single Line Text Box'),
        ('multi_textbox', 'Multi line Text box'),
        ('date', 'Date'),
        # ('multiple_choice', 'Multiple choice: multiple answers allowed')
        ], string='Question Type')
    validation_length_min = fields.Integer('Minimum Text Length')
    validation_length_max = fields.Integer('Maximum Text Length')
    labels_ids = fields.One2many(
        'survey.label', 'monitoring_question_id', string='Types of answers', copy=True,
        help='Labels used for proposed choices: simple choice, multiple choice and columns of matrix')
    question_id = fields.Many2one('question.answer', 'Question')
    ans_score = fields.Float('Answer Score', default=0.0)
    skipped = fields.Boolean('Skipped')
    neg_marks = fields.Float('Negative score', default=0.25, help='If Any question wrong it will substract score from total')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")


class QuestionsAnswers(models.Model):
    _name = 'questions.answers'
    _rec_name = 'name'

    name = fields.Char('name')
    sequence = fields.Integer('Sequence', default=10)
    question_id = fields.Many2one('via.monitoring.question', string="Question")
    monitoring_question_id = fields.Many2one('via.monitoring', string="Question")
    answer_type = fields.Selection([
        ('number', 'Number'),
        ('simple_choice', 'Multiple choice: only one answer'),
        ('date', 'Date'),
        ('textbox', 'Single line Text box'),
        ('multi_textbox', 'Multi line Text box'),
        # ('multiple_choice', 'Multiple choice: multiple answers allowed')
        ], string='Answer Type')
    skipped = fields.Boolean('Skipped')
    answer_is_correct = fields.Boolean('Correct')
    answer_score = fields.Float('Score')
    value_suggested = fields.Many2one('survey.label', string="Suggested answer")
    answer = fields.Char('Answers')
    ans_score = fields.Float('Answer Score')
    answer_char = fields.Char('Answers Char')
    answer_textbox = fields.Text('Multi line Textbox')
    answer_float = fields.Float('Answer Numerical')
    answer_date = fields.Date('Answer Date')
    answer_sel = fields.Many2one('survey.label', string='Answer Select')
    active = fields.Boolean('Active', default=True)
    partner_id = fields.Many2one('res.partner')
    is_page = fields.Boolean('Is a page?', default=False)
    # name = fields.Char('name', translate=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
