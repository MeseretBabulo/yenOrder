# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError

class ContainerMeasurementLogic(models.Model):
    _name = "container_logic.container_measurement_logic_model"
    _description = "Container Measurement Logic"

    company = fields.Many2one(
        'res.company',
        string="Company",
        required=True
    )

    name = fields.Char(string="Container Type")

    weight = fields.Float(string = "Weight")

    size = fields.Float(string="Size(feet)")
    load_capacity = fields.Float(string="Load Capacity(cubic meter)")


class SalesOrderContainer(models.Model):
    _inherit = 'sale.order'

    enable_container_calculations = fields.Boolean(string="Enable Container Calculations")

    port_of_loading = fields.Char(string="Port Of Loading")
    port_of_discharge = fields.Char(string="Port Of Discharge")

    ico = fields.Char(string="Ico")
    cert_no = fields.Char(string="Certificate No")
    
    container_line_ids = fields.One2many('container.line', 'sale_containers', string="Container Lines")
    def compute_product_ids(self):
        total_service_price = 0
        for record in self.sale_order_option_ids:
            total_service_price += record.price_unit

        # Total quantity for non-service products (storable + consumable)
        total_non_service_qty = sum(self.order_line.mapped('product_uom_qty'))

        print("total_service_price",total_service_price)
        print("total_non_service_qty",total_non_service_qty)

        if total_service_price == 0:
            price_per_kg = 0
        else:
            price_per_kg = total_non_service_qty/total_service_price

        for record in self.container_line_ids:
            record.costs = price_per_kg*record.product_weight
        self.container_line_ids._compute_package_quantity()
    
class ContainerLine(models.Model):
    _name = 'container.line'
    _description = 'Container Line'

    sale_containers = fields.Many2one('sale.order')
    name = fields.Many2one('container_logic.container_measurement_logic_model', string="List of Containers", ondelete='cascade')

    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        domain="[('id', 'in', product_ids)]"  # Use the computed field for domain
    )
    weight = fields.Float(string="Weight",related="name.weight")
    size = fields.Float(string="Size(feet)",related="name.size")
    load_capacity = fields.Float(string="Load Capacity(cubic meter)",related="name.load_capacity")
    product_weight = fields.Float(string="Product Weight")
    packaging_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Package UoM",
        store=True, readonly=False,)
    
    package_quantity = fields.Float(string="Package Quantity", compute="_compute_package_quantity", store=True)

    product_ids = fields.Many2many(
        comodel_name='product.product',
        compute='_compute_product_ids',
        string="Products",
        store=True,
    )

    costs = fields.Float(string="Costs",readonly="1",store=True)
    cont_no = fields.Char(string="Cntr No")
    seal_no = fields.Char(string="Seal No")
    

    # @api.depends('product_weight', 'packaging_uom')
    @api.onchange('product_weight', 'packaging_uom')
    def _compute_package_quantity(self):
        """Automatically compute package quantity based on UoM conversion."""
        print("_compute_package_quantity")
        for record in self:
            print("record",record)
            print("record.product_weight",record.product_weight)
            print("record.packaging_uom",record.packaging_uom)
            if record.product_weight and record.packaging_uom:
                # Convert from the selected UoM to Kg
                kg_value = record.packaging_uom._compute_quantity(1.0, self.env.ref('uom.product_uom_kgm'))
                print("kg_value",kg_value)
                if kg_value:
                    record.package_quantity = record.product_weight / kg_value
                else:
                    record.package_quantity = 0
            else:
                record.package_quantity = 0
        
        print(record.package_quantity)


    @api.depends('sale_containers.order_line.product_id')
    def _compute_product_ids(self):
        for record in self:
            if record.sale_containers:
                # Get the product IDs from the sale order lines
                product_ids = record.sale_containers.order_line.mapped('product_id.id')                
                record.product_ids = [(6, 0, product_ids)]
            else:
                record.product_ids = [(5, 0, 0)]  # Clear the product_ids if no sale order is set

    @api.depends('name')
    def _compute_container_line_cost(self):
        for record in self:
            if record.sale_containers:
                # Get the product IDs from the sale order lines
                product_ids = record.sale_containers.order_line.mapped('product_id.id')                
                record.product_ids = [(6, 0, product_ids)]

            else:
                record.product_ids = [(5, 0, 0)]  # Clear the product_ids if no sale order is set
    @api.constrains('product_weight')
    def _check_product_weight(self):
        """ Validate that product_weight does not exceed the related sale order line's quantity """
        for record in self:
            if record.product_id and record.sale_containers:
                # Find the corresponding sale order line
                sale_order_line = record.sale_containers.order_line.filtered(lambda line: line.product_id == record.product_id)
                
                if sale_order_line:
                    total_ordered_qty = sum(sale_order_line.mapped('product_uom_qty'))  # Get total ordered quantity
                    print("total_ordered_qty",total_ordered_qty)
                    print("total_ordered_qty",total_ordered_qty)
                    if record.product_weight > total_ordered_qty:
                        raise ValidationError(
                            f"Error: The product weight ({record.product_weight} kg) "
                            f"exceeds the available quantity ({total_ordered_qty} kg) in the sale order."
                        )


 