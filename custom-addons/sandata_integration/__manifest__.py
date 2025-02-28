# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


{
    'name': 'SANDATA Integration a',
    'version': '1.0.1',
    'category': '',
    'summary': '',
    'author': 'Bista Solutions',
    'license': 'AGPL-3',
    'description': 'SANDATA Integrations.',
    'depends': [
       'web','project', 'analytic', 'bista_timesheet_attendance', 'hr', 'via_crm', 'via_sales_enhancement', 'hr_timesheet'
    ],
    'data': [
        'security/sandata_security.xml',
        'security/ir.model.access.csv',
        'wizard/service_note_wizard_view.xml',
        'wizard/wizard_create_attendance_update_view.xml',
        'wizard/delay_reason_view.xml',
        'wizard/wizard_create_attendance_view.xml',
        'views/sandata_view.xml',
        'views/hr_employee_view.xml',
        # 'views/res_partner_view.xml',
        'views/project_task_view.xml'
    ],
    'demo': [],
    'test': [],
    'qweb': [],
    'assets': {
        'web.assets_common': [
            'sandata_integration/static/src/css/custom.css',
        ],
    },
    'installable': True,
    'auto_install': False,
}
