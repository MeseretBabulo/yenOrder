from odoo import fields, models, api
import werkzeug


class SurveyInherit(models.Model):
    _inherit = "survey.survey"

    survey_template = fields.Many2one(string="Survey Template",comodel_name="survey.survey")
    created_from_project = fields.Boolean(string='Created From Project')
    ISP_program_name = fields.Char("ISP Program name")
    mpi_number = fields.Char("MPI#", compute='_compute_mpi_number')
    provider_program = fields.Char("Provider Program")
    individual_name = fields.Char("Individual name")
    ma_number = fields.Char("MA#")
    isp_start_date = fields.Date("ISP start date")
    isp_end_date = fields.Date("ISP End Date")
    project_manager = fields.Many2one('res.users', 'Validation Manager')
    target_completion_date = fields.Date("Target Completion Date")
    evv = fields.Boolean(string='EVV')
    schedule_frequency_comment = fields.Char(string="Schedule and Frequency Comment")
    goal_service = fields.Char(string="Goal/Service")
    criteria_for_completion = fields.Char(string="Criteria for Completion")
    scoring_method = fields.Char(string="Scoring Method")

    def open_survey_url(self):
        survey_id = self
        url = werkzeug.urls.url_join(survey_id.get_base_url(), survey_id.get_start_url()) if survey_id else False
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def open_answers(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Answers',
            'view_mode': 'tree,form',
            'res_model': 'survey.user_input',
            'domain': [('survey_id', '=', self.id), ('test_entry', '=', False)],
            'context': "{'create': False}",

        }

    def action_edit(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit',
            'view_mode': 'form',
            'res_model': 'survey.survey',
            'domain': [('survey_id', '=', self.id)],
            'res_id': self.id,
            'target': 'current',
            'context': "{'create': False}",
        }

    def _compute_mpi_number(self):
        self.mpi_number = self.env.company.ks_mpi

    def get_survey_survey_ids(self):
        survey_question_ids = []
        for survey_question in self.survey_template.question_and_page_ids:
            survey_question_id = survey_question.copy()
            survey_question_id.survey_id = None
            survey_question_ids.append(survey_question_id.id)
        return survey_question_ids

    @api.onchange('survey_template')
    def onchange_survey_template_ks(self):
        for rec in self:
            if rec.survey_template:
                rec.question_and_page_ids = [(6, 0, rec.get_survey_survey_ids())]
                # rec.question_and_page_ids = sur_template.question_and_page_ids
                rec.description = rec.survey_template.description
                rec.description_done = rec.survey_template.description_done
                rec.questions_layout = rec.survey_template.questions_layout
                rec.progression_mode = rec.survey_template.progression_mode
                rec.is_time_limited = rec.survey_template.is_time_limited
                rec.time_limit = rec.survey_template.time_limit
                rec.questions_selection = rec.survey_template.questions_selection
                rec.users_can_go_back = rec.survey_template.users_can_go_back
                rec.access_mode = rec.survey_template.access_mode
                rec.users_login_required = rec.survey_template.users_login_required
                rec.is_attempts_limited = rec.survey_template.is_attempts_limited
                rec.attempts_limit = rec.survey_template.attempts_limit
                rec.scoring_type = rec.survey_template.scoring_type
                rec.scoring_success_min = rec.survey_template.scoring_success_min
                rec.certification = rec.survey_template.certification
                rec.certification_mail_template_id = rec.survey_template.certification_mail_template_id
                rec.certification_report_layout = rec.survey_template.certification_report_layout
                rec.certification_give_badge = rec.survey_template.certification_give_badge
                rec.certification_badge_id = rec.survey_template.certification_badge_id
                rec.certification_badge_id_dummy = rec.survey_template.certification_badge_id_dummy
                rec.session_speed_rating = rec.survey_template.session_speed_rating
                # rec.session_code = rec.survey_template.session_code
                rec.session_link = rec.survey_template.session_link

    @api.model_create_multi
    def create(self, vals):
        temp_survey = super(SurveyInherit, self).create(vals)
        for rec in temp_survey:
            if rec.created_from_project:
                project = self.env['project.project'].browse([self.env.context.get('project_id', False)])
                if project:
                    project.write({'ks_survey': rec.id})
        return temp_survey

    def write(self, vals):
        temp_survey = super(SurveyInherit, self).write(vals)
        if vals.get('survey_template'):
            self.testing()
        return temp_survey

    @api.depends('user_input_ids.state', 'user_input_ids.test_entry', 'user_input_ids.scoring_percentage',
                 'user_input_ids.scoring_success')
    def _compute_survey_statistic(self):
        default_vals = {
            'answer_count': 0, 'answer_done_count': 0, 'success_count': 0,
            'answer_score_avg': 0.0, 'success_ratio': 0.0
        }
        stat = dict((cid, dict(default_vals, answer_score_avg_total=0.0)) for cid in self.ids)
        user_input = self.env['survey.user_input']
        base_domain = ['&', ('survey_id', 'in', self.ids), ('test_entry', '!=', True)]

        read_group_res = user_input.read_group(base_domain, ['survey_id', 'state'],
                                               ['survey_id', 'state', 'scoring_percentage', 'scoring_success'],
                                               lazy=False)
        for item in read_group_res:
            stat[item['survey_id'][0]]['answer_count'] += item['__count']
            stat[item['survey_id'][0]]['answer_score_avg_total'] += item['scoring_percentage']
            if item['state']:
                stat[item['survey_id'][0]]['answer_done_count'] += item['__count']
            if item['scoring_success']:
                stat[item['survey_id'][0]]['success_count'] += item['__count']

        for survey_stats in stat.values():
            avg_total = survey_stats.pop('answer_score_avg_total')
            survey_stats['answer_score_avg'] = avg_total / (survey_stats['answer_done_count'] or 1)
            survey_stats['success_ratio'] = (survey_stats['success_count'] / (
                        survey_stats['answer_done_count'] or 1.0)) * 100

        for survey in self:
            survey.update(stat.get(survey._origin.id, default_vals))
