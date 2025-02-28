# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, exceptions, api, tools, _
import xlrd
import tempfile
import base64
from odoo.exceptions import UserError, ValidationError


class LeadImport(models.TransientModel):
    _name = 'lead.import'
    _description = 'Import Lead'

    file_to_import = fields.Binary('File To Import', required=True)
    file_name = fields.Char('File name', required=True)

    def action_import(self):
        """Load Product Master data from the Excel file."""
        try:
            lead_obj = self.env['crm.lead']
            if not self.file_to_import:
                raise exceptions.Warning(_("You need to select a file!"))
            binary_data = self.file_to_import
            file_name = self.file_name
            f = tempfile.NamedTemporaryFile(mode='wb+', delete=False)
            filename = '/tmp/' + str(file_name)
            with open(filename, 'wb') as f:
                x = base64.b64decode(binary_data)
                f.write(x)
            workbook = xlrd.open_workbook(filename)
            num_rows = workbook.sheet_by_index(0).nrows - 1
            curr_row = 0
            vals = {}
            while curr_row < num_rows:
                curr_row += 1
                if curr_row > 0:
                    vals = {}
                    lead_id = False
                    partner_id = False
                    row = workbook.sheet_by_index(0).row(curr_row)
                    if row[0] and row[0].value:
                        vals.update({'name': str(row[0].value).strip()})
                    if row[1] and row[1].value:
                        vals.update({'contact_name': str(row[1].value).strip()})
                    if row[2] and row[2].value:
                        vals.update({'firstname': str(row[2].value).strip()})
                    if row[3] and row[3].value:
                        vals.update({'lastname': str(row[3].value).strip()})
                    if row[4] and row[4].value:
                        vals.update({'gender': str(row[4].value).strip()})
                    if row[5] and row[5].value:
                        vals.update({'phone': str(row[5].value).strip()})
                    if row[6] and row[6].value:
                        vals.update({'primary_language': str(row[6].value).strip()})
                    if row[7] and row[7].value:
                        vals.update({'email_from': str(row[7].value).strip()})
                    vals.update({'type': 'lead'})
                    if vals:
                        lead_obj.create(vals)
        except (OSError, Exception) as err:
            raise ValidationError(_("%s", tools.ustr(err)))
        return True
