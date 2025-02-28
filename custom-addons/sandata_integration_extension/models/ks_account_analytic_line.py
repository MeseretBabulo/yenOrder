from odoo import api, fields, models, _
from odoo.http import request
import werkzeug


class AccountAnalyticLineInherit(models.Model):
    _inherit = 'account.analytic.line'

    def open_service_note(self):
        survey_id = self.project_id.ks_survey
        url = werkzeug.urls.url_join(survey_id.get_base_url(), survey_id.get_start_url()) if survey_id else False
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
