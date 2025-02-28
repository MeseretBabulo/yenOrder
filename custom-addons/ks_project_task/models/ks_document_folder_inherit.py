from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DocumentFolderInherit(models.Model):
    _inherit = 'documents.folder'

    medical_docs = fields.Boolean('Medical Folder')
    folder_type = fields.Selection([
                            ('res_admin', 'Res-Admin'),
                            ('ihcs_admin', 'Ihcs-Admin'),
                            ('pds_admin', 'Pds-Admin'),
                            ('accounting', 'Accounting'),
                            ('cst_folder', 'C&T')],
                            string="Folder Type")

    def write(self, vals):
        res = super(DocumentFolderInherit, self).write(vals)
        medical_folder_count = self.env['documents.folder'].search_count([('medical_docs', '=', True)])
        if medical_folder_count > 1:
            raise ValidationError(_("Already another medical folder is selected first "
                                  "deselect that then choose any new one."))
        return res

