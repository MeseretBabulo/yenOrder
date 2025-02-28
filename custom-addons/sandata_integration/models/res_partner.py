# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

import logging
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_uuid = fields.Char(string="Partner UUID")

    def name_get(self):
        ctx = dict(self._context)
        if ctx.get('create_attendance'):
            result = []
            for partner in self:
                name = partner.name or ""
                if partner.street:
                    name = name + ', ' + partner.street
                if partner.street2:
                    name = name + ', ' + partner.street2
                if partner.city:
                    name = name + ', ' + partner.city
                if partner.state_id:
                    name = name + ', ' + partner.state_id.name
                if partner.country_id:
                    name = name + ', ' + partner.country_id.name
                if partner.zip:
                    name = name + ', ' + partner.zip

                result.append((partner.id, name))
            return result
        else:
            return super(ResPartner, self).name_get()

    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
    #     if args is None:
    #         args = []
    #     if self.env.context.get('create_attendance', False) and self.env.context.get('partner_id', False):
    #         partner_ids = [rec.id for rec in self.search([('parent_id', '=', self.env.context.get('partner_id'))]) if rec]
    #         if partner_ids:
    #             args.append(('id', 'in', list(set(([self.env.context.get('partner_id')]+partner_ids)))))
    #     return super(ResPartner, self)._name_search(name=name, args=args, operator=operator, limit=100, name_get_uid=name_get_uid)

