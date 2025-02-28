from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_published_snippet = fields.Boolean(
        string='Published in Snippet',
        default=False,
    )

    def action_snippet_publish(self):
        """Toggle the publication state."""
        for record in self:
            record.is_published_snippet = not record.is_published_snippet
