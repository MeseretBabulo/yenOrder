import base64
from odoo import fields, models


class KsProgressNotes(models.Model):
    _name = "progress.notes"
    _description = "Progress Notes"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    survey_id = fields.Many2one('survey.survey', string="Survey Id", tracking=True)
    start_date = fields.Datetime(string='Start Date', tracking=True)
    end_date = fields.Datetime(string='End Date', tracking=True)
    progress_towards_outcome = fields.Text(string="Progress Towards Outcome")
    comments_recommendations = fields.Text(string="Comments/Recommendations")
    is_generate = fields.Boolean(string="Is Generate", default=False)
    document_preview = fields.Binary(string="Document Preview", tracking=True)

    def action_download_answer_report(self):
        self.is_generate = True
        report_template_pdf = self.env.ref('ks_project_task.action_answer_report')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_pdf[0])
        ir_values = {
            'name': "Clinical Report",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % data_id.id,
            'target': 'self',
        }

    def action_generate_answer_report(self):
        report_template_pdf = self.env.ref('ks_project_task.action_answer_report')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_pdf[0])
        ir_values = {
            'name': "ID Card",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        self.document_preview = data_id.datas
        return True

