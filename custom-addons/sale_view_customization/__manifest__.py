{
    'name': 'Sale View Customization',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Customizes sale order views',
    'description': """
        This module customizes the sale order views by:
        - Hiding the preview button
        - Hiding optional products tab
        - Hiding customer signature
        - Hiding add shipping button
    """,
    'depends': ['sale', 'delivery'],
    'data': [
        'views/sale_order_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 