# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, _


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    via_service_note_count = fields.Integer(compute='_compute_employee_service_note_count', string='# Service Notes')

    def _compute_employee_service_note_count(self):
        for user in self:
            task_data = self.env['via.service.note'].search_count([('employee_id', '=', user.id),
                                                                   ('company_id', '=', self.env.company.id)])
            user.via_service_note_count = task_data


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    emp_certificate = fields.Binary('Certificate', groups="hr.group_hr_user")
    emp_certificate_name = fields.Char('Certificate Name', groups="hr.group_hr_user")