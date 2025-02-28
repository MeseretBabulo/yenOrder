# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

import logging
import json
from odoo import fields, models, api,tools, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from socket import gaierror, timeout
import requests
import psycopg2

_logger = logging.getLogger(__name__)


class WizardImportOpenFDADrugData(models.TransientModel):
    _name = 'wizard.import.open.fda.drug.data'
    _description = 'Import Open FDA Drug Data'

    disclaimer = fields.Text(string='Disclaimer')
    terms = fields.Html(string='Terms')
    license = fields.Html(string="License")
    last_updated = fields.Char(string="Last Update")

    @api.model
    def default_get(self, fields):
        res = super(WizardImportOpenFDADrugData, self).default_get(fields)
        try:
            # api_url_page = "https://api.fda.gov/drug/ndc.json?search=finished:true&limit=1"
            # response_page = requests.get(api_url_page)
            # pdf_path = get_module_resource('via_mar', 'drug_data', 'drug-ndc-0001-of-0001.json')
            pdf_path = '/tmp/ndc_data_file/drug-ndc-0001-of-0001.json'
            if pdf_path:
                f = open(pdf_path, "r")
                data = json.loads(f.read())
            # if 'meta' in response_page.json().keys():
                if 'meta' in data.keys():
                    if 'disclaimer' in fields:
                        # res['disclaimer'] = response_page.json()['meta']['disclaimer']
                        res['disclaimer'] = data['meta']['disclaimer']
                    if 'terms' in fields:
                        # res['terms'] = response_page.json()['meta']['terms']
                        res['terms'] = "<a href='" +data['meta']['terms']+ "'>"+ data['meta']['terms'] + "</a>"
                    if 'license' in fields:
                        # res['license'] = response_page.json()['meta']['license']
                        res['license'] = "<a href='" + data['meta']['license']+ "'>"+ data['meta']['license'] + "</a>"
                    if 'last_updated' in fields:
                        # res['last_updated'] = response_page.json()['meta']['last_updated']
                        res['last_updated'] = data['meta']['last_updated']
                f.close()
            else:
                raise ValidationError(_('File Not Found'))
        except (OSError, Exception) as err:
            # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
            raise UserError(_(tools.ustr(err)))
        return res

    def import_open_fda_drug_data(self):
        # connection establishment
        try:
            import json
            conn = psycopg2.connect(
                database=self.env.cr.dbname
            )
            conn.autocommit = True
            cursor = conn.cursor()
            sql = '''CREATE Temporary TABLE open_fda_temp (generic_name VARCHAR(1000), product_ndc VARCHAR(1000), product_type VARCHAR(1000), brand_name VARCHAR(1000), is_imported boolean);'''
            cursor.execute(sql)
            # self.env.cr.execute("""delete from open_fda_drug_data""")
            sql3 = '''SELECT product_ndc FROM open_fda_drug_data'''
            cursor.execute(sql3)
            res = [row[0] for row in cursor.fetchall()]
            pdf_path = '/tmp/ndc_data_file/drug-ndc-0001-of-0001.json'
            if pdf_path:
                f = open(pdf_path, "r")
                data = json.loads(f.read())
                for each_rec in data['results']:
                    if each_rec.get('product_ndc') not in res and each_rec.get('finished'):
                        drug_data_insert = '''
                                            INSERT
                                                INTO
                                            open_fda_drug_data
                                                (name,product_type,product_ndc,brand_name,is_imported)
                                            VALUES
                                                (%s,%s,%s,%s,%s);'''
                        record_to_insert = (
                        each_rec.get('generic_name'), each_rec['product_type'],each_rec['product_ndc'], each_rec.get('brand_name'),
                        True)
                        cursor.execute(drug_data_insert, record_to_insert)
                conn.commit()
                conn.close()
                f.close()
            else:
                raise ValidationError(_('File Not Found'))
        except IOError as err:
            raise ValidationError(_(tools.ustr(err)))
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint")
            raise ValidationError("Connection Error: " + _("Could not establish the connection to the API."))
        except (OSError, Exception) as err:
            # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
            raise UserError(_(tools.ustr(err)))
        except (gaierror, timeout,) as e:
            raise UserError(_("No response received. Check server information.\n %s", tools.ustr(e)))
        return True
