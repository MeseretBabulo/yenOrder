from odoo import fields, models


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    modifier_1 = fields.Many2one('ks_project_task.modifiers_one', string='Modifier 1')
    modifier_2 = fields.Many2one('ks_project_task.modifiers_two', string='Modifier 2')
    modifier_3 = fields.Many2one('ks_project_task.modifiers_three', string='Modifier 3')
    modifier_4 = fields.Many2one('ks_project_task.modifiers_four', string='Modifier 4')
    procedure_code = fields.Many2one("ks_project_task.procedure_code", "Procedure Code")
    reasoncode = fields.Char('ReasonCode')
    call_type = fields.Char('Call type')
    mobile_login = fields.Char('Mobile Login')
    resolution_code = fields.Char('Resolution code')
