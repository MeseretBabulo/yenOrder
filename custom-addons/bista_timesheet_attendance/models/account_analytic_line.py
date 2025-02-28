from odoo import api, fields, models, _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    attendance_id = fields.Many2one('hr.attendance', string="Attendance#")

    check_in_time = fields.Datetime(string="Check-In Time")
    check_out_time = fields.Datetime(string="Check-Out Time")
    latitude_in = fields.Float(
        "Check-in Latitude", digits="Location", readonly=True
    )
    longitude_in = fields.Float(
        "Check-in Longitude", digits="Location", readonly=True
    )
    latitude_out = fields.Float(
        "Check-out Latitude", digits="Location", readonly=True
    )
    longitude_out = fields.Float(
        "Check-out Longitude", digits="Location", readonly=True
    )