# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    sale_id = fields.Many2one('sale.order')

    def write(self, vals):
        if 'sale_id' in vals:
            vals.update({'res_id': vals.get('sale_id'),
                         'res_model': 'sale.order',
                         'company_id': self.env.company.id})
        return super(DocumentsDocument, self).write(vals)
