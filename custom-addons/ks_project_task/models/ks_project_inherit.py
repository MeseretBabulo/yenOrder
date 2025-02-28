from odoo import fields, models, api


class ProjectInherit(models.Model):
    _inherit = "project.project"

    ks_survey = fields.Many2one('survey.survey', 'Survey')
    ks_survey_read_only = fields.Boolean('Make Survey ReadOnly', default=False)
    medical_appointment_checker = fields.Boolean('Medical Appointment', default=False)
    ks_answer_done_count = fields.Integer("Attempts", compute="_compute_survey_statistic")

    def _compute_survey_statistic(self):
        if self.ks_survey:
            self.ks_answer_done_count = self.env['survey.survey'].search([('id', '=', self.ks_survey.id)]).answer_done_count
        else:
            self.ks_answer_done_count = 0

    @api.onchange('team_id')
    def team_id_change(self):
        if self.partner_id and self.partner_id.sales_team_ids:
            self.partner_id.sales_team_ids = [(4, self.team_id.id)]

    def action_survey_user_input_completed(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'project_form',
            'view_mode': 'tree,form',
            'res_model': 'survey.user_input',
            'domain': [('survey_id', '=', self.ks_survey.id), ('state', '=', 'done'), ('test_entry', '=', False)],
            'context': "{'create': False}"
        }

    def _open_wizard_from_here(self):
        survey = self.env['link.project.survey'].search([('program_type', '=', self.program_type)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Survey',
            'view_mode': 'form',
            'res_model': 'survey.survey',
            'target': 'new',
            'context': {
                'default_created_from_project': True,
                'project_id': self.id,
                'default_survey_template': survey.survey_template.id,
                'default_title': self.name + " (" + self.partner_id.name + ")" if self.partner_id else self.name,
                'default_individual_name': self.partner_id.name,
                'default_ISP_program_name': self.name,
                'default_ma_number': self.partner_id.ma_number,
                'default_provider_program': self.partner_id.payer_program,
                'default_isp_start_date': self.partner_id.plan_start_date,
                'default_isp_end_date': self.partner_id.plan_end_date,
                'default_project_manager': self.user_id.id,
            }
        }


