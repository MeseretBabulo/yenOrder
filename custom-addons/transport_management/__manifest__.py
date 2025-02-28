# __manifest__.py
{
    'name': 'Transport Management',
    'version': '1.0',
    'summary': 'Manage Transportation for Purchase and Sales',
    'author': '',
    'depends': ['base', 'sale', 'purchase', 'account', 'mail', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/transport_group_rules.xml',
        'data/ir_sequence_data.xml',
        'data/vehicle_type.xml',
        # 'data/routes.xml',
        'views/transport_record_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        # 'views/vendor_bill_views..xml',
    ],
    'installable': True,
    'application': False,
}