from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_view_picking(self):
        pickings = self.picking_ids
        transport_records = self.transport_record_ids
        if transport_records and pickings:
            # Extract transport data from first record
            transport_data = {
                'vehicle_type': transport_records[0].vehicle_type,
                'plate_number': transport_records[0].plate_number,
                'driver_id': transport_records[0].driver_id.id,
                'transport_provider_id': transport_records[0].transport_provider_id.id,
                'transport_record': True
            }

            if transport_data:
                _logger.info("Updating pickings with: %s", {
                    k: v for k, v in transport_data.items() 
                    if not k.endswith('_id')
                })
                pickings.sudo().write(transport_data)

        # FIX: Call super OUTSIDE the if/else blocks
        return super().action_view_picking()
    
class SorckPicking(models.Model):
    _inherit = 'stock.picking'
    
    transport_record = fields.Boolean()
    vehicle_type = fields.Char(string='Vehicle Type')
    plate_number = fields.Char(string='Plate Number')
    driver_id = fields.Many2one(
        'res.partner', string='Driver', domain="[('is_company', '=', False)]")
    transport_provider_id = fields.Many2one(
        'res.partner', string='Transport Provider', domain="[('is_company', '=', True)]")
    
class VehicleType(models.Model):
    _name = 'vehicle.type'
    _description = 'Vehicle Type'

    # Fields
    name = fields.Char(string='Vehicle Type', required=True)

class LocationCombination(models.Model):
    _name = 'location.combination'
    _description = 'Location Combination (Country and State/City)'

    country = fields.Many2one('res.country', string='Country', required=True)
    state = fields.Many2one('res.country.state', string='State/City', required=True, domain="[('country_id', '=', country)]")
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    @api.depends('country', 'state')
    def _compute_display_name(self):
        for record in self:
            country_name = record.country.name if record.country else ''
            state_name = record.state.name if record.state else ''
            if country_name and state_name:
                record.display_name = f"{state_name}, {country_name}"
            elif country_name:
                record.display_name = country_name
            elif state_name:
                record.display_name = state_name
            else:
                record.display_name = "Unknown Location"  # Fallback value


   
    
