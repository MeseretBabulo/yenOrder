# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models
from odoo.http import request


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _load_menus_blacklist(self):
        self.clear_caches()
        res = super()._load_menus_blacklist()
        if request.httprequest.cookies.get('cids'):
            cid = request.httprequest.cookies.get('cids').split(',')
            company_id = self.env['res.company'].browse(int(cid[0]))
        else:
            company_id = self.env.user.company_id if self.env.user and self.env.user.company_id else False
        # if company_id.via_company_type != 'pa':
        # # # if self.env.user and self.env.user.company_ids[0].via_company_type != 'pa':
        #     res.append(self.env.ref('via_sales_enhancement.menu_via_service_note').id)
        #     res.append(self.env.ref('via_sales_enhancement.menu_via_error_code').id)
        #     res.append(self.env.ref('via_sales_enhancement.menu_via_service_note_survey').id)
        return res


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        self.env['ir.ui.menu'].sudo()._load_menus_blacklist()
        info = super().session_info()
        return info
