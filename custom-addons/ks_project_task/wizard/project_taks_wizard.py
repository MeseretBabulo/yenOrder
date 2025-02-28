# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CreateProjectTaskWizard(models.TransientModel):
    _name = 'create.project.task.wizard'

    # name = fields.Char(string='Name')
    name = fields.Char(string='Reason for appointment')
    medical_facilities = fields.Many2one('res.partner', string='Medical facility', domain="[('is_company', '=', True)]")
    specialist = fields.Many2one('ks_project_task.specialist', string="specialist")
    chose_medical_form_id = fields.Many2one('documents.document', string="Medical form")
    chose_medical_form_ids = fields.Many2many('documents.document', string="Medical form", compute="_compute_chose_medical_form_ids")
    project_id = fields.Many2one("project.project", string='Project')
    physician_id = fields.Many2one("res.partner", string='Physician', domain="[('id', 'in', physician_ids)]")
    planned_date_begin = fields.Datetime("Start date")
    planned_date_end = fields.Datetime("End date")
    physician_ids = fields.Many2many('res.partner', compute='_compute_physician_ids', store=False)

    @api.depends('project_id')
    def _compute_chose_medical_form_ids(self):
        medical_folder = self.env['documents.folder'].search([('medical_docs', '=', True)]).id
        document_ids = self.env['documents.document'].search([('folder_id', '=', medical_folder)]).ids
        if document_ids:
            self.chose_medical_form_ids = [(6, 0, document_ids)]
        else:
            self.chose_medical_form_ids = [(6, 0, [])]

    def create_project_task(self):
        if not self.project_id:
            raise UserError(_("Please create task from project."))
        vals = {
            "name": _('Appointment %s') % (self.physician_id.name),
            "physician_id": self.physician_id.id,
            "planned_date_begin": self.planned_date_begin,
            "planned_date_end": self.planned_date_end,
            "project_id": self.project_id.id,
            "reason_for_appointment": self.name,
            "medical_facilities": self.medical_facilities.id,
            "specialist": self.specialist.id,
            "medical_form": self.chose_medical_form_id.attachment_id.datas,
            "medical_form_name": self.chose_medical_form_id.attachment_id.name,
            "medical_appointment": True,
        }
        self.env['project.task'].create(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.depends('project_id')
    def _compute_physician_ids(self):
        for wizard in self:
            if wizard.project_id:
                partner = wizard.project_id.partner_id
                if partner:
                    if partner.physician_ids:
                        wizard.physician_ids = partner.physician_ids
                    else:
                        wizard.physician_ids = False
                else:
                    wizard.physician_ids = False
            else:
                wizard.physician_ids = False


