# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _


class ViaAttendanceLine(models.Model):
    _inherit = "via.attendance.line"

    is_manual = fields.Boolean(string="Is Manual?",
                                copy=False)
    is_checkout_done = fields.Boolean(string="Is Check-out Done?",
                                copy=False)
    via_company_type = fields.Selection(related="company_id.via_company_type", store=True, string="Company Type")

    def open_check_out_attendance_wizard(self):
        form_view_id = self.env.ref('sandata_integration.wizard_create_attendance_form_view').id
        if form_view_id:
            return {
                    'name': _('Create Attendance Wizard'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'views': [
                            (form_view_id, 'form')],
                    'view_id': form_view_id,
                    'res_model': 'wizard.create.attendance',
                    'context': {'default_partner_id': self.task_id and\
                                self.task_id.partner_id and\
                                self.task_id.partner_id.id,
                                'from_checkout': True, 'tasks': self.task_id.id}
                    }

    def open_service_note_wizard(self):
        tree_view_id = self.env.ref('sandata_integration.via_service_note_tree_wizard_view').id
        return {
            'name': _('Service Notes'),
            'view_mode': 'tree',
            'res_model': 'via.service.note',
            'view_id': int(tree_view_id),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': [('via_attendance_line_id', '=', self.id)]
        }


class ViaServiceNote(models.Model):
    _inherit = "via.service.note"

    def open_attendance_line(self):
        tree_view_id = self.env.ref('sandata_integration.via_account_analytic_line_tree_wizard_view').id
        return {
            'name': _('Attendance'),
            'view_mode': 'tree',
            'res_model': 'account.analytic.line',
            'view_id': int(tree_view_id),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': [('id', '=', self.account_analytic_line_id.id)]
        }
