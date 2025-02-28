# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

import pytz
from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.http import request


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def _program_type_selection(self):
        company_id = False
        if request and request.httprequest.cookies.get('cids'):
            cid = request.httprequest.cookies.get('cids').split(',')
            company_id = self.env['res.company'].browse(int(cid[0]))
        else:
            company_id = self.env.user.company_id if self.env.user and self.env.user.company_id else False
        if company_id.via_company_type == 'pa':
            return [('support_brokering', 'Supports Brokering'),
                                    ('htts', 'Housing Transistion & Tenancy Sustaining Service'),
                                    ('ihcs', 'In-Home & Community Supports'),
                                    # ('ihcs_e', 'In-Home & Community Supports Enhanced'),
                                    ('ihcs_2_1', 'In-Home & Community Supports 2x1 (Two staff to One presenter)'),
                                    ('ihcs_e', 'In-Home & Community Supports Enhanced'),
                                    ('companion', 'Companion'),
                                    ('cps', 'Community Participation Support'),
                                    ('cpse', 'Community Participation Support Enhanced'),
                                    ('ci', 'Community Integration'),
                                    ('residential', 'Residential')]
        elif company_id.via_company_type == 'nj':
            return [('sp', 'SP (Support program)'),
                    ('ccp', 'CCP (Community Care Waiver)')]
        else:
            return [('', '')]

    program_type = fields.Selection(_program_type_selection,
                                    string="Program Type")


class ProjectTask(models.Model):
    _inherit = "project.task"

    is_pa_company = fields.Boolean("Is PA Company",
        default=False, copy=False,
        compute="_compute_pa_company")
    physician_ids = fields.Many2many('res.partner',
        'project_partner_physician_rel',"project_partner_id",
        "project_physician_id", compute='_compute_physician_ids',
        string="Physicians")
    physician_id = fields.Many2one('res.partner',
        string="Physician", domain="[('id', 'in', physician_ids)]")
    partner_id = fields.Many2one('res.partner',
                                 string='Person Supported',
                                 compute='_compute_partner_id', recursive=True, store=True, readonly=False,
                                 tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    program_type = fields.Selection(related='project_id.program_type',
                                    string="Program Type")
    is_sn_editable = fields.Boolean(compute='_compute_sn_editable',
                    string="SN Editable?")

    @api.depends('program_type')
    def _compute_sn_editable(self):
        for task in self:
            if task.program_type and\
            task.program_type.startswith("ihcs") and\
            self.env.user.has_group('via_sales_enhancement.group_service_note_user') and\
            not self.env.user.has_group('via_sales_enhancement.group_service_note_admin'):
                task.is_sn_editable = False
            elif self.env.user.has_group('via_sales_enhancement.group_service_note_admin'):
                task.is_sn_editable = True
            else:
                task.is_sn_editable = True
 

    @api.depends('partner_id')
    def _compute_physician_ids(self):
        for task in self:
            if task.partner_id:
                task.physician_ids = task.partner_id.physician_ids
            else:
                task.physician_ids = []

    @api.depends("company_id")
    def _compute_pa_company(self):
        self.is_pa_company = False
        if request.httprequest.cookies.get('cids'):
            cid = request.httprequest.cookies.get('cids').split(',')
            company_id = self.env['res.company'].browse(int(cid[0]))
        else:
            company_id = self.env.user.company_id if self.env.user and self.env.user.company_id else False
        if company_id.via_company_type == 'pa':
            self.is_pa_company = True

    def _populate_missing_personal_stages(self):
        # Assign the default personal stage for those that are missing
        personal_stages_without_stage = self.env['project.task.stage.personal'].sudo().search([('task_id', 'in', self.ids), ('stage_id', '=', False)])
        if self.project_id:
            if personal_stages_without_stage and not self.company_id.remove_project_stage_type:
                user_ids = personal_stages_without_stage.user_id
                personal_stage_by_user = defaultdict(lambda: self.env['project.task.stage.personal'])
                for personal_stage in personal_stages_without_stage:
                    personal_stage_by_user[personal_stage.user_id] |= personal_stage
                for user_id in user_ids:
                    stage = self.env['project.task.type'].sudo().search([('user_id', '=', user_id.id)], limit=1)
                    # In the case no stages have been found, we create the default stages for the user
                    if not stage:
                        stages = self.env['project.task.type'].sudo().with_context(lang=user_id.partner_id.lang, default_project_id=False).create(
                            self.with_context(lang=user_id.partner_id.lang)._get_default_personal_stage_create_vals(user_id.id)
                        )
                        stage = stages[0]
                    personal_stage_by_user[user_id].sudo().write({'stage_id': stage.id})
        else:
            self.stage_id = False

    def name_get(self):
        result = []
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        for task in self:
            start_date_utc = ''
            end_date_utc = ''
            if task.planned_date_begin:
                start_date_utc = datetime.strftime(
                    pytz.utc.localize(datetime.strptime(task.planned_date_begin.strftime("%Y-%m-%d %H:%M:%S"),
                                                        DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),
                    "%H:%M")
            if task.planned_date_end:
                end_date_utc = datetime.strftime(
                    pytz.utc.localize(datetime.strptime(task.planned_date_end.strftime("%Y-%m-%d %H:%M:%S"),
                                                        DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),
                    "%H:%M")
            name = str(start_date_utc and str(start_date_utc) or '') +  \
                   str(end_date_utc and ' - ' + str(end_date_utc) or '') + \
                   ' ( ' + str(task.name and str(task.name)) + ' )'
            result.append((task.id, name))
        return result