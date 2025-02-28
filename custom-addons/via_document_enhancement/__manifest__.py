# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


{
    'name': 'VIA Document Enhancement',
    'version': '17.0.1.2.0',
    'category': '',
    'summary': '',
    'author': 'Bista Solutions',
    'license': 'AGPL-3',
    'description': 'Document Enhancement',
    'depends': [
        'via_sales_enhancement', 'documents'
    ],
    'data': [
        'security/documents_security.xml',
        'views/documents_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'via_document_enhancement/static/src/js/document_inspector.js',
        ],
    },
    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': True,
}

