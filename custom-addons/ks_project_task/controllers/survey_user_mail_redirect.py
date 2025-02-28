import odoo.http as http

from odoo.http import request
from odoo.tools.misc import get_lang
from werkzeug.urls import url_encode


class SurveyController(http.Controller):

    @http.route('/survey/redirect/', type='http', auth="public")
    def survey_order_redirect(self, id, **kwargs):
        order = request.env['survey.user_input'].sudo().search([('id', '=', int(id))])
        return request.redirect('/web#id=%d&view_type=form&model=%s' % (order.id, order._name))
