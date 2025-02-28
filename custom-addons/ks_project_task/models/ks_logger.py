from odoo import fields, models, api


class KsLogger(models.Model):
    _name = 'ks_project_task.ks_logger'

    name = fields.Char('Type')
    date = fields.Datetime('Date')
    update_data = fields.Boolean('Update data')
    response = fields.Char('Response')
    data_file = fields.Char('Data file')
