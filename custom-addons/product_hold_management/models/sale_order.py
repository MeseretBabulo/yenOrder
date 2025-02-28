from odoo import models, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            held_products = order.order_line.filtered(lambda l: l.product_id.is_held)
            if held_products:
                held_product_names = ', '.join(held_products.mapped('product_id.display_name'))
                raise UserError(_(
                    'The following product variants are currently on hold and cannot be sold: %s\n'
                    'Please contact the administrator for more information.'
                ) % held_product_names)
        return super(SaleOrder, self).action_confirm()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_product_id_check_hold(self):
        if not self.product_id:
            return
            
        if self.product_id.is_held:
            product_name = self.product_id.display_name
            hold_reason = self.product_id.hold_reason
            held_by = self.product_id.held_by.name if self.product_id.held_by else _('Unknown')
            
            message = _("""
Product Variant: %s

⚠️ This product variant is currently on HOLD

Reason: %s

Placed on hold by: %s
            """) % (product_name, hold_reason or _('No reason specified'), held_by)
            
            return {
                'warning': {
                    'title': _('⛔ Product On Hold'),
                    'message': message
                },
                'value': {'product_id': False},
                'domain': {'product_id': []}
            }
