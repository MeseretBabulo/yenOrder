{
    'name': 'Product Hold Management',
    'version': '17.0.1.0.0',
    'category': 'Inventory/Sales',
    'summary': 'Manage product hold status',
    'description': """
        This module allows administrators to:
        * Put products on hold
        * Prevent sale of held products
        * Release held products
    """,
    'depends': ['base', 'product', 'sale_management'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/product_hold_management/static/src/css/product_hold.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 