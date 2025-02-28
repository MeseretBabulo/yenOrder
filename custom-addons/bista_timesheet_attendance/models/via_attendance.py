from odoo import api, fields, models, _


class ViaAttendanceLine(models.Model):
    _name = "via.attendance.line"
    _rec_name = 'check_in_time'

    def _default_employee(self):
        company = self.env.company
        return self.env["hr.employee"].search(
            [("user_id", "=", self.env.uid), ("company_id", "in", [company.id, False])],
            limit=1,
            order="company_id ASC",
        )

    date = fields.Date(string="Date")
    task_id = fields.Many2one('project.task', string="Task")
    active = fields.Boolean(related="task_id.active", store=True)
    company_id = fields.Many2one('res.company',
                    default=lambda self: self.env.company)
    check_in_time = fields.Datetime(string="Check-In Time")
    check_in_latitude = fields.Float(
        "Check-in Latitude", digits="Location", readonly=True
    )
    check_in_longitude = fields.Float(
        "Check-in Longitude", digits="Location", readonly=True
    )
    check_out_time = fields.Datetime(string="Check-Out Time")
    check_out_latitude = fields.Float(
        "Check-out Latitude", digits="Location", readonly=True
    )
    check_out_longitude = fields.Float(
        "Check-out Longitude", digits="Location", readonly=True
    )

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        default=lambda self: self._default_employee()
    )
    description = fields.Char(string="Description")
    delay_time_differance = fields.Float(string="Delay Time Difference")
    temperature = fields.Char(string="Temperature")
    delay_reason = fields.Char(string="Delay Reason")
