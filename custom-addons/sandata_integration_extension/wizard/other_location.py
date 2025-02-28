# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class OtherLocationWizard(models.TransientModel):
    _name = 'other.location.wizard'
    _description = 'wizard for show Isp Location'

    other_location = fields.Boolean('Other Location')
    partner_id = fields.Many2one('res.partner', string='Partner')
    child_locations = fields.Many2one('res.partner', string='Locations')
    so_line = fields.Many2one('sale.order.line',string='Sale Order Item')
    sale_line_id = fields.Many2one('sale.order.line', string="Service Order")
    task_id = fields.Many2one('project.task',string="Task Id")
    comment = fields.Text(string="Comment")

    def save_other_location(self):
        if self.task_id:
            # self.task_id.so_line_wizard = self.so_line.id
            # self.task_id.timesheet_ids.write({'so_line': self.so_line.id})
            # attendance_line_id = max(self.task_id.attendance_line_ids.mapped('id'))
            # attendance_line = self.task_id.attendance_line_ids.browse(attendance_line_id)
            # self.task_id.so_line_wizard = self.so_line.id
            self.task_id.child_line_location_wiz = self.child_locations.id
            self.task_id.comment = self.comment
            # attendance_line.child_line_location = self.child_locations.id

    # def save_other_location(self):
    #     dict_data = self.env.context.get('kwargs')
    #     dict_data.update({'so_line': self.so_line.id})
    #     return self.env['project.task'].with_context(from_other_location=True).timesheet_sign_in(dict_data)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            return {'domain': {'child_locations': [('parent_id', '=', self.partner_id.id)]}}
        else:
            return {'domain': {'child_locations': []}}

    @api.onchange('sale_line_id')
    def onchange_sale_line_id(self):
        if self.sale_line_id:
            sale_order_id = self.sale_line_id.order_id.id
            related_sale_order_lines = self.env['sale.order.line'].search([('order_id', '=', sale_order_id)])
            # Filtering the Sale Order Lines to show only those related to the selected Sale Order Line
            filtered_sale_order_lines = related_sale_order_lines.filtered(
                lambda line: line.order_id.id == sale_order_id)
            return {'domain': {'so_line': [('id', 'in', filtered_sale_order_lines.ids)]}}
        else:
            return {'domain': {'so_line': []}}

