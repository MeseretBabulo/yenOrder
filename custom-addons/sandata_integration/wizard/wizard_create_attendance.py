# -*- coding: utf-8 -*-
import pytz
from odoo import api, fields, models,tools, _
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class WizardCreateAttendance(models.TransientModel):
    _name = 'wizard.create.attendance'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner',
                                string="Customer")
    check_in_time = fields.Datetime(string="Check-In")
    check_out_time = fields.Datetime(string="Check-Out")
    is_new = fields.Boolean(string="Is New?")
    is_check_in = fields.Boolean(string="Is Check-in?")
    partner_firstname = fields.Char(string="Firstname")
    partner_lastname = fields.Char(string="Lastname")
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    zip = fields.Char(string='Zip')
    city = fields.Char(string='City')
    state_id = fields.Many2one(
        "res.country.state", string='State')
    country_id = fields.Many2one(
        'res.country', string='Country')

    @api.constrains('check_in_time', 'check_out_time')
    def _check_in_check_out(self):
        for man_attendance in self:
            if man_attendance.check_in_time and\
                (man_attendance.check_in_time > datetime.now()):
                raise ValidationError(_("""Check-in date cannot be future date."""))
            if man_attendance.check_out_time and\
                (man_attendance.check_out_time > datetime.now()):
                raise ValidationError(_("""Check-out date cannot be future date."""))

    @api.model
    def default_get(self, fields):
        res= super(WizardCreateAttendance, self).default_get(fields)
        if self.env.context.get('from_main_task', False):
            res.update({
                'is_check_in': True
                })
        return res

    def action_create_attendance(self):
        partner_obj = self.env['res.partner']
        partner_id = self.partner_id
        for create_attendance in self:
            # if create_attendance.is_new and not self.env.context('from_checkout', False):
            if create_attendance.is_new and not self.env.context.get('from_checkout', False):
                partner_id = partner_obj.create({
                    'name': create_attendance.partner_firstname + create_attendance.partner_lastname,
                    'street': create_attendance.street,
                    'street2': create_attendance.street2,
                    'zip': create_attendance.zip,
                    'city': create_attendance.city,
                    'state_id': create_attendance.state_id.id,
                    'country_id': create_attendance.country_id.id,
                    'type': 'other',
                    'partner_type': 'other',
                    'parent_id': self.env.context.get('default_partner_id', False)
                })
        if partner_id:
            if self.is_check_in:
                partner_id.geo_localize()
                return self.env['project.task'].with_context(create_attendance=True,
                                                             partner_id=partner_id,
                                                             check_in_time=self.check_in_time).timesheet_sign_in()
            else:
                return self.env['project.task'].with_context(create_attendance=True,
                                                             partner_id=partner_id,
                                                             from_checkout=True,
                                                             check_out_time=self.check_out_time).timesheet_sign_out()
