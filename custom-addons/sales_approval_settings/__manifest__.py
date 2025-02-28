# -*- coding: utf-8 -*-
{
    'name': "Sales Approval Settingss",
    'website': "",
    'Author': 'A G',
    'version': '1.0',
    'sequence': 1,
    'depends': ['sale_management',],
    'data': [
        'security/groups.xml',
        'views/views.xml',
        'views/submenu.xml',
        'security/ir.model.access.csv'
        # 'views/actions_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}