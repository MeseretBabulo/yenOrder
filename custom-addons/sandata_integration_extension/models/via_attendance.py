# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class ViaAttendanceLine(models.Model):
    _inherit = "via.attendance.line"

    so_line = fields.Many2one('sale.order.line',string="Sale order Item")
    child_line_location = fields.Many2one('res.partner', string="Location")
