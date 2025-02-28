# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    via_project_service_note_count = fields.Integer(compute='_compute_project_service_note_count', string='# Service Notes')
    team_id = fields.Many2one(
        'crm.team', 'Sales Team',
        ondelete="set null", tracking=True,
        change_default=True, check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    def _compute_project_service_note_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        for project in self:
            task_data = self.env['via.service.note'].search_count([('project_id', '=', project.id),
                                                                   ('company_id', '=', self.env.company.id)])
            project.via_project_service_note_count = task_data


class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_color = fields.Integer(related='stage_id.task_color',
                            string="Color")
    team_id = fields.Many2one(
        'crm.team', 'Sales Team', related="project_id.team_id")


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    task_color = fields.Integer(string="Color")