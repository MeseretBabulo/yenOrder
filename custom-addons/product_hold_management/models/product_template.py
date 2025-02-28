from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_held = fields.Boolean(
        string='On Hold',
        default=False,
        help='If checked, this product variant cannot be sold until released by an admin'
    )
    hold_reason = fields.Text(
        string='Hold Reason',
        help='Reason why this product variant is put on hold'
    )
    hold_date = fields.Datetime(
        string='Hold Date',
        readonly=True,
        copy=False
    )
    held_by = fields.Many2one(
        'res.users',
        string='Held By',
        readonly=True,
        copy=False
    )

    def action_hold_product(self):
        self.ensure_one()
        # Check if product is a storable product
        if self.type != 'product':
            raise UserError(_('Only storable products can be put on hold.'))
        
        # Check if product has stock
        if self.qty_available <= 0:
            raise UserError(_('Cannot put product variant on hold: No stock available.'))
            
        # Open a form view to input the hold reason
        return {
            'name': _('Hold Product'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.product',
            'res_id': self.id,
            'target': 'new',
            'view_id': False,
            'views': [(False, 'form')],
            'context': {
                'default_hold_reason': False,
                'form_view_ref': 'product_hold_management.view_hold_product_reason_form',
            },
        }

    def action_confirm_hold(self):
        self.ensure_one()
        if not self.hold_reason:
            raise UserError(_('Please provide a reason for holding the product variant.'))
            
        self.write({
            'is_held': True,
            'hold_date': fields.Datetime.now(),
            'held_by': self.env.user.id,
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_release_product(self):
        self.ensure_one()
        self.write({
            'is_held': False,
            'hold_date': False,
            'held_by': False,
            'hold_reason': False,
        }) 