# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

import requests
import os
import zipfile
import io
from odoo import fields, models, tools, _
from odoo.exceptions import UserError

class OpenFDADrugData(models.Model):
    _name = "open.fda.drug.data"
    _description = "Open FDA Drug Data"

    name = fields.Char(string="Drug Name",
                            copy=False)
    product_type = fields.Char(string="Product Type",
                            copy=False)
    product_ndc = fields.Char(string="NDC Code",
                            copy=False)
    brand_name = fields.Char(string="Brand",
                            copy=False)
    is_imported = fields.Boolean(string="Imported?",
                            copy=False)

    def action_download_ndc_drug_data(self):
        try:
            api_url_page = "https://api.fda.gov/download.json"
            response_page = requests.get(api_url_page)
            ndc_dir_path = '/tmp/ndc_data_file'
            if response_page.json().get('results'):
                if response_page.json().get('results').get('drug') and \
                        response_page.json().get('results').get('drug').get('ndc') and \
                        response_page.json().get('results').get('drug').get('ndc').get('partitions') and \
                        response_page.json().get('results').get('drug').get('ndc').get('partitions')[0] and \
                        response_page.json().get('results').get('drug').get('ndc').get('partitions')[0].get('file'):
                    if not os.path.exists(ndc_dir_path):
                        os.makedirs(ndc_dir_path)
                    bkp_file = requests.get(
                        response_page.json().get('results').get('drug').get('ndc').get('partitions')[0].get('file'),
                        stream=True)
                    zip_file_content = zipfile.ZipFile(io.BytesIO(bkp_file.content))
                    zip_file_content.extractall('/tmp/ndc_data_file')
        except (OSError, Exception) as err:
            raise UserError(_(tools.ustr(err)))
