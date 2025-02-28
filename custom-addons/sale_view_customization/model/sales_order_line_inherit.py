from odoo import models, fields, _, api
from odoo.exceptions import UserError
import logging
_logger  = logging.getLogger(__name__)

class SalesOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'


    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Override the default behavior to set price_unit as standard_price instead of list_price.
        """
        if self.product_id:
            self.price_unit = self.product_id.standard_price
    