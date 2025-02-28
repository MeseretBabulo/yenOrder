# -*- coding: utf-8 -*-
{
    'name': "Container Logic",
    'website': "",
    'Author': 'AG',
    'version': '0.1',
    'sequence': 1,
    'depends': ['sale','sale_management','sale_pdf_quote_builder'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/submenu.xml',
        'views/sale_order_line.xml',
        'views/sale_order_template.xml',
        'views/account_move_line_view.xml',
        'reports/container_report.xml',
        'reports/commercial_invoice.xml'
    ],
    'license': 'AGPL-3',
    'installable': True
}
