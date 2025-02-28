from odoo import api, fields, models
class UploadEmployee(models.Model):
    _inherit = 'hr.employee'

    fayda_attachment = fields.Binary(
        "Fayda Attachment",
        related='work_contact_id.fayda_attachment',
        store=True,  
        readonly=False 
    )

    passport_attachment = fields.Binary(
        "Passport Attachment",
        related='work_contact_id.passport_attachment',
        store=True,  
        readonly=False 
    )

    tin_number = fields.Char(string='TIN Number')

    @api.onchange('fayda_attachment')
    def _onchange_fayda_attachment(self):
        for record in self:
            if record.work_contact_id:
                record.work_contact_id.fayda_attachment = record.fayda_attachment

    @api.onchange('passport_attachment')
    def _onchange_passport_attachment(self):
        for record in self:
            if record.work_contact_id:
                record.work_contact_id.passport_attachment = record.passport_attachment

from odoo import models, fields, api

class VendorContactsPrivateInformation(models.Model):
    _inherit = 'res.partner'

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
    
    