class TransportRecord(models.Model):
    _name = 'transport.record'
    _inherit = ['mail.thread']
    _description = 'Transport Record'

    # Fields for the transport record
    name = fields.Char(
        string='Sequence', required=True, copy=False, readonly=True, default=lambda self: 'New')
    transport_provider_id = fields.Many2one(
        'res.partner', string='Transport Provider', domain="[('is_company', '=', True)]", required=True)
    driver_id = fields.Many2one(
        'res.partner', string='Driver', domain="[('is_company', '=', False)]", required=True)
    vehicle_type = fields.Many2one(
        'vehicle.type', 
        string='Vehicle Type', 
        required=True, 
        help="Select the type of vehicle used for transport"
    )
    plate_number = fields.Char(string='Plate Number', required=True)
    pick_up_date = fields.Date(string='Pick-Up Date', required=True)
    delivery_date = fields.Date(string='Delivery Date', required=True)
    source = fields.Many2one(
        'location.combination', 
        string='Source', 
        required=True, 
        domain="[]", 
        help="Select the source location (e.g., Addis Ababa, Ethiopia)"
    )
    destination = fields.Many2one(
        'location.combination', 
        string='Destination', 
        required=True, 
        domain="[]", 
        help="Select the destination location (e.g., Dire Dawa, Ethiopia)"
    )
    transport_cost = fields.Float(string='Transportation Unit Price')
    driver_per_diem = fields.Float(string="Driver Per Diem", default=0.0, store=True)
    total_cost = fields.Float(string="Total Cost", compute='_compute_total_cost', default=0.0, store=True)
    destination_weight = fields.Float(string='Destination Weight (in quintal)')
    state = fields.Selection(
        [('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('cancelled', 'Cancelled'), 
         ('transport_billed', 'Transport Billed'), ('per_diem_billed', 'Per Diem Billed'),('done', 'Done')],
        default='draft',
        required=True,
    )
    sale_order_id = fields.Many2one('sale.order', string='Related Sale Order')
    purchase_order_id = fields.Many2one('purchase.order', string='Related Purchase Order')
    transport_bill_id = fields.Many2one('account.move', string='Transport Vendor Bill', readonly=True, copy=False)
    per_diem_bill_id = fields.Many2one('account.move', string='Per Diem Vendor Bill', readonly=True, copy=False)
    transport_bill_count = fields.Integer(compute='_compute_transport_bill_count')
    per_diem_bill_count = fields.Integer(compute='_compute_per_diem_bill_count')

    @api.depends('transport_bill_id')
    def _compute_transport_bill_count(self):
        for record in self:
            record.transport_bill_count = 1 if record.transport_bill_id else 0

    @api.depends('per_diem_bill_id')
    def _compute_per_diem_bill_count(self):
        for record in self:
            record.per_diem_bill_count = 1 if record.per_diem_bill_id else 0

    @api.depends('driver_per_diem', 'delivery_date', 'pick_up_date')
    def _compute_total_cost(self):
        for record in self:
            if record.pick_up_date and record.delivery_date:
                duration = (record.delivery_date - record.pick_up_date).days
                record.total_cost = record.driver_per_diem * duration
            else:
                record.total_cost = 0
                
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('transport.record') or 'New'  
        # Get active model and ID from context
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        
        # Update related records
        if active_model == 'purchase.order':
            purchase_order = self.env['purchase.order'].browse(active_id)
            purchase_order.transport_record = True
            vals.setdefault('purchase_order_id', active_id)
            
        elif active_model == 'sale.order':
            sale_order = self.env['sale.order'].browse(active_id)
            sale_order.transport_record = True
            vals.setdefault('sale_order_id', active_id)
        
        # Create the record
        return super(TransportRecord, self).create(vals)

    def action_submit(self):
        self.state = 'submitted'
        

    def action_approve(self):
        self.state = 'approved'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_set_to_draft(self):
        self.state = 'draft'

    def action_create_transport_bill(self):
        self.ensure_one()
        _logger.info("kkkkkk %s",self.state)
        if self.state not in ['approved','per_diem_billed']:
            raise UserError("The Transport Record must be in Approved state to create bills.")

        if self.transport_bill_id:
            raise UserError("A Transport bill has already been created for this transportation record.")

        # Search for the 'Transport' product
        transport_product = self.env['product.product'].search([('name', '=', 'Transport')], limit=1)
        if not transport_product:
            raise UserError("The 'Transport' product must be created in the system.")

        # Ensure the product has a valid expense account
        expense_account = transport_product.property_account_expense_id or transport_product.categ_id.property_account_expense_categ_id
        if not expense_account:
            raise UserError("The 'Transport' product or its category does not have a valid expense account configured.")

        # Create the bill with the correct account
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.transport_provider_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': transport_product.id,
                'quantity': self.destination_weight,
                'price_unit': self.transport_cost,
                'account_id': expense_account.id,  
            })],
        })
        _logger.info('biiiiii %s', bill)
        self.transport_bill_id = bill.id
        self.state = 'transport_billed'

    def action_create_per_diem_bill(self):
        self.ensure_one()
        if self.state not in ['transport_billed','transport_billed']:
            raise UserError("The Transport Record must be in Transport Billed state to create per diem bills.")

        if self.per_diem_bill_id:
            raise UserError("A Per Diem bill has already been created for this transportation record.")

        # Ensure the Per Diem product exists
        per_diem_product = self.env['product.product'].search([('name', '=', 'Per Diem')], limit=1)
        if not per_diem_product:
            per_diem_product = self.env['product.product'].create({
                'name': 'Per Diem',
                'type': 'service',
                'categ_id': self.env.ref('product.product_category_all').id,
            })

        # Get the expense account from the product's category
        expense_account = per_diem_product.categ_id.property_account_expense_categ_id
        if not expense_account:
            raise UserError("The product category does not have an expense account configured.")

        # Create the bill with the correct account
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.driver_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': per_diem_product.id,
                'quantity': self.destination_weight,
                'price_unit': self.driver_per_diem,
                'name': per_diem_product.name,
                'account_id': expense_account.id, 
            })],
        })
        self.per_diem_bill_id = bill.id
        self.state = 'done'

    def action_view_transport_bills(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transport Bills',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', '=', self.transport_bill_id.id)],
            'target': 'current',
        }

    def action_view_per_diem_bills(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Per Diem Bills',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', '=', self.per_diem_bill_id.id)],
            'target': 'current',
        }


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    transport_record = fields.Boolean()
    transport_record_ids = fields.One2many(
        'transport.record', 'purchase_order_id', string='Transport Records')
    enable_transport_tracking = fields.Boolean(string="Enable Transport Tracking")
    
    def action_create_transport_record(self):
        """Action to open the Transport Record form and link it to the Purchase Order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Transport Record',
            'view_mode': 'form',
            'res_model': 'transport.record',
            'context': {'default_purchase_order_id': self.id},
            'target': 'new',
        }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    transport_record = fields.Boolean()
    transport_record_ids = fields.One2many(
        'transport.record', 'sale_order_id', string='Transport Records')
    enable_transport_tracking = fields.Boolean(string="Enable Transport Tracking")
    
    def action_create_transport_record(self):
        """Action to open the Transport Record form and link it to the Sale Order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Transport Record',
            'view_mode': 'form',
            'res_model': 'transport.record',
            'context': {'default_sale_order_id': self.id},
            'target': 'new',
        }
