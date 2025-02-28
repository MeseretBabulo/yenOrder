# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


{
    'name': 'VIA Sales Enhancement',
    'version': '1.0.1',
    'category': '',
    'summary': '',
    'author': 'Bista Solutions',
    'license': 'AGPL-3',
    'description': 'Sale Enhancement',
    'depends': [
        'base', 'analytic', 'account', 'sale_management', 'mail', 'via_crm', 'product', 'project', 'hr', 'sale_project',
        'hr_timesheet', 'bista_timesheet_attendance', 'documents', 'sale_project', 'industry_fsm', 'sign'
    ],
    'data': [
        'security/project_security.xml',
        'security/sale_security.xml',
        'security/service_note_security.xml',
        'security/ir.model.access.csv',
        'data/documents_sale_order_data.xml',
        'data/mail_activity_type_data.xml',
        'views/product_form_view.xml',
        'views/via_service_note_survey_view.xml',
        'views/via_service_note_view.xml',
        'views/via_attendance_view.xml',
        # 'views/partner_view.xml',
        'views/res_company_view.xml',
        'views/project_view.xml',
        'views/project_task_views.xml',
        'views/sale_order_view.xml',
        'views/via_error_code_view.xml',
        'views/document_view.xml',
        'views/hr_employee_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'via_sales_enhancement/static/src/js/document_inspector.js',
        ],
    },
    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': True,
}

