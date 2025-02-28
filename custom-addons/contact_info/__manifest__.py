{
    'name': 'Contact Info',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Add Contact Info button to show OdooBot messages',
    'description': """
        This module adds a Contact Info button in the Contacts configuration menu
        that shows messages from OdooBot.
    """,
    'depends': ['base', 'contacts', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/contact_info_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 