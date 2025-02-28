from odoo import fields, models, api


class ModelName(models.Model):
    _name = 'ks_project_task.specialist'

    name = fields.Char(string="Specialist")
