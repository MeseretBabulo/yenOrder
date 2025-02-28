# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ResidentialReport(models.TransientModel):
    _name = 'residential.report'
    _description = 'HR Time Off Summary Report By Employee'

    person_support_id = fields.Many2one('res.partner', string="Person Supported")
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='End Date', required=True)

    def check_date_range(self):
        if self.date_to < self.date_from:
            raise ValidationError(_('Enter proper date range'))

    def print_report(self):
        self.check_date_range()
        datas = {'form': {'date_from': self.date_from,
                          'date_to': self.date_to,
                          'id': self.id,
                          },
                 }
        return self.env.ref('via_mar.action_report_residential').report_action(self, data=datas)
