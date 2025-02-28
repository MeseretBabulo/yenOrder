# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


import math
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    def name_get(self):
        res = []
        for analytic in self:
            name = analytic.name
            if analytic.code:
                name = '[' + analytic.code + '] ' + name
            # if analytic.partner_id.commercial_partner_id.name:
            #     name = name + ' - ' + analytic.partner_id.commercial_partner_id.name
            res.append((analytic.id, name))
        return res


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'

    service_bill_unit = fields.Char()

    @api.onchange('product_id', 'product_uom_id', 'unit_amount', 'currency_id')
    def on_change_unit_amount(self):
        if not self.product_id:
            self.service_bill_unit = math.ceil(((self.unit_amount * 100) / 25))
            return {}

        result = 0.0
        prod_accounts = self.product_id.product_tmpl_id.with_company(self.company_id)._get_product_accounts()
        unit = self.product_uom_id
        account = prod_accounts['expense']
        if not unit or self.product_id.uom_po_id.category_id.id != unit.category_id.id:
            unit = self.product_id.uom_po_id

        # Compute based on pricetype
        amount_unit = self.product_id.price_compute('standard_price', uom=unit)[self.product_id.id]
        amount = amount_unit * self.unit_amount or 0.0
        result = (self.currency_id.round(amount) if self.currency_id else round(amount, 2)) * -1
        self.amount = result
        self.general_account_id = account
        self.product_uom_id = unit
