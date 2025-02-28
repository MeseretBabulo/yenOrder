from odoo import models, fields, _, api
from odoo.exceptions import UserError
from num2words import num2words
import logging
_logger  = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('bank_sent', 'Sent Proforma to Bank'),
        ('bank_approved', 'Bank Approved'),
        ('sent', 'PO Sent to Supplier'),
        ('docs_received', 'Received Supplier Docs'),
        ('submit_documents', 'Submit Documents to Bank'),
        ('purchase', 'Purchase Order'),
        ('vendor_shipped', 'Supplier Shipment'),
        ('custom_clearance', 'Custom Clearance'),
        ('arrived', 'Arrived'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    supplier_attachment_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[('res_model', '=', 'purchase.order')],
        string="Supplier Attachments"
    )
    # field for determinnig Type of Purchase

    is_direct_purchase = fields.Boolean(string="Is Direct purchase")

    # field for filtering type of users

    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, change_default=True, tracking=True, domain="['&', ('is_vendor', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

    proforma_invoice = fields.Char(string= "Proforma Invoice")

    total_price_in_words = fields.Char(compute='_compute_amount', store=False)

    def convert_to_birr(self,word):
        """
        Converts the word 'point' to 'birr' in a string and adds 'cents' 
        at the end if the string doesn't already end with 'birr'.
        
        Args:
            word (str): The input string to process.
        
        Returns:
            str: The processed string with 'point' replaced by 'birr' 
                and 'cents' appended if necessary.
        """
        # Replace 'point' with 'birr'
        converted = word.replace("euro", "birr")
        
        return converted



    @api.depends('order_line')
    def _compute_amount(self):
        total_amount = 0
        for line in self.order_line:
            tax_results = self.order_line.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = next(iter(tax_results['totals'].values()))
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']
            total_amount = total_amount + amount_untaxed + amount_tax
        self.total_price_in_words = self.convert_to_birr(str(num2words(total_amount, to = 'currency'))).upper()


    @api.onchange('order_line')
    def _compute_orderline_country(self):
        for record in self.order_line:
            for rec in record.product_id.product_template_variant_value_ids:
                if rec.attribute_id.name == "Country":
                    record.selected_country = rec.name

                
    def action_rfq_send(self):
        self.write({'state': 'sent'})
        return super(PurchaseOrder, self).action_rfq_send()
    
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft','submit_documents', 'sent']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True
    
    def button_bank_sent(self):
        """Send email to the bank with the proforma invoice as an attachment."""
        if not self.order_line:
            raise UserError(_("You need to add at least one product line before sending to the bank."))

        template = self.env.ref('purchase.email_template_edi_purchase', raise_if_not_found=False)
        if template:
            self.message_post_with_template(template.id)
        else:
            raise UserError(_("Email template for sending to the bank not found."))

        self.write({'state': 'bank_sent'})

    # def button_docs_received(self):
    #     """Open a wizard to upload and store supplier documents."""
    #     self.ensure_one()  # Ensure this is called on a single record
    #     return {
    #         'name': _('Upload Supplier Documents'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'purchase.uploadwizard.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_res_id': self.id,  # Pass the current purchase order's ID to the wizard
    #             'default_res_model': 'purchase.order',  # Specify the model to which the attachment belongs
    #             'active_id': self.id,  # Pass the active purchase order ID
    #             'active_model': 'purchase.order',  # Specify that the active model is 'purchase.order'
    #         },
    #     }
    def button_docs_received(self):
        """Open a wizard to upload and store supplier documents."""
        self.ensure_one()  # Ensure this is called on a single record
        return {
            'name': _('Upload Supplier Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.uploadwizard.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_id': self.id,  # Pass the current purchase order's ID to the wizard
                'default_res_model': 'purchase.order',  # Specify the model to which the attachment belongs
                'active_id': self.id,  # Pass the active purchase order ID
                'active_model': 'purchase.order',  # Specify that the active model is 'purchase.order'
            },
        }
            
        
    def action_send_to_bank(self):
        """
        Opens a window to compose an email with the "Send to Bank" template loaded by default.
        """
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data._xmlid_lookup('purchase_new_states.email_template_send_to_bank')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_ids': self.ids,
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
        })

        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Proforma Invoice Sent to Bank')
        self.write({'state': 'bank_sent'})

        return {
            'name': _('Compose Email to Bank'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        
        
    def button_submit_documents(self):
        """Transition to 'submit_documents' state."""
        """
        Opens a window to compose an email with the "Send to Bank" template loaded by default.
        """

        filtered_attachments = self.supplier_attachment_ids.filtered(lambda a: a.is_supplier_docs)
        attachment_ids = filtered_attachments.mapped('id') 

        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data._xmlid_lookup('purchase_new_states.email_template_send_to_bank2')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_ids': self.ids,
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
            'default_attachment_ids': [(6, 0, attachment_ids)],
        })

        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Proforma Invoice Sent to Bank')
        self.write({'state': 'submit_documents'})
        return {
            'name': _('Compose Email to Bank'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        
    def button_bank_reject_first(self):
        """Transition to 'document received' state."""
        self.write({'state': 'draft'})
        

    def button_bank_approved(self):
        """Transition to 'purchase' state."""
        self.write({'state': 'purchase'})
    
    def button_bank_reject(self):
        """Transition to 'document received' state."""
        self.write({'state': 'sent'})
        
        
    def button_bank_approved_rfq(self):
        """Transition to 'bank_approved' state."""
        self.write({'state': 'bank_approved'})

    def button_vendor_shipped(self):
        """Transition to 'vendor_shipped' state."""
        self.write({'state': 'vendor_shipped'})

    def button_custom_clearance(self):
        """Transition to 'custom_clearance' state."""
        self.write({'state': 'custom_clearance'})

    def button_arrived(self):
        """Transition to 'arrived' state."""
        self.write({'state': 'arrived', 'invoice_status' : 'to invoice'})
        

        
        