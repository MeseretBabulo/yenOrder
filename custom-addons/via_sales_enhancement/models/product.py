# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductPack(models.Model):
    _inherit = 'product.template'

    is_special_service = fields.Boolean('Special Service')
    isp_description = fields.Html('ISP Description')
