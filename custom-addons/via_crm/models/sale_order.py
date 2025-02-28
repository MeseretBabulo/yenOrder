# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res and res.order_line:
            res.partner_id.service_ids = res.partner_id.service_ids.ids  +\
                [product_id.product_tmpl_id.id
                for product_id in res.order_line.mapped('product_id')
                if product_id.product_tmpl_id]
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for so in self:
            so_ids = self.search([
                ('state', '!=', 'cancel'),
                ('partner_id', '=', so.partner_id.id)
                ])
            service_ids =[product_id.product_tmpl_id.id for so in so_ids
                for product_id in so.order_line.mapped('product_id')
                if product_id.product_tmpl_id]
            so.partner_id.service_ids = list(set(service_ids)) if service_ids else [(6, 0, [])]
        return res