from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountAnalyticLineInherit(models.Model):
    _inherit = 'account.analytic.line'

    check_in_time = fields.Datetime('Check in')
    check_out_time = fields.Datetime('Check out')
    actual_hrs = fields.Float('Actual Hrs')
    paid_hrs = fields.Float('Paid Hrs')
    billed_hrs = fields.Float('Billed Hrs')
    visit_id = fields.Many2one("via.attendance.line", "Visit id")
    visit_character_id = fields.Char("Visitor id", compute='_compute_visit_id')
    child_line_location = fields.Many2one('res.partner', string="Location")
    comment = fields.Text(string="Comment")

    def _compute_visit_id(self):
        for rec in self:
            if rec.visit_id:
                rec.check_in_time = rec.visit_id.check_in_time
                rec.check_out_time = rec.visit_id.check_out_time
                rec.visit_character_id = str(rec.visit_id.id)
            else:
                attendance_line = self.env['via.attendance.line'].search([('check_in_time', '=', rec.check_in_time)],
                                                                         limit=1)
                if attendance_line:
                    rec.visit_character_id = attendance_line.visit_id  # Already String value in visit_id
                    rec.visit_id = int(rec.visit_character_id)
                    rec.check_in_time = rec.visit_id.check_in_time
                    rec.check_out_time = rec.visit_id.check_out_time
                else:
                    rec.visit_character_id = "None"
                    rec.visit_id = None

    @api.onchange('check_in_time', 'check_out_time')
    def write_time(self):
        if self.check_in_time and self.check_out_time:
            if self.check_in_time > self.check_out_time:
                raise UserError("Check out Time can't be lower than check in time.")
            time_consume = self.check_out_time - self.check_in_time
            if time_consume.days:
                raise UserError(
                    "Check in and Check out time difference is more than 24 Hrs please select correct time.")
            # if min is below 9 corner case fix
            actual_hrs_bool = False
            hrs, min_chk, _ = str(time_consume).split(':')
            if int(min_chk) <= 9:
                actual_hrs_bool = True
                time_consume = str(hrs) + ":11:" + str(_)
            time_consume_new = self.convert_time_to_float(str(time_consume))
            hrs_min = self.convert_time_to_float_round_off(str(time_consume))
            paid_hrs = self.round_off(hrs_min)
            self.paid_hrs = self.convert_time_to_float_round_off_new(paid_hrs)
            unit_amount = self.round_off_lower(hrs_min)
            self.unit_amount = self.convert_time_to_float_round_off_new(unit_amount)
            if actual_hrs_bool:
                time_diff = self.convert_time_to_float(str(self.check_out_time - self.check_in_time))
                self.actual_hrs = time_diff
            else:
                self.actual_hrs = time_consume_new

    def round_off(self, time_cons):
        hours_str, minutes_str = str(time_cons).split('.')
        int_hours = int(hours_str)
        min = int(minutes_str)
        if min <= 9:
            min *= 10
        if min % 15 == 0:
            return time_cons
        time_consume = 0
        i = 1
        while min > time_consume:
            time_consume = 15 * i
            i += 1
        if time_consume == 60:
            int_hours += 1
            time_consume = 0
        return int_hours + (time_consume) / 100

    def round_off_lower(self, time_cons):
        hours_str, minutes_str = str(time_cons).split('.')
        min = int(minutes_str)
        if min <= 9:
            min *= 10
        if min % 15 == 0:
            return time_cons
        time_consume = 0
        i = 1
        while min > time_consume:
            time_consume = 15 * i
            i += 1
        return int(hours_str) + (time_consume - 15) / 100

    def convert_time_to_float_round_off_new(self, time_consume):
        time_consume = str(time_consume)
        hours, minutes = time_consume.split('.')
        min = int(minutes) / 60
        if min <= 0.09:
            min *= 10
        total_hours = int(hours) + min
        return float(total_hours)

    def convert_time_to_float(self, time_consume):
        # Check if time_consume contains days
        hours, minutes, _ = time_consume.split(':')
        total_hours = int(hours) + (int(minutes) / 60)

        return float(total_hours)

    def convert_time_to_float_round_off(self, time_consume):
        # Check if time_consume contains days
        hours, minutes, _ = time_consume.split(':')
        total_hours = int(hours) + int(minutes) / 100
        return float(total_hours)

    def create(self, vals):
        """
        Call the onChange method manually when creating a record,
        as it will not be triggered automatically.
        """
        result = super().create(vals)
        for rec in result:
            rec.write_time()
        return result
