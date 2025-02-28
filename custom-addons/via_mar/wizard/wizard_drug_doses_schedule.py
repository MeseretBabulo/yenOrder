# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import psycopg2
from datetime import datetime, timedelta, time
import csv
import calendar
# from odoo.addons.resource.models.resource import float_to_time
from pytz import timezone, UTC
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from dateutil.rrule import rrule, rruleset, DAILY, WEEKLY, MONTHLY, YEARLY, MO, TU, WE, TH, FR, SA, SU
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


MONTHS = {
    'january': 31,
    'february': 28,
    'march': 31,
    'april': 30,
    'may': 31,
    'june': 30,
    'july': 31,
    'august': 31,
    'september': 30,
    'october': 31,
    'november': 30,
    'december': 31,
}

DAYS = {
    'mon': MO,
    'tue': TU,
    'wed': WE,
    'thu': TH,
    'fri': FR,
    'sat': SA,
    'sun': SU,
}

WEEKS = {
    'first': 1,
    'second': 2,
    'third': 3,
    'last': 4,
}


class ScheduleDrugDoses(models.Model):
    _name = 'schedule.drug.doses'
    _description = 'Schedule Drug Doses'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date", tracking=True)
    med_presc_id = fields.Many2one('medical.prescription.line',
                                    string="Prescription Line#")
    # dose = fields.Float(related="med_presc_id.dose",
    #                                 string="Give Amount/Quantity")
    # dose_unit_id = fields.Many2one('uom.uom', related="med_presc_id.dose_unit_id",
    #                                string="UOM")
    dose_schedule_ids = fields.One2many('drug.doses.timing.lines',
                                    'drug_schedule_id',
                                    string="Dose Timing")
    admin_frequency_id = fields.Many2one(related="med_presc_id.admin_frequency_id",
                                    string="Frequency")
    instructions = fields.Text(string="Instructions", related="med_presc_id.dose_instructions")
    team_id = fields.Many2one('crm.team',
                                    string="Team")
    strength = fields.Char(related="med_presc_id.strength",
                                    string="Strength")
    #Recurrence Fields#

    repeat_show_dow = fields.Boolean(compute='_compute_repeat_visibility')
    repeat_show_day = fields.Boolean(compute='_compute_repeat_visibility')
    repeat_show_week = fields.Boolean(compute='_compute_repeat_visibility')
    repeat_show_month = fields.Boolean(compute='_compute_repeat_visibility')

    is_recurrence = fields.Boolean(string="Recurrence")
    repeat_interval = fields.Integer(string='Repeat Every', default=1)
    repeat_unit = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months'),
    ], default='day')
    repeat_type = fields.Selection([
        ('until', 'End Date'),
    ], default="until", string="Until")
    repeat_until = fields.Date(string="End Date")
    repeat_number = fields.Integer(string="Repetitions")

    repeat_on_month = fields.Selection([
        ('date', 'Date of the Month'),
        ('day', 'Day of the Month'),
    ])

    repeat_on_year = fields.Selection([
        ('date', 'Date of the Year'),
        ('day', 'Day of the Year'),
    ])

    mon = fields.Boolean(string="Mon")
    tue = fields.Boolean(string="Tue")
    wed = fields.Boolean(string="Wed")
    thu = fields.Boolean(string="Thu")
    fri = fields.Boolean(string="Fri")
    sat = fields.Boolean(string="Sat")
    sun = fields.Boolean(string="Sun")

    repeat_day = fields.Selection([
        (str(i), str(i)) for i in range(1, 32)
    ])
    repeat_week = fields.Selection([
        ('first', 'First'),
        ('second', 'Second'),
        ('third', 'Third'),
        ('last', 'Last'),
    ], default='first')
    repeat_weekday = fields.Selection([
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ], string='Day Of The Week', readonly=False)
    repeat_month = fields.Selection([
        ('january', 'January'),
        ('february', 'February'),
        ('march', 'March'),
        ('april', 'April'),
        ('may', 'May'),
        ('june', 'June'),
        ('july', 'July'),
        ('august', 'August'),
        ('september', 'September'),
        ('october', 'October'),
        ('november', 'November'),
        ('december', 'December'),
    ])

    @api.constrains('start_date', 'end_date')
    def _check_start_and_end_date(self):
        for record in self:
            if (record.start_date and record.end_date and record.start_date > record.end_date):
                raise ValidationError(_("""Start date cannot be greater than End date."""))
            elif datetime.strptime(str(record.start_date), DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
                raise ValidationError('Please select a date equal/or greater than the current date')
            # elif datetime.strptime(str(record.end_date), DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
            #     raise ValidationError('Please select a date equal/or greater than the current date')
            if (record.start_date and record.med_presc_id.date_med_end and record.med_presc_id.date_med_started):
                if (
                        record.start_date < record.med_presc_id.date_med_started or record.start_date > record.med_presc_id.date_med_end):
                    raise ValidationError("Start and End date Must be between Date Med Start and Date med End")
            if (record.end_date and record.med_presc_id.date_med_end and record.med_presc_id.date_med_started):
                if (
                        record.end_date < record.med_presc_id.date_med_started or record.end_date > record.med_presc_id.date_med_end):
                    raise ValidationError("Start and End date Must be between Date Med Start and Date med End")

    @api.model
    def default_get(self, fields):
        res = super(ScheduleDrugDoses, self).default_get(fields)
        week_start = datetime.today().weekday()
        if self.env.context.get('active_id'):
            res.update({
                'med_presc_id': self.env.context.get('active_id')
            })
        if 'repeat_weekday' in fields:
            res['repeat_weekday'] = self._fields.get('repeat_weekday').selection[week_start][0]
        return res

    @api.onchange('start_date', 'end_date')
    def check_start_end_date(self):
        if (self.start_date and self.end_date and self.start_date > self.end_date):
            raise ValidationError(_("""Start date cannot be greater than End date."""))
        elif self.start_date and datetime.strptime(str(self.start_date), DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
            raise ValidationError('Please select a date equal/or greater than the current date')
        elif self.end_date and datetime.strptime(str(self.end_date), DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
            raise ValidationError('Please select a date equal/or greater than the current date')
        if (self.start_date and self.med_presc_id.date_med_end and self.med_presc_id.date_med_started):
            if(self.start_date < self.med_presc_id.date_med_started or self.start_date > self.med_presc_id.date_med_end):
                raise ValidationError("Start and End date Must be between Date Med Start and Date med End")
        if (self.end_date and self.med_presc_id.date_med_end and self.med_presc_id.date_med_started):
            if (self.end_date < self.med_presc_id.date_med_started or self.end_date > self.med_presc_id.date_med_end):
                raise ValidationError("Start and End date Must be between Date Med Start and Date med End")


    @api.depends('is_recurrence', 'repeat_unit', 'repeat_on_month', 'repeat_on_year')
    def _compute_repeat_visibility(self):
        for dose_schedule in self:
            dose_schedule.repeat_show_day = dose_schedule.is_recurrence and (dose_schedule.repeat_unit == 'month' and dose_schedule.repeat_on_month == 'date') or (dose_schedule.repeat_unit == 'year' and dose_schedule.repeat_on_year == 'date')
            dose_schedule.repeat_show_week = dose_schedule.is_recurrence and (dose_schedule.repeat_unit == 'month' and dose_schedule.repeat_on_month == 'day') or (dose_schedule.repeat_unit == 'year' and dose_schedule.repeat_on_year == 'day')
            dose_schedule.repeat_show_dow = dose_schedule.is_recurrence and dose_schedule.repeat_unit == 'week'
            dose_schedule.repeat_show_month = dose_schedule.is_recurrence and dose_schedule.repeat_unit == 'year'

    def _get_weekdays(self, n=1):
        self.ensure_one()
        if self.repeat_unit == 'week':
            return [fn(n) for day, fn in DAYS.items() if self[day]]
        return [DAYS.get(self.repeat_weekday)(n)]

    def schedule_medicine_dose(self):
        dose_schedule_obj = self.env['drug.doses.schedule']
        day_count = 0
        date_list = []
        today = fields.Date.today()
        tomorrow = today + relativedelta(days=1)
        for dose_line in self:
            if not dose_line.dose_schedule_ids:
                raise ValidationError(_("""Please enter the drug doses timing."""))
            if len(dose_line.dose_schedule_ids) < self.med_presc_id.admin_frequency_id.frequency_count:
                raise ValidationError(_("""You cannot add less dose timing lines. Please check frequency of admin"""))
            start_date = dose_line.start_date
            if not dose_line.end_date:
                # last_day_date = start_date.replace(day = calendar.monthrange(start_date.year, start_date.month)[1])
                last_day_date = start_date.replace(year=start_date.year + 2)
            else:
                last_day_date = dose_line.end_date
            day_count = (last_day_date - start_date).days + 1
            if dose_line.is_recurrence:
                week_day_list = {
                                'mon': dose_line.mon,
                                'tue': dose_line.tue,
                                'wed': dose_line.wed,
                                'thu': dose_line.thu,
                                'fri': dose_line.fri,
                                'sat': dose_line.sat,
                                'sun': dose_line.sun
                                    }
                if dose_line.repeat_unit == 'day':
                    date_list = dose_line.get_day_date_list(start_date, last_day_date, dose_line.repeat_interval,
                                                            dose_line.repeat_unit, week_day_list, day_count)
                elif dose_line.repeat_unit == 'week':
                    date_list = self._get_next_recurring_dates(start_date, dose_line.repeat_interval,
                                                               dose_line.repeat_unit,
                                                               dose_line.repeat_type, dose_line.end_date or last_day_date,
                                                               dose_line.repeat_on_month,
                                                               dose_line._get_weekdays(), dose_line.repeat_day,
                                                               '', dose_line.repeat_month, count=1)
                else:
                    if dose_line.repeat_on_month == 'date':
                        date_list = self._get_next_recurring_dates(start_date, dose_line.repeat_interval,
                                                                   dose_line.repeat_unit,
                                                                   dose_line.repeat_type, dose_line.end_date or last_day_date,
                                                                   dose_line.repeat_on_month,
                                                                   False, dose_line.repeat_day,
                                                                   '', dose_line.repeat_month, count=1)
                    else:
                        date_list = self._get_next_recurring_dates(start_date, dose_line.repeat_interval,
                                                                   dose_line.repeat_unit,
                                                                   dose_line.repeat_type, dose_line.end_date or last_day_date,
                                                                   dose_line.repeat_on_month,
                                                                   dose_line._get_weekdays(
                                                                       WEEKS.get(dose_line.repeat_week)),
                                                                   dose_line.repeat_day,
                                                                   dose_line.repeat_week, dose_line.repeat_month,
                                                                   count=1)
                # date_list = dose_line.get_day_date_list(start_date, last_day_date, dose_line.repeat_interval, dose_line.repeat_unit, week_day_list, day_count)
            else:
                date_list = [d for d in (start_date + timedelta(n) for n in range(day_count)) if d <= last_day_date]
            # for single_date in date_list:
            #     for each_line in dose_line.dose_schedule_ids:
            #         user_tz = self.env.user.tz or 'UTC'
            #         start = datetime.combine(single_date, float_to_time(each_line.drug_time))

            for single_date in date_list:
                for each_line in dose_line.dose_schedule_ids:
                    user_tz = self.env.user.tz or 'UTC'
                    
                    # Convert float time to hours and minutes inline
                    float_time = each_line.drug_time
                    hours = int(float_time)  # Get the whole hours
                    minutes = int((float_time - hours) * 60)  # Get the remaining minutes
                    drug_time = (hours, minutes)  # Create a tuple for hours and minutes
                    
                    # Combine date and time
                    start = datetime.combine(single_date, time(*drug_time))

                    if each_line.am_pm == 'pm':
                        start = start + timedelta(hours=12)
                    start_dt = timezone(user_tz).localize(start).astimezone(UTC)
                    start_dt = start_dt.strftime("%Y-%m-%d %H:%M:%S")
                    # if dose_schedule_obj.sudo().search([
                    #                         ('start_date', '=', start_dt),
                    #                         ('patient_id', '=', dose_line.med_presc_id.patient_id.id)]):
                    #     raise ValidationError(_("""Dose already schedule for the date %s"""%(start_dt)))
                    dose_schedule_obj.sudo().create({
                                            'medi_presc_line_id': dose_line.med_presc_id and\
                                                                dose_line.med_presc_id.id,
                                            'start_date': start_dt,
                                            'end_date': start_dt,
                                            # 'dose': dose_line.dose,
                                            'strength': dose_line.strength,
                                            'team_id': dose_line.team_id and\
                                                        dose_line.team_id.id,
                                            'instructions': dose_line.instructions,
                                            'drug_time': each_line.drug_time
                                            })
            dose_line.med_presc_id.is_dose_schedule = True
            dose_line.med_presc_id.schedule_wiz_id = dose_line.id
        return True

    def get_day_date_list(self, start_date, last_day_date, repeat_interval, repeat_unit, week_day_list, day_count):
        date_list = []
        old_repeat_interval = repeat_interval
        for dose_line in self:
            for n in range(0, day_count):
                if repeat_unit == 'day':
                    if (start_date + timedelta(repeat_interval)) <= last_day_date:
                        if n == 0:
                            date_list.append(start_date + timedelta(n))
                        else:
                            date_list.append(start_date + timedelta(repeat_interval))
                            repeat_interval += old_repeat_interval
                # elif repeat_unit == 'week':pass
        return date_list

    @api.model
    def _get_next_recurring_dates(self, date_start, repeat_interval, repeat_unit, repeat_type, repeat_until,
                                  repeat_on_month, weekdays, repeat_day, repeat_week, repeat_month,
                                  **kwargs):

        count = kwargs.get('count', 1)
        rrule_kwargs = {'interval': repeat_interval or 1, 'dtstart': date_start}
        repeat_day = int(repeat_day)
        start = False
        dates = []
        if repeat_type == 'until':
            rrule_kwargs['until'] = repeat_until if repeat_until else fields.Date.today()
        else:
            rrule_kwargs['count'] = count

        if repeat_unit == 'week' \
                or (repeat_unit == 'month' and repeat_on_month == 'day'):
            rrule_kwargs['byweekday'] = weekdays

        if repeat_unit == 'day':
            rrule_kwargs['freq'] = DAILY
        elif repeat_unit == 'month':
            rrule_kwargs['freq'] = MONTHLY
            if repeat_on_month == 'date':
                start = date_start - relativedelta(days=1)
                if repeat_type == 'until' and repeat_until > date_start:
                    delta = relativedelta(repeat_until, date_start)
                    count = delta.years * 12 + delta.months+1
                for i in range(count):
                    start = start.replace(day=min(repeat_day, monthrange(start.year, start.month)[1]))
                    if start < repeat_until:
                        if i == 0 and start < date_start:
                            # Ensure the next recurrence is in the future
                            start += relativedelta(months=repeat_interval)
                        dates.append(start)
                        start += relativedelta(months=repeat_interval)
                return dates
        else:
            rrule_kwargs['freq'] = WEEKLY
        rules = rrule(**rrule_kwargs)
        return list(rules) if rules else []


class DrugDosesTimingLines(models.Model):
    _name = 'drug.doses.timing.lines'
    # _name = 'wizard.drug.doses.timing.lines'
    _description = 'Drug Doses Timing Lines'

    drug_schedule_id = fields.Many2one('schedule.drug.doses',
                                        string="Drug Schedule")
    drug_time = fields.Float(string="Time")
    am_pm = fields.Selection([
                            ('am', 'AM'),
                            ('pm', 'PM')
                            ],
                            string="AM/PM")

    @api.onchange('drug_time')
    def onchange_drug_time(self):
        if self.drug_time and self.drug_time < 0.0 or self.drug_time > 12.0:
            raise ValidationError(_("""Time should be between 00:01 to 11:59"""))

    @api.model
    def create(self,vals):
        res = super(DrugDosesTimingLines, self).create(vals)
        if res and res.drug_schedule_id and\
        res.drug_schedule_id.med_presc_id and\
        res.drug_schedule_id.med_presc_id.admin_frequency_id and\
        res.drug_schedule_id.med_presc_id.admin_frequency_id.frequency_count:
            if len(res.drug_schedule_id.dose_schedule_ids) > res.drug_schedule_id.med_presc_id.admin_frequency_id.frequency_count:
                raise ValidationError(_("""You cannot add more dose timing lines. Please check frequency of admin."""))
        return res


