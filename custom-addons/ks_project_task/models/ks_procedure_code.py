from odoo import fields, models


class ProcedureCode(models.Model):
    _name = 'ks_project_task.procedure_code'
    _rec_name = 'name'

    name = fields.Char("Procedure Code", required=True)

