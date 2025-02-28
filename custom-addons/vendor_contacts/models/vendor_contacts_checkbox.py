from odoo import models, fields, api

class VendorContactsCheckbox(models.Model):
    _inherit = 'res.partner'

    is_vendor = fields.Boolean(string="Is Vendor")
    fayda_attachment = fields.Binary("Fayda Attachment", attachment=True)
    passport_attachment = fields.Binary("Passport Attachment", attachment=True)

    @api.onchange('fayda_attachment')
    def _onchange_fayda_attachment(self):
        """Update the Employee's Fayda Attachment when changed in Contact."""
        for record in self:
            employee = self.env['hr.employee'].search([('work_contact_id.id', '=', record.id.origin)], limit=1)
            if employee:
                employee.fayda_attachment = record.fayda_attachment
    
    @api.onchange('passport_attachment')
    def _onchange_passport_attachment(self):
        """Update the Employee's Passport Attachment when changed in Contact."""
        for record in self:
            employee = self.env['hr.employee'].search([('work_contact_id.id', '=', record.id.origin)], limit=1)
            if employee:
                employee.passport_attachment = record.passport_attachment
   

