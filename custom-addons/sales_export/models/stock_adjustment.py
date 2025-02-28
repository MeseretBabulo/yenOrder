from odoo import models, fields, _, api
from odoo.exceptions import UserError
from num2words import num2words
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import check_barcode_encoding, groupby, SQL
from odoo.tools.float_utils import float_compare, float_is_zero

import logging
_logger  = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    grade = fields.Selection([
        ('5', 'Grade 5'),
        ('4', 'Grade 4'),
        ('3', 'Grade 3'),
        ('2', 'Grade 2'),
        ('1', 'Grade 1'),
    ], string="Coffee Grade", company_dependent=True)

   
    
class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _domain_product_id(self):
        if self.user_has_groups('stock.group_stock_user'):
            return ("[] if not context.get('inventory_mode') else"
                " [('type', '=', 'product'), ('product_tmpl_id', 'in', context.get('product_tmpl_ids', []) + [context.get('product_tmpl_id', 0)])] if context.get('product_tmpl_ids') or context.get('product_tmpl_id') else"
                " [('type', '=', 'product')]")
        return "[]"
    @api.model
    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when creating a quant in `inventory_mode`. """
        return super()._get_inventory_fields_create() + ['origin_product', 'grade', 'to_grade']

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when modifying a quant in `inventory_mode`. """
        fields = super()._get_inventory_fields_write()
        fields.extend(['origin_product', 'grade', 'to_grade'])
        return fields

    origin_product = fields.Many2one(
        'product.product', 'Origin Product',
        domain=lambda self: self._domain_product_id(),
        check_company=True)
    grade = fields.Selection([
        ('6', 'Grade 6'),
        ('5', 'Grade 5'),
        ('4', 'Grade 4'),
        ('3', 'Grade 3'),
        ('2', 'Grade 2'),
        ('1', 'Grade 1')
    ], string='From')
    to_grade = fields.Selection([
        ('6', 'Grade 6'),
        ('5', 'Grade 5'),
        ('4', 'Grade 4'),
        ('3', 'Grade 3'),
        ('2', 'Grade 2'),
        ('1', 'Grade 1')
    ], string='TO')
    
    @api.onchange('origin_product')
    def _onchange_origin_product(self):
        """ Auto-fill grade when origin_product is selected """
        if self.origin_product:
            self.grade = self.origin_product.grade

        """ Auto-fill to_grade when product_id is selected """
        if self.product_id:
            self.to_grade = self.product_id.grade

  
    # def action_apply_inventory(self):
    #     """
    #     Overriding the stock inventory apply action to adjust stock
    #     based on coffee grade improvement.
    #     """
    #     _logger.info(" self %s",self.company_id.name)
    #     if self.company_id.id == 2:
    #         _logger.info("yyyyyyyyy")
            
    #         for quant in self:
    #             if quant.origin_product and quant.to_grade:
    #                 # Reduce stock of the origin product
    #                 origin_quant = self.env['stock.quant'].search([
    #                     ('product_id', '=', quant.origin_product.id),
    #                     ('location_id', '=', quant.location_id.id)
    #                 ], limit=1)

    #                 _logger.info("origin_quant : %s",origin_quant)
    #                 _logger.info("origin_quant.quantity : %s",origin_quant.quantity)
    #                 _logger.info("quant.quantity : %s",quant.quantity)
    #                 _logger.info("quant : %s",quant.to_grade)
    #                 if origin_quant and origin_quant.quantity >= quant.inventory_diff_quantity:
    #                     origin_quant.quantity -= quant.quantity
    #                 else:
    #                     raise UserError("quantity in the original product to adjust... less than converted grade quantity")

    #                 # Assign the new grade to the target product and adjust quantity
    #                 target_product = self.env['product.product'].search([
    #                     ('name', '=', quant.origin_product.name),
    #                     ('grade', '=', quant.grade)
    #                 ], limit=1)

    #                 _logger.info( "target_product %s",target_product)
    #                 _logger.info( "quant.inventory_diff_quantity %s",quant.inventory_diff_quantity)
    #                 if not target_product:
    #                     raise UserError("No matching product found with the upgraded grade.")
                    
    #                 diff_qty = origin_quant.quantity - quant.inventory_diff_quantity
    #                 new_quant = self.create({
    #                     'product_id': target_product.id,
    #                     'location_id': quant.location_id.id,
    #                     'inventory_quantity': diff_qty,
    #                     # 'inventory_quantity': quant.quantity,
    #                 })
    #                 _logger.info( "new_quant %s",new_quant)
    #                 _logger.info( "new_quant %s",new_quant.inventory_quantity)
    #     else:
    #         _logger.info( "nnnnnnnnnnnn")
                

    #     # Call the original apply function
    #     return super(StockQuant, self).action_apply_inventory()

    def action_apply_inventory(self):
        """
        Overriding the stock inventory apply action to adjust stock
        based on coffee grade improvement.
        """
        _logger.info("Processing Inventory Adjustment for Company: %s", self.company_id.name)

        if self.company_id.id != 2:
            _logger.info("Skipping adjustment as the company ID is not 2.")
            return super(StockQuant, self).action_apply_inventory()
        for quant in self:
            if quant.origin_product and quant.grade and quant.to_grade:
                _logger.info("Processing Adjustment for Product: %s | Original Grade: %s | New Grade: %s",
                             quant.origin_product.name, quant.grade, quant.to_grade)

                # Fetch stock of the origin product in the same location
                origin_quant = self.env['stock.quant'].search([
                    ('product_id', '=', quant.origin_product.id),
                    ('location_id', '=', quant.location_id.id)
                ], limit=1)

                if not origin_quant:
                    raise UserError(f"No available stock found for the origin product '{quant.origin_product.display_name}' in the selected location.")

                _logger.info("Origin Product Stock Before Adjustment: %s KG", origin_quant.quantity)

                # Validate stock availability before adjustment
                if origin_quant.quantity < quant.inventory_diff_quantity:
                    raise UserError(f"Insufficient stock! Available: {origin_quant.quantity} {origin_quant.product_id.uom_id.name}, Required: {quant.inventory_diff_quantity} {quant.product_id.uom_id.name}.")

                # Find the corresponding upgraded product variant
                target_product = self.env['product.product'].search([
                    ('name', '=', quant.origin_product.name),
                    ('grade', '=', quant.grade)
                ], limit=1)

                if not target_product:
                    raise UserError(f"No matching product found with the upgraded grade '{quant.to_grade}'.")

                _logger.info("Target Product Found: %s | New Grade: %s", target_product.name, quant.to_grade)

           
                # Deduct stock from the origin product using stock move
                _logger.info("Origin Product Stock After Deduction: %s KG", origin_quant.quantity)

                # Create a new stock quant for the upgraded product
                new_quant = self.create({
                    'product_id': target_product.id,
                    'location_id': quant.location_id.id,
                    'inventory_quantity': origin_quant.quantity - quant.inventory_diff_quantity,
                })

                _logger.info("Created New Stock Quant: %s | Quantity: %s KG", new_quant.product_id.name, new_quant.inventory_quantity)

        _logger.info("Inventory Adjustment Process Completed Successfully!")
        return super(StockQuant, self).action_apply_inventory()
    
    
    
    def _get_inventory_move_values(self, qty, location_id, location_dest_id, package_id=False, package_dest_id=False):
        """
        Called when user manually sets a new quantity (via `inventory_quantity`)
        just before creating the corresponding stock move.

        :param location_id: `stock.location`
        :param location_dest_id: `stock.location`
        :param package_id: `stock.quant.package`
        :param package_dest_id: `stock.quant.package`
        :return: dict with all values needed to create a new `stock.move` with its move line.
        """
        self.ensure_one()

        # Default naming logic
        if self.env.context.get('inventory_name'):
            name = self.env.context.get('inventory_name')
        elif fields.Float.is_zero(qty, 0, precision_rounding=self.product_uom_id.rounding):
            name = _('Product Quantity Confirmed')
        else:
            name = _('Product Quantity Updated')

        # Custom Naming for Coffee Grade Improvement
        if self.origin_product and self.grade and self.to_grade:
            name = f"Quality Upgrade: {self.origin_product.name} (Grade {self.grade} → {self.to_grade})"

        if self.user_id and self.user_id.id != SUPERUSER_ID:
            name += f' ({self.user_id.display_name})'

        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': qty,
            'company_id': self.company_id.id or self.env.company.id,
            'state': 'confirmed',
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'is_inventory': True,
            'picked': True,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom_id.id,
                'quantity': qty,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id,
                'company_id': self.company_id.id or self.env.company.id,
                'lot_id': self.lot_id.id,
                'package_id': package_id.id if package_id else False,
                'result_package_id': package_dest_id.id if package_dest_id else False,
                'owner_id': self.owner_id.id,
            })]
        }