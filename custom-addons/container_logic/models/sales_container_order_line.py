from odoo import api, fields, models, _
class SalesOrderLineContainer(models.Model):
    _inherit = 'sale.order.line' 

    gross_quantity = fields.Float(string="Gross Quantity")

    hs_code = fields.Char(string="HS Code")

    def _prepare_invoice_line(self, sequence=None):
        """Override to include custom fields when creating invoice lines."""
        # Call the super method to get default invoice line values
        invoice_line_vals = super()._prepare_invoice_line(sequence=sequence)
        # print("invoice_line", invoice_line_vals)


        # Reference to Pound UoM (Ensure this exists in UoM settings)
        pound_uom = self.env.ref('uom.product_uom_lb', raise_if_not_found=False)  

        # Calculate quantity in pounds
        quantity_lb = 0.0
        if self.product_uom and pound_uom:
            quantity_lb = self.product_uom._compute_quantity(self.product_uom_qty, pound_uom)

        print("quantity_lb",quantity_lb)
        # Add custom field to invoice line values
        invoice_line_vals.update({
            'hs_code': self.hs_code,  
            'gross_quantity': self.gross_quantity 
        })
        
        return invoice_line_vals

    
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        print("invoice_vals",invoice_vals)
        # Pass custom sale order values to the invoice
        invoice_vals.update({
            'port_of_loading': self.port_of_loading,
            'port_of_discharge': self.port_of_discharge,
            'ico': self.ico,
            'cert_no': self.cert_no,
        })
        
        return invoice_vals

    