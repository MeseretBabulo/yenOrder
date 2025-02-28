# -*- coding: utf-8 -*-
{
    'name': "Sales Export",
    'website': "",
    'category': 'Purchase',
    'Author': '',
    'version': '17.0.1.0.0',
    'sequence': 1,
    'depends': ['sale','stock','product'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/sale_order_views.xml',
        'views/stock_quant_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}

