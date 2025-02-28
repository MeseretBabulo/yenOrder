# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'VIA Monitoring',
    'version': '1.0.1',
    'category': '',
    'summary': '',
    'author': 'Bista Solutions',
    'license': 'AGPL-3',
    'description': 'Monitoring',
    'depends': [
        'sale_management', 'project', 'survey', 'contacts'
    ],
    'data': [
        'security/mmt_security.xml',
        'security/ir.model.access.csv',
        'views/asset_question_answer.xml',
        'views/questions_view.xml',
        # 'views/sale_order_view.xml',
        'report/report.xml',
        'report/monitoring_report.xml'
    ],
    'assets': {
    },
    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': True,
}

