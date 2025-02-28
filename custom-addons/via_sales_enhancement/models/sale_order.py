# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


import math
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    documents_count = fields.Integer(compute='_compute_documents_count',
                                    string="Documents Count")

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        mail_activity_obj = self.env['mail.activity']
        analytic_account_obj = self.env['account.analytic.account']
        if res and self.env.company.via_company_type == 'nj':
            model_id = self.env['ir.model'].search([('model', '=', 'sale.order')],
                limit=1)
            if model_id:
                mail_activity_id = mail_activity_obj.create({
                                        'res_name': res.name,
                                        'res_model': 'sale.order',
                                        'res_id': res.id,
                                        'summary': "Upload Monitoring Tool document for %s"%(res.name),
                                        'res_model_id': model_id.id,
                                        'activity_type_id': self.env.ref('via_sales_enhancement.mail_sale_order_upload_activity_data').id,
                                        'user_id': res.user_id and res.user_id.id
                                        })
            if res.partner_id and not res.partner_id.analytic_account_id:
                analytic_account_id = analytic_account_obj.search([('partner_id', '=', res.partner_id.id),
                                            ('company_id', '=', self.env.company.id)],
                                            limit=1)
                if analytic_account_id:
                    res.partner_id.analytic_account_id = analytic_account_id.id
                    res.analytic_account_id = analytic_account_id.id
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        analytic_account_obj = self.env['account.analytic.account']
        super(SaleOrder, self).onchange_partner_id()
        if self.env.company.default_partner_inv_add_id:
            self.partner_invoice_id = self.env.company.default_partner_inv_add_id.id
        if self.env.company.via_company_type == 'nj':
            if self.partner_id:
                if self.partner_id.analytic_account_id:
                    self.analytic_account_id = self.partner_id.analytic_account_id.id
                else:
                    analytic_account_id = analytic_account_obj.search([('partner_id', '=', self.partner_id.id),
                                                ('company_id', '=', self.env.company.id)],
                                                limit=1)
                    if analytic_account_id:
                        self.partner_id.analytic_account_id = analytic_account_id.id
                        self.analytic_account_id = analytic_account_id.id
                    else:
                        self.analytic_account_id = False
            else:
                self.analytic_account_id = False

    def _prepare_analytic_account_data(self, prefix):
        res = super(SaleOrder, self)._prepare_analytic_account_data(prefix)
        for sale_order in self:
            if self.env.company.via_company_type == 'nj':
                res.update({
                            'name': str((sale_order.partner_id.ma_number + ' - ') or '') + str((sale_order.partner_id.name) or '')
                            })
        return res

    def _compute_documents_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        for sale_order in self:

            sale_order.documents_count = self.env['documents.document'].search_count([
                                ('res_model', '=', 'sale.order'),
                                ('res_id', '=', sale_order.id),
                                ('type', '!=', 'empty'),
                                ('company_id', '=', self.env.company.id)
                                ])

    def view_sale_order_docs(self):
        doc_obj = self.env['documents.document']
        for sale_order in self:
            document_ids = doc_obj.search([
                                ('res_model', '=', 'sale.order'),
                                ('res_id', '=', sale_order.id),
                                ('type', '!=', 'empty'),
                                ('company_id', '=', self.env.company.id)
                                ])
            if document_ids:
                kanban_view_id = self.env.ref('documents.document_view_kanban').id
                return {
                        'name': _('Sale Documents'),
                        'view_type': 'kanban',
                        'view_mode': 'kanban,tree',
                        'res_model': 'documents.document',
                        'views': [
                                    (kanban_view_id, 'kanban'),
                                    (self.env.ref('documents.documents_view_list').id,'tree')
                                ],
                        'view_id': kanban_view_id,
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', document_ids.ids)],
                        }
        return True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        product_id = self.env['product.product'].browse(vals.get('product_id'))
        sale_order_id = self.env['sale.order'].browse(vals.get('order_id'))
        if product_id and product_id.is_special_service and sale_order_id:
            if request.httprequest.cookies.get('cids'):
                cid = request.httprequest.cookies.get('cids').split(',')
                company_id = self.env['res.company'].browse(int(cid[0]))
            else:
                company_id = self.env.user.company_id if self.env.user and self.env.user.company_id else False
            if company_id.via_company_type == 'pa':
                special_service_counts = self.search_count([('product_id', '=', product_id.id),
                                                            ('order_id', '!=', sale_order_id.id),
                                                            ('order_id.partner_id', '=', sale_order_id.partner_id.id),
                                                            ('company_id', '=', self.env.company.id)])
                # if special_service_counts > 0:
                #     raise ValidationError(_("Can Not Create order with a Same Partner and product."))
            else:
                pass
        return super(SaleOrderLine, self).create(vals)

    # @api.depends('analytic_line_ids.project_id', 'project_id.pricing_type')
    @api.depends('analytic_line_ids.project_id')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        lines_by_timesheet = self.filtered(lambda sol: sol.qty_delivered_method == 'timesheet')
        domain = lines_by_timesheet._timesheet_compute_delivered_quantity_domain()
        mapping = lines_by_timesheet.sudo()._get_delivered_quantity_by_analytic(domain)
        for line in lines_by_timesheet:
            line.qty_delivered = math.floor(mapping.get(line.id or line._origin.id, 0.0) * 100 / 25)

    def _timesheet_create_task_prepare_values(self, project):
        self.ensure_one()
        planned_hours = self._convert_qty_company_hours(self.company_id)
        sale_line_name_parts = self.name.split('\n')
        title = sale_line_name_parts[0] or self.product_id.name
        description = '<br/>'.join(sale_line_name_parts[1:])
        return {
            'name': title if project.sale_line_id else '%s: %s: %s' % (self.order_id.name or '', 'Task', title),
            'planned_hours': planned_hours,
            'partner_id': self.order_id.partner_id.id,
            'email_from': self.order_id.partner_id.email,
            'description': description,
            'project_id': project.id,
            'sale_line_id': self.id,
            'sale_order_id': self.order_id.id,
            'company_id': project.company_id.id,
            'planned_date_begin': project.date_start or False,
            'planned_date_end': project.date or False,
            'user_ids': False,  # force non assigned task, as created as sudo()
        }

    def _timesheet_create_project_prepare_values(self):
        res = super(SaleOrderLine, self)._timesheet_create_project_prepare_values()

        if self.order_id and self.order_id.team_id:
            res.update({
                        # 'team_id': self.order_id.team_id.id,
                        'team_id': self.product_id.project_template_id.team_id.id,
                        'program_type': self.product_id.project_template_id and self.product_id.project_template_id.program_type or '',
                        'date_start': self.order_id.opportunity_id.plan_start_date if self.order_id.opportunity_id and self.order_id.opportunity_id.plan_start_date else False,
                        'date': self.order_id.opportunity_id.plan_end_date if self.order_id.opportunity_id and self.order_id.opportunity_id.plan_end_date else False})
        return res
