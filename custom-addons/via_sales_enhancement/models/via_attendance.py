# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ViaAttendanceLine(models.Model):
    _inherit = 'via.attendance.line'

    note = fields.Char("Notes")
    via_error_code_ids = fields.Many2many("via.error.code", "timesheet_error_code_rel", "timesheet_id", "error_code_id",
                                          string="Error Code")
