# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


{
    'name': 'VIA MAR',
    'version': '17.0.1.2.0',
    'category': 'Miscellaneous',
    'summary': '',
    'author': 'Bista Solutions',
    'license': 'AGPL-3',
    'description': 'Medical Administration Record',
    'depends': [
       'sale_management', 'via_crm', 'uom'
    ],
    'external_dependencies': {
        'python3': ['simple_icd_10'],
    },
    'data': [
        'security/mar_security.xml',
        'security/ir.model.access.csv',
        'views/root_menu.xml',
        'views/via_medical_admin_record_view.xml',
        'data/drug_schedule_action.xml',
        'wizard/wizard_import_icd10_diagnosis_data_view.xml',
        'wizard/wizard_import_open_fda_drug_data_view.xml',
        'wizard/wizard_drug_dose_schedule_view.xml',
        'wizard/wizard_residential_views.xml',
        'views/icd10_diagnosis_data_view.xml',
        'views/open_fda_drug_data_view.xml',
        'views/drug_initials_view.xml',
        'views/res_partner_view.xml',
        'views/drug_doses_schedule_view.xml',
        'views/residential_view.xml',
        'views/menus.xml',
        'report/report.xml',
        'report/medical_admin_record_report.xml',
        'report/medication_profile_report.xml',
        'report/residential_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'via_mar/static/src/js/drug_popover.js',
        ],
        'web.assets_qweb': [
            'via_mar/static/src/xml/*.xml',
        ],
    },
    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': True,
}
