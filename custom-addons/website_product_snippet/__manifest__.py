{
    'name': 'Website Product Snippet',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Custom product snippet with hover effects',
    'depends': ['website', 'product'],
    'data': [
        'views/product.xml',
        'views/snippet.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_product_snippet/static/src/js/snippet.js',
            'website_product_snippet/static/src/scss/snippet.scss',
        ],
    },
    'installable': True,
    'application': False,
}