# -*- coding: utf-8 -*-
{
    'name': "Purchase Bank Tracking State",
    'website': "",
    'category': 'Purchase',
    'Author': '',
    'version': '17.0.1.0.0',
    'sequence': 1,
    'depends': ['purchase','purchase_stock','vendor_contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'data/mail_template_data_inherit.xml',
        'views/views.xml',
        'views/orderline_country_view.xml',

    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}