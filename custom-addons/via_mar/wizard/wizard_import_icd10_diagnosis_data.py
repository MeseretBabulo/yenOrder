# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
import psycopg2
# import simple_icd_10 as icd
# import icd10
# import time
# from memory_profiler import profile


class WizardImportICD10DiagnosisData(models.TransientModel):
    _name = 'wizard.import.icd10.diagnosis.data'
    _description = 'Import ICD10 Diagnosis Data'

    # @profile
    def import_icd10_diagnosis_data(self):
        # connection establishment
        conn = psycopg2.connect(
            database=self.env.cr.dbname
        )
        conn.autocommit = True
        cursor = conn.cursor()
        # print(code.block_description)
        # print(icd.get_description(data))

        sql = '''CREATE Temporary TABLE icd10_diagnosis_temp (code VARCHAR(1000),description VARCHAR(1000),is_imported boolean);'''
        cursor.execute(sql)
        sql3 = '''SELECT code FROM icd10_diagnosis_data'''
        cursor.execute(sql3)
        res = [row[0] for row in cursor.fetchall()]
        # for data in icd.get_all_codes(with_dots=True):
        #     code = icd.find(str(data))
        #     if code and str(code) not in res:
        #         # self.env.cr.execute("""delete from icd10_diagnosis_data""")
        #         sql2 = '''insert into icd10_diagnosis_temp(code, description, is_imported) VALUES(%s,%s,%s);'''
        #         record_to_insert = (str(data), icd.get_description(data), True)
        #         cursor.execute(sql2, record_to_insert)
        cursor.execute('''INSERT INTO icd10_diagnosis_data (code, description, is_imported) SELECT code, description, is_imported FROM icd10_diagnosis_temp''')
        conn.commit()
        conn.close()
        return True
