# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    def action_apply(self):
        ctx = dict(self.env.context)
        ctx.update({'from_crm': True})
        self.env.context = ctx
        res = super(Lead2OpportunityPartner, self).action_apply()
        return res


class Opportunity2Quotation(models.TransientModel):
    _inherit = 'crm.quotation.partner'

    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        ctx = dict(self.env.context)
        ctx.update({'from_crm': True})
        self.env.context = ctx
        self.ensure_one()
        res = super(Opportunity2Quotation, self).action_apply()
        return res
