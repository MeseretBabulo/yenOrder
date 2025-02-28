from odoo import http
from odoo.http import request

class SnippetController(http.Controller):
    @http.route('/snippet/products', type='json', auth='public', website=True)
    def get_published_products(self):
        products = request.env['product.template'].sudo().search([
            ('is_published_snippet', '=', True),
            ('website_published', '=', True)
        ])
        
        return {
            'products': [{
                'id': product.id,
                'name': product.name,
                'description': product.description_sale or '',
                'image_url': f'/web/image/product.template/{product.id}/image_1024',
                'public_url': f'/shop/product/{product.id}',
            } for product in products]
        }