from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    def _default_employee(self):
        company = self.env.company
        return self.env["hr.employee"].search(
            [("user_id", "=", self.env.uid), ("company_id", "in", [company.id, False])],
            limit=1,
            order="company_id ASC",
        )

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        default=lambda self: self._default_employee()
    )
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
    attendance_state = fields.Selection([
                            ('checked_in', 'Checked In'),
                            ('checked_out', 'Checked Out')],
                            string="Attendance State")
    attendance_line_ids = fields.One2many('via.attendance.line', 'task_id',
                            string="Attendances")
    # planned_time = fields.Float(string="Planned Time")
    # time_am_pm = fields.Selection([
    #                             ('am', 'AM'),
    #                             ('pm', 'PM')],
    #                             string="AM/PM")

    def timesheet_sign_in(self, kwargs=None):
        """
        :param kwargs: {'lat': FLOAT, 'lng': FLOAT, 'mode': 'readonly | edit'}
        """
        via_atten_line_obj = self.env['via.attendance.line']
        user = self.env.user
        company = self.env.company
        employee_id = self.env['hr.employee'].search([
                                        ('user_id', '=', user.id),
                                        ('company_id', '=', company.id)],
                                        limit=1)

        for record in self:
            via_line_ids = via_atten_line_obj.search([
                                    ('employee_id', '=', employee_id.id),
                                    ('check_out_time', '=', False),
                                    ('company_id', '=', company.id)], limit=1)
            if via_line_ids:
                raise ValidationError(_("""At a time you can Check-in in the one task only. Please checkout from %s.""", via_line_ids.task_id.name))
            via_atten_line_obj.create({
                                        'date': fields.Date.today(),
                                        'task_id': record.id,
                                        'check_in_time': fields.Datetime.now(),
                                        'check_in_latitude': kwargs.get('lat'),
                                        'check_in_longitude': kwargs.get('lng'),
                                        })
        return True

    def timesheet_sign_out(self, kwargs=None):
        """
        :param kwargs: {'lat': FLOAT, 'lng': FLOAT, 'mode': 'readonly | edit'}
        """
        via_atten_line_obj = self.env['via.attendance.line']
        analytic_line_obj = self.env['account.analytic.line']
        user = self.env.user
        company = self.env.company
        employee_id = self.env['hr.employee'].search([
                                        ('user_id', '=', user.id),
                                        ('company_id', '=', company.id)], limit=1)
        worked_hours = 0.0
        for record in self:
            via_line_ids = via_atten_line_obj.search([
                                    ('employee_id', '=', employee_id.id),
                                    ('check_out_time', '=', False),
                                    ('task_id', '!=', record.id),
                                    ('company_id', '=', company.id)], limit=1)
            if via_line_ids:
                raise ValidationError(_("""Please Check-out from %s task first.""", via_line_ids.task_id.name))
            sign_in_line = via_atten_line_obj.search([
                                    ('employee_id', '=', employee_id.id),
                                    ('company_id', '=', company.id),
                                    ('task_id', '=', record.id),
                                    ('check_out_time', '=', False)],
                                    limit=1, order='id desc')
            if sign_in_line:
                sign_in_line.write({
                                    'check_out_time': fields.Datetime.now(),
                                    'check_out_latitude': kwargs.get('lat'),
                                    'check_out_longitude': kwargs.get('lng'),
                                    })
                duration = (sign_in_line.check_out_time - sign_in_line.check_in_time).total_seconds() / 3600
                hours_spent = round(duration, 2)
                analytic_line_obj.create({
                                        'date': sign_in_line.date,
                                        'employee_id': employee_id.id,
                                        'name': sign_in_line.description or '',
                                        'check_in_time': sign_in_line.check_in_time,
                                        'check_out_time': sign_in_line.check_out_time,
                                        'latitude_in': sign_in_line.check_in_latitude,
                                        'longitude_in': sign_in_line.check_in_longitude,
                                        'latitude_out': sign_in_line.check_out_latitude,
                                        'longitude_out': sign_in_line.check_out_longitude,
                                        'task_id': sign_in_line.task_id.id,
                                        'unit_amount': hours_spent
                                        })
            else:
                raise ValidationError(_("""Please Check-in first."""))
        return True
