# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.http import request


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

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

    is_service_note = fields.Boolean(string="Is Service Note")
    is_manual = fields.Boolean('Is Manual')
    via_company_type = fields.Selection(related="company_id.via_company_type", store=True, string="Company Type")
    program_type = fields.Selection(_program_type_selection,
                                    string="Program Type")

    def open_service_note(self):
        form_view_id = self.env.ref('sandata_integration.via_service_note_wizard_form_view').id
        for record in self:
            if record.task_id.sale_line_id and record.task_id.sale_line_id.order_id.partner_id and \
                    record.task_id.sale_line_id.order_id.partner_id.isp_ids:

                isp_ids = record.task_id.sale_line_id.order_id.partner_id.isp_ids.filtered(
                    lambda isp: isp.product_id.id == record.task_id.sale_line_id.product_id.id).sorted(key=lambda r: r.id)
                if isp_ids:
                    list_data = []
                    if isp_ids[-1].outcome_phrase:
                        list_data.append(
                            (0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
                                    'isp_id': isp_ids[-1].id
                                    }))
                    # if isp_ids[-1].reason_for_outcome:
                    #     list_data.append((0, 0, {
                    #         'outcome_phrase': isp_ids[-1].reason_for_outcome,
                    #         'isp_id': isp_ids[-1].id
                    #     }))
                    # if isp_ids[-1].outcome_statement:
                    #     list_data.append(
                    #         (0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
                    #                 'isp_id': isp_ids[-1].id
                    #                 }))
                    # if isp_ids[-1].actions_taken:
                    #     list_data.append(
                    #         (0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
                    #                 'isp_id': isp_ids[-1].id
                    #                 }))
                    # if isp_ids[-1].progress_status:
                    #     list_data.append(
                    #         (0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
                    #                 'isp_id': isp_ids[-1].id
                    #                 }))
                    return {
                        'name': _('Service Notes'),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'via.service.note.wizard',
                        'view_id': form_view_id,
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': {'tasks': self.env.context.get('params') and self.env.context.get('params').get('id'),
                                    'manual_timesheet_note': True,
                                    'default_account_analytic_line_id': record.id,
                                    'employee_id': record.employee_id.id,
                                    'default_service_note_survey_ids': list_data}
                    }
                else:
                    return {
                        'name': _('Service Notes'),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'via.service.note.wizard',
                        'view_id': form_view_id,
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': {
                            'tasks': self.env.context.get('params') and self.env.context.get('params').get('id'),
                            'manual_timesheet_note': True,
                            'employee_id': record.employee_id.id,
                            'default_account_analytic_line_id': record.id}
                    }
            else:
                return {
                    'name': _('Service Notes'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'via.service.note.wizard',
                    'view_id': form_view_id,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'tasks': self.env.context.get('params') and self.env.context.get('params').get('id'),
                                'manual_timesheet_note': True,
                                'employee_id': record.employee_id.id,
                                'default_account_analytic_line_id': record.id}
                }

    def open_service_note_entry(self):
        tree_view_id = self.env.ref('sandata_integration.via_service_note_tree_wizard_view').id
        return {
            'name': _('Service Notes'),
            'view_mode': 'tree',
            'res_model': 'via.service.note',
            'view_id': int(tree_view_id),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': [('account_analytic_line_id', '=', self.id)]
        }