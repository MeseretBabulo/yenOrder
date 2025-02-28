from odoo import fields, models, api


class ModifiersOne(models.Model):
    _name = 'ks_project_task.modifiers_one'
    _rec_name = 'modifier_1'

    modifier_1 = fields.Char("Modifier 1")


class ModifiersTwo(models.Model):
    _name = 'ks_project_task.modifiers_two'
    _rec_name = 'modifier_2'

    modifier_2 = fields.Char("Modifier 2")


class ModifiersThree(models.Model):
    _name = 'ks_project_task.modifiers_three'
    _rec_name = 'modifier_3'

    modifier_3 = fields.Char("Modifier 3")


class ModifiersFour(models.Model):
    _name = 'ks_project_task.modifiers_four'
    _rec_name = 'modifier_4'

    modifier_4 = fields.Char("Modifier 4")

