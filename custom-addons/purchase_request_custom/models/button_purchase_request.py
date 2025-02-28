from odoo import api, fields, models ,_
from odoo.exceptions import UserError
class PurchaseRequest(models.Model):
    _inherit = "purchase.request"
        
    def button_to_approve(self):
        self.to_approve_allowed_check()
        approval_limit = self.env['res.config.settings'].sudo().search([],limit=1)
        if float(self.estimated_cost) > float(approval_limit.po_double_validation_amount): 
            raise UserError(
                _(
                    "You can't request an amount which is greater than the amount that is allowed to you.\n"
                    " Notify the admin to increase this amount."
                )
                
            )
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        for record in self:
            record.activity_schedule(
                activity_type_id=activity_type.id,
                summary="New Purchase Request Created",
                note="Click the link to explore the new created Purchase Request",
                user_id=self.assigned_to.id  # Specify the user to notify
            )
        return self.write({"state": "to_approve"})