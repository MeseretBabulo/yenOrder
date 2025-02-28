from odoo import models, fields, _, api
from odoo.exceptions import UserError
import logging
_logger  = logging.getLogger(__name__)

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    selected_country = fields.Char(string="Selected Item")

    hs_code = fields.Char(string="HS Code")

    