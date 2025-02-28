# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

import pytz
from odoo import api, fields, models, _
from datetime import datetime


class ResidentialFormsReport(models.AbstractModel):
    _name = 'report.via_mar.report_residential_forms_template'
    _description = 'Residential Report'

    def get_drill_records(self, records):
        fire_drill_ids = self.env['residential.fire.drill'].sudo().\
            search([('create_date', '>=', str(records.date_from) + ' 00:00:00'),
                    ('create_date', '<=', str(records.date_to) + ' 23:59:59'),
                    ('person_support_id', '=', records.person_support_id.id)],
                   order='id asc')
        return fire_drill_ids

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('via_mar.report_residential_forms_template')
        record_id = data['form']['id'] if data and data.get('form', False) and data.get('form').get('id', False) else \
        docids[0]
        records = self.env['residential.report'].browse(record_id)
        docids = records.ids
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        res = {
            'doc_model': 'residential.report',
            'doc_ids': docids,
            'docs': records,
            'data': data,
            'get_drill_records': self.get_drill_records(records),
            'current_time': datetime.now().astimezone(local),
            'current_user': self.env.user.name
        }
        return res
