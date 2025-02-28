# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    monitoring_template_id = fields.Many2one('via.monitoring.template',
                                             string="Monitoring Template")

    def action_open_monitoring(self):
        pass
