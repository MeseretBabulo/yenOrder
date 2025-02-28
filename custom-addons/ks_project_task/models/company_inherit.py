from odoo import fields, models, api


class ModelName(models.Model):
    _inherit = 'res.company'

    ks_mpi = fields.Char('MPI', required=True)
