from odoo import api, fields, models, _
from num2words import num2words
class AccountMove(models.Model):
    _inherit = "account.move"

    port_of_loading = fields.Char(string="Port Of Loading")
    port_of_discharge = fields.Char(string="Port Of Discharge")

    ico = fields.Char(string="Ico")
    cert_no = fields.Char(string="Certificate No")

    total_price_in_words = fields.Char(string= "Total Price in Words")




class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    gross_quantity = fields.Char(string="Gross Quantity")  # Replace with your field type

    hs_code = fields.Char(string="HS Code")
    quantity_lb = fields.Char(string="Quantity(LB)")


