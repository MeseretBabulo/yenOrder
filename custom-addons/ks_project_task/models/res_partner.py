# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    project_count = fields.Integer(compute="_compute_projects_count")
    ks_answer_count = fields.Integer("Attempts", compute="_compute_answer_count")
    sales_team_ids = fields.Many2many('crm.team', string="Sales Teams")
    survey_id = fields.Many2one('survey.survey', string="Survey")
    survey_ids = fields.Many2many('survey.survey', string="Surveys")
    linked_medical_project_id = fields.Many2one('project.project', string="Linked Medical Project", compute="_compute_linked_medical_project")
    medical_appointments_tasks_count = fields.Integer(string="linked tasks")

    def _compute_survey_ids(self):
        if self.survey_id:
            self.survey_ids = [(4, self.survey_id.id)]
        else:
            self.survey_ids = None

    def _compute_answer_count(self):
        self.ks_answer_count = self.env['survey.user_input'].search_count([('name_of_person_supported', '=', self.id)])

    def survey_user_answers(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Survey Answers',
            'view_mode': 'tree,form',
            'res_model': 'survey.user_input',
            'domain': [('name_of_person_supported', '=', self.id)],
            'context': "{'create': False}"
        }
    
    def _compute_projects_count(self):
        for partner in self:
            partner.project_count = self.env['project.project'].search_count([('partner_id', '=', partner.id)])

    def action_open_projects_view(self):
        return {
            'type': 'ir.actions.act_window',
            'domain': [('partner_id', '=', self.id)],
            'view_mode': 'kanban',
            'view_id': self.env.ref('project.view_project_kanban').id,
            'res_id': self.id,
            'name': _('Projects'),
            'res_model': 'project.project',
        }

    def action_archive(self):
        for partner in self:
            if partner.active:
                return {
                    'name': _('Archive Partner'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'res.partner.archive.wizard',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'view_id': self.env.ref('ks_project_task.view_res_partner_archive_wizard_form').id,
                    'context': {'default_partner_id': partner.id},
                }

    def action_unarchive(self):
        self.active = True

    def _compute_linked_medical_project(self):
        linked_project_id = self.env['project.project'].search([('partner_id.id', '=', self.id), (
            'medical_appointment_checker', '=', True)], limit=1)
        if linked_project_id:
            self.linked_medical_project_id = linked_project_id.id
            self.medical_appointments_tasks_count = len(linked_project_id.task_ids.ids)
        else:
            self.linked_medical_project_id = None
            self.medical_appointments_tasks_count = 0

    def create_medical_appointment(self):
        # linked_project_id = self.env['project.project'].search([('partner_id.id', '=', self.id), (
        #     'medical_appointment_checker', '=', True)], limit=1).id
        return {
            'name': _('Create Medical Appointment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'create.project.task.wizard',
            'context': {
                'default_project_id': self.linked_medical_project_id.id
            }
        }

    def medical_appointments_tasks(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Medical Tasks',
            'view_mode': 'kanban,tree,form',
            'res_model': 'project.task',
            'domain': [('project_id', '=', self.linked_medical_project_id.id)]
            # 'context': "{'create': False}"
        }
