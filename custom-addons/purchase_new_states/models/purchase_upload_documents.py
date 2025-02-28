from odoo import models, fields, _

class PurchaseAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'
    is_supplier_docs = fields.Boolean(string="Supplier Docs",default=False)

    

class PurchaseUploadWizard(models.TransientModel):
    _name = 'purchase.uploadwizard.wizard'
    _description = 'Upload Supplier Documents'

    # file_name = fields.Char(string="File Name", required=True)
    # file_attachment = fields.Binary(string="Attachment", required=True)
    attachment_ids = fields.One2many(
        'purchase.uploadwizard.attachment',
        'wizard_id',
        string="Attachments",
        required=True
    )

    def action_upload_files(self):
        """
        Save the uploaded files as attachments in the purchase order
        and update the state to `submit_documents`.
        """
        # Retrieve the active purchase order ID from the context
        active_id = self.env.context.get('active_id')
        if not active_id:
            raise ValueError(_("No active purchase order found to attach the files."))

        # Get the purchase order record
        purchase_order = self.env['purchase.order'].browse(active_id)

        # Loop through the attachments and create them in `ir.attachment`
        for attachment in self.attachment_ids:
            self.env['ir.attachment'].create({
                'name': attachment.file_name,          # Name of the file
                'datas': attachment.file_attachment,  # Binary data of the file
                'res_model': 'purchase.order',        # Model to which the attachment belongs
                'res_id': purchase_order.id,          # ID of the purchase order
                'type': 'binary',
                'is_supplier_docs':True                     # Type of attachment (binary file)
            })

        # Update the state of the purchase order to `submit_documents`
        purchase_order.write({'state': 'docs_received'})

        # Close the wizard and optionally show a success message
        return {
            'type': 'ir.actions.act_window_close',  # This closes the wizard
        }

    # def action_upload_file(self):
    #     """
    #     Save the uploaded file as an attachment in the purchase order.
    #     """
    #     # Retrieve the active purchase order ID from the context
    #     active_id = self.env.context.get('active_id')
    #     if not active_id:
    #         raise ValueError(_("No active purchase order found to attach the file."))

    #     # Get the purchase order record
    #     purchase_order = self.env['purchase.order'].browse(active_id)

    #     # Create the attachment in the `ir.attachment` model
    #     self.env['ir.attachment'].create({
    #         'name': self.file_name,          # Name of the file
    #         'datas': self.file_attachment,  # Binary data of the file
    #         'res_model': 'purchase.order',  # Model to which the attachment belongs
    #         'res_id': purchase_order.id,    # ID of the purchase order
    #         'type': 'binary',               # Type of attachment (binary file)
    #     })

    #     # Optionally, show a success message
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': _('Success!'),
    #             'message': _('Supplier document has been uploaded successfully.'),
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }
class PurchaseUploadAttachment(models.TransientModel):
        _name = 'purchase.uploadwizard.attachment'
        _description = 'Attachments for Purchase Order Upload Wizard'

        wizard_id = fields.Many2one(
            'purchase.uploadwizard.wizard',
            string="Wizard",
            required=True,
            ondelete='cascade'
        )
        file_name = fields.Char(string="File Name", required=True)
        file_attachment = fields.Binary(string="Attachment", required=True)
