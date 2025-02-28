# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import re
import phonenumbers


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def _get_default_source_platform(self):
        company_id = False
        if request.httprequest.cookies.get('cids'):
            cid = request.httprequest.cookies.get('cids').split(',')
            company_id = self.env['res.company'].browse(int(cid[0]))
        else:
            company_id = self.company_id
        if company_id and company_id.via_company_type == 'nj':
            return 'irecord'
        else:
            return 'hcsis'

    def _program_type_selection(self):
        company_id = False
        if request and request.httprequest.cookies.get('cids'):
            cid = request.httprequest.cookies.get('cids').split(',')
            company_id = self.env['res.company'].browse(int(cid[0]))
        else:
            company_id = self.env.user.company_id if self.env.user and self.env.user.company_id else False
        if company_id.via_company_type == 'pa':
            return [('support_brokering', 'Supports Brokering'),
                                    ('htts', 'Housing Transistion & Tenancy Sustaining Service'),
                                    ('ihcs', 'In-Home & Community Supports'),
                                    # ('ihcs_e', 'In-Home & Community Supports Enhanced'),
                                    ('ihcs_2_1', 'In-Home & Community Supports 2x1 (Two staff to One presenter)'),
                                    ('ihcs_e', 'In-Home & Community Supports Enhanced'),
                                    ('companion', 'Companion'),
                                    ('cps', 'Community Participation Support'),
                                    ('cpse', 'Community Participation Support Enhanced'),
                                    ('ci', 'Community Integration'),
                                    ('residential', 'Residential')]
        elif company_id.via_company_type == 'nj':
            return [('sp', 'SP (Support program)'),
                    ('ccp', 'CCP (Community Care Waiver)')]
        else:
            return [('', '')]

    via_company_type = fields.Selection(related='company_id.via_company_type',
                                string="Company Type", store=True)
    user_id = fields.Many2one(string="Lead")
    gender = fields.Selection([('female', 'Female'),
                               ('male', 'Male'),
                               ('non_binary_or_third_gender', 'Non-binary/third gender'),
                               ('prefer_to_self_describe', 'Prefer to self-describe'),
                               ('prefer_not_to_say', 'Prefer not to say'),
                               ('transgender', 'Transgender'),
                               ('cisgender', 'Cisgender'),
                               ('agender', 'Agender'),
                               ('genderqueer', 'Genderqueer'),
                               ('a_gender_not_listed', 'A gender not listed')], string="Gender")
    date_of_birth = fields.Date(string="Date of Birth")
    county_id = fields.Many2one('via.res.county',
                                string="County")
    mci_number = fields.Char(string="MCI Number",
                                    copy=False)
    # medicaid_number = fields.Char(string="MedicaID Number",
    #                                 copy=False)
    plan_start_date = fields.Date(string="Plan Start Date")
    plan_end_date = fields.Date(string="Plan End Date")
    status_of_plan = fields.Selection([
                            ('w', 'W'),
                            ('r', 'R'),
                            ('rv', 'RV'),
                            ('a', 'A'),
                            ('ai', 'AI'),
                            ('ri', 'RI'),
                            ('sr', 'SR')], string="Status Of Plan")
    # medicaid_date_in_service = fields.Date(string="MedicaID Date In Service")
    # medicaid_date_out_service = fields.Date(string="MedicaID Date Out Service")
    assessment_date = fields.Date('Assessment Date')
    is_legal_guardian = fields.Boolean(string="Legal Guardian")
    is_person_graduating = fields.Boolean(string="Person Graduating")
    plan_tier = fields.Selection([
                            ('A', 'A'),
                            ('Aa', 'Aa'),
                            ('B', 'B'),
                            ('Ba', 'Ba'),
                            ('C', 'C'),
                            ('Ca', 'Ca'),
                            ('D', 'D'),
                            ('Da', 'Da'),
                            ('E', 'E'),
                            ('Ea', 'Ea'),
                            ('Fa', 'Fa'),
    ],
                            string="Tier")
    source_platform = fields.Selection([
                            ('irecord', 'iRecord'),
                            ('hcsis', 'HCSIS')],
                            string="Source Platform",
                            copy=False, default=_get_default_source_platform)
    partner_relationship = fields.Selection([
                            ('self', 'Self'),
                            ('mother', 'Mother'),
                            ('father', 'Father'),
                            ('spouse', 'Spouse'),
                            ('son', 'Son'),
                            ('daughter', 'Daughter'),
                            ('friend', 'Friend'),
                            ('sibling', 'Sibling'),
                            ('relative', 'Relative'),
                            ('legal_guardian', 'Legal Guardian'),
                            ('other', 'Other')],
                            default='self',
                            string="Relationship to Presenter")
    partner_relative_id = fields.Many2one('res.partner',
                                    string="Representative")
    representative_firstname = fields.Char(string="Rep. First Name",
                                            tracking=1)
    representative_lastname = fields.Char(string="Rep. Last Name",
                                            tracking=1)
    representative_street = fields.Char(string="Street")
    representative_street2 = fields.Char(string="Street2")
    representative_city = fields.Char(string="City")
    representative_state_id = fields.Many2one('res.country.state',
                                    string="State")
    representative_zip = fields.Char(string="Zip")
    representative_country_id = fields.Many2one('res.country',
                                    string="Country")
    representative_email = fields.Char(string="Email")
    representative_phone = fields.Char(string="Phone")
    representative_mobile = fields.Char(string="Mobile")
    representative_comment = fields.Html(string="Comment",
                                        translate=True)
    firstname = fields.Char(string="First Name",
                            tracking=1,
                            copy=False, compute='_compute_firstname', readonly=False, store=True)
    lastname = fields.Char(string="Last Name",
                            tracking=1,
                            copy=False, compute='_compute_lastname', readonly=False, store=True)
    internal_unique_id_code = fields.Char(string="Internal Unique ID",
                            copy=False)
    ma_number = fields.Char(string="MA Number",
                            copy=False)
    goes_by = fields.Char(string="Goes by")
    program_type = fields.Selection(_program_type_selection,
                                string="Program Type")
    funding_source = fields.Selection([
                            ('pfds', 'PFDS'),
                            ('community_living', 'Community Living,'),
                            ('consolidated', 'Consolidated'),
                            ('base', 'Base'),
                            ('other', 'Other')],
                            string="Funding Source")
    distinguish_region = fields.Selection([
                            ('western', 'Western'),
                            ('central', 'Central'),
                            ('north_east', 'Northeast'),
                            ('south_east', 'Southeast')],
                            string="Region")
    status = fields.Selection([
                            ('pre_auth', 'Pre-Auth'),
                            ('authorized', 'Authorized'),
                            ('inactive', 'Inactive')],
                            string="Status")
    race = fields.Selection([('american_indian_native', 'American Indian/Alaskan Native'),
                             ('asian', 'Asian'),
                             ('black_american', 'Black/African American'),
                             ('native_other', 'Native Hawiian or Pacific Islander'),
                             ('white', 'White'),
                             ('other_race_ethnicity_or_origin', 'Some other race, ethnicity, or origin'),
                             ('prefer_to_self_describe', 'Prefer to self-describe'),
                             ('prefer_not_to_say', 'Prefer not to say')
                             ],
                            string="Race")
    ethnicity = fields.Selection([
                            ('not_hispanic', 'Not Hispanic'),
                            ('hispanic', 'Hispanic')],
                                string="Ethnicity")

    living_arrangement = fields.Selection([
                                        ('own_apartment', 'Own Apartment/House'),
                                        ('with_relative', 'Living with Relative'),
                                        ('with_parent', 'Living with Parent')],
                                        string="Living Arrangement")
    primary_language = fields.Selection([
                                        ('english', 'English'),
                                        ('spanish', 'Spanish'),
                                        ('american_sign', 'American Sign Language'),
                                        ('other', 'Other')],
                                        string="Primary Language")

    developmental_disability = fields.Selection([
                                ('autism', 'Autism'),
                                ('cerebral_palsy', 'Cerebral Palsy'),
                                ('other', 'Other')],
                                string="Developmental Disability")

    intellectual_disability = fields.Selection([
                                            ('mild', 'Mild'),
                                            ('moderate', 'Moderate'),
                                            ('profound', 'Profound'),
                                            ('severe', 'Severe'),
                                            ('unspecified', 'Unspecified')],
                                            string="Intellectual Disability")

    mobility = fields.Selection([
                                ('walks_on_own', 'Walks on own'),
                                ('walker_cane', 'Walker/crutches/cane'),
                                ('wheel_chair', 'Wheelchair'),
                                ('other', 'other')],
                                string="Mobility")
    commu_issue = fields.Selection([
                                ('yes', 'Yes'),
                                ('no', 'No')],
                                string="Communication Issue")
    outcome_phrase = fields.Html(string="Outcome Phrase")
    reason_for_outcome = fields.Text(string="Reason for Outcome")
    outcome_statement = fields.Text(string="Outcome Statement")
    actions_taken = fields.Text(string="Actions")
    progress_status = fields.Text(string="Progress")
    date_referral = fields.Date(string="Date Referral")
    referral_meeting_date = fields.Date(string="Referral Meeting Date")
    project_auth_date = fields.Date(string="Project Auth. Date")
    pre_auth_region = fields.Selection([
                            ('western', 'Western'),
                            ('central', 'Central'),
                            ('north_east', 'Northeast'),
                            ('south_east', 'Southeast')],
                            string="Pre-Auth Region")
    pre_auth_county_id = fields.Many2one('via.res.county',
                                string="Pre-Auth County")
    support_coordinator = fields.Char("Support Coordinator")
    # pre_auth_sc_user_id = fields.Many2one('res.users',
    #                             string="Pre-Auth Support Coordinator")
    sc_phone_no = fields.Char(string="Support Coordinator Phone#")
    pre_auth_notes = fields.Text(string="Pre-Auth Notes")
    projected_units = fields.Char(string="Projected Units")
    authorized_date = fields.Date(string="Authorized Date")
    stage_type = fields.Selection(related='stage_id.stage_type',
                                string="Stage Type")
    is_won_stage = fields.Boolean(related="stage_id.is_won", string="Is Won")
    payer = fields.Selection([('PAOLTL', 'PAOLTL'),
                                 ('PAODP', 'PAODP'),
                                 ('PAOMAP', 'PAOMAP'),
                                 ('PAABH', 'PAABH'),
                                 ('PAGHP', 'PAGHP'),
                                 ('PAHPP', 'PAHPP'),
                                 ('PAUHC', 'PAUHC'),
                                 ('PAGEIS', 'PAGEIS'),
                                 ('PAAHPH', 'PAAHPH'),
                                 ('PAKPH', 'PAKPH'),
                                 ('PAUPPH', 'PAUPPH'),
                                 ('PAUPMC', 'PAUPMC'),
                                 ('PAHW', 'PAHW'),
                                 ('PAACP', 'PAACP'),
                                 ('PAKF', 'PAKF'),
                                 ], string="Payer ID", required=True,
                                 copy=False)
    payer_program = fields.Selection([('OLTL', 'OLTL'),
                                 ('ODP', 'ODP'),
                                 ('OMAP', 'OMAP'),
                                 ('PHC', 'PHC'),
                                 ('CHC', 'CHC'),
                                 ], string="Payer Program", required=True,
                                 copy=False)
    won_stage_id = fields.Many2one('crm.stage', related="stage_id", store=True, tracking=0)
    isp_ids = fields.One2many('via.isp', 'crm_lead_id')
    sexual_orientation = fields.Selection([('straight_or_heterosexual', 'Straight/Heterosexual'),
                                           ('gay_or_Lesbian', 'Gay or Lesbian'),
                                           ('bisexual', 'Bisexual'),
                                           ('queer', 'Queer'),
                                           ('asexual', 'Asexual'),
                                           ('prefer_to_self_describe', 'Prefer to self-describe'),
                                           ('prefer_not_to_say', 'Prefer not to say'),
                                           ], string="Sexual Orientation", copy=False)
    religion = fields.Selection([('christian', 'Christian'),
                                 ('buddhist', 'Buddhist'),
                                 ('hindu', 'Hindu'),
                                 ('muslim', 'Muslim'),
                                 ('jewish', 'Jewish'),
                                 ('sikh', 'Sikh'),
                                 ('no_religion', 'No Religion'),
                                 ('prefer_not_to_say', 'Prefer not to say'),
                                 ('another', 'Another (specify)'),
                                 ], string="Religion", copy=False)
    is_hispanic = fields.Boolean(string="No, not of Hispanic, Latino/a/x, or Spanish origin")
    is_mexican = fields.Boolean(string="Yes, Mexican, Mexican American, Chicano/a/x")
    is_puerto_rican = fields.Boolean(string='Yes, Puerto Rican')
    is_cuban = fields.Boolean(string="Yes, Cuban")
    is_another_hispanic = fields.Boolean(string="Yes, Another Hispanic, Latino/a/x or Spanish origin")
    is_other_race = fields.Boolean(string="Some other race, ethnicity, or origin")
    is_self_describe = fields.Boolean(string="Prefer to self-describe")
    is_not_say = fields.Boolean(string="Prefer not to say")
    service_ids = fields.Many2many('product.product', 'product_crm_rel', "lead_id", "product_id",
                                   string="Service", domain="[('detailed_type', '=', 'service')]")
    partner_id = fields.Many2one(
        'res.partner', string='Person Supported', check_company=True, index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    # _sql_constraints = [
    #     ('internal_unique_id_code_uniq', 'unique (internal_unique_id_code)',
    #      'The Internal Unique ID of the Lead must be unique per company!')
    # ]

    @api.depends('partner_id.firstname')
    def _compute_firstname(self):
        for lead in self:
            # if lead.partner_id.firstname:
            lead.firstname = lead.partner_id.firstname

    @api.depends('partner_id.lastname')
    def _compute_lastname(self):
        for lead in self:
            # if lead.partner_id.lastname:
            lead.lastname = lead.partner_id.lastname

    def action_sale_quotations_new(self):
        if not self.partner_id:
            return self.env["ir.actions.actions"]._for_xml_id("sale_crm.crm_quotation_partner_action")
        else:
            self.with_context(active_id=self.id, from_crm=True)._handle_partner_assignment(self.partner_id.id)
            return self.action_new_quotation()

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.mci_number = ''
            self.ma_number = ''

    @api.constrains('mci_number', 'ma_number')
    def _check_mis_medicaid_numbers(self):
        for lead in self:
            ma_number_counts = self.search_count([('ma_number', '=', lead.ma_number),
                                                  '|', ('company_id', '=', self.env.company.id),
                                                  ('company_id', '=', False),
                                                  ('id', '!=', lead.id)])
            mci_numbers_counts = self.search_count([('mci_number', '=', lead.mci_number),
                                                    '|', ('company_id', '=', self.env.company.id),
                                                    ('company_id', '=', False),
                                                    ('id', '!=', lead.id)])
            if not lead.partner_id:
                if lead.mci_number and mci_numbers_counts > 0:
                    raise ValidationError(_("""MCI number should be unique."""))
                if lead.ma_number and ma_number_counts > 0:
                    raise ValidationError(_("""MA number should be unique."""))

    @api.constrains('phone')
    def check_phone_number(self):
        for lead in self:
            pass
            # if lead.country_id and lead.phone and len(lead.phone) != 14:
            #     raise ValidationError(_("""Phone number length should be 10."""))

    @api.depends('company_id')
    def _compute_user_company_ids(self):
        res = super(CrmLead, self)._compute_user_company_ids()
        for rec in self:
            if rec.company_id.via_company_type == 'nj':
                self.source_platform = 'irecord'
            else:
                self.source_platform = 'hcsis'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # OVERRIDE to add the 'available_partner_bank_ids' field dynamically inside the view.
        # TO BE REMOVED IN MASTER
        from lxml import etree
        import json
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        tree = etree.fromstring(res['arch'])
        if view_type == 'form':
            if request.httprequest.cookies.get('cids'):
                cid = request.httprequest.cookies.get('cids').split(',')
                company_id = self.env['res.company'].browse(int(cid[0]))
            else:
                company_id = self.company_id
            if 'ma_number' in res['fields']:
                node = tree.xpath("//field[@name='ma_number']")
                if company_id and company_id.via_company_type == 'nj':
                    node[0].set("required", "0")
                    modifiers = json.loads(node[0].get("modifiers"))
                    modifiers['required'] = False
                    node[0].set("modifiers", json.dumps(modifiers))
        res['arch'] = etree.tostring(tree, encoding='unicode')
        return res

    @api.model
    def create(self, vals):
        if vals.get('phone', False):
            formatter = phonenumbers.AsYouTypeFormatter("US")
            formated_phone_number = ''
            for each_letter in vals.get('phone'):
                formated_phone_number = formatter.input_digit(each_letter)
            if formated_phone_number:
                vals.update({'phone': formated_phone_number})
        if vals.get('partner_id', False):
            dict_updated = {}
            partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
            for field_name in ['gender', 'date_of_birth', 'mci_number',
                               'plan_start_date', 'plan_end_date', 'status_of_plan', 'assessment_date',
                               'plan_tier', 'is_person_graduating',
                               'is_legal_guardian', 'source_platform', 'partner_relationship',
                               'support_coordinator', 'ma_number', 'goes_by', 'program_type',
                               'funding_source', 'distinguish_region', 'status', 'race', 'ethnicity',
                               'living_arrangement', 'primary_language', 'developmental_disability',
                               'intellectual_disability', 'mobility', 'commu_issue', 'sexual_orientation',
                               'religion', 'is_hispanic', 'is_mexican', 'is_puerto_rican', 'is_cuban',
                               'is_another_hispanic', 'is_other_race', 'is_self_describe', 'is_not_say',
                               'outcome_phrase', 'reason_for_outcome', 'outcome_statement',
                               'actions_taken', 'progress_status', 'date_referral', 'referral_meeting_date',
                               'project_auth_date', 'pre_auth_region', 'sc_phone_no', 'pre_auth_notes',
                               'projected_units', 'authorized_date', 'payer_program', 'payer']:
                if field_name == 'plan_tier':
                    if partner_id.plan_tier and not partner_id.plan_tier.isnumeric():
                        dict_updated[field_name] = partner_id.plan_tier
                else:
                    if getattr(partner_id, field_name) not in [False, '']:
                        dict_updated[field_name] = getattr(partner_id, field_name)
            for field_name in ['county_id', 'pre_auth_county_id']:
                if getattr(partner_id, field_name).id not in [False, '']:
                    dict_updated[field_name] = getattr(partner_id, field_name).id
            for field_name in ['ma_number']:
                if getattr(partner_id, field_name) not in [False, '']:
                    dict_updated[field_name] = getattr(partner_id, field_name)
            if dict_updated:
                vals.update(dict_updated)
        res = super(CrmLead, self).create(vals)
        return res

    def write(self, vals):
        for crm_lead in self:
            formatter = phonenumbers.AsYouTypeFormatter("US")
            formated_phone_number = ''
            if vals.get('phone', False):
                for each_letter in vals.get('phone'):
                    formated_phone_number = formatter.input_digit(each_letter)
                if formated_phone_number:
                    vals.update({'phone': formated_phone_number})
        if vals.get('partner_id', False):
            dict_updated = {}
            partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
            for field_name in ['gender', 'date_of_birth', 'mci_number',
                               'plan_start_date', 'plan_end_date', 'status_of_plan', 'assessment_date',
                               'plan_tier', 'is_person_graduating',
                               'is_legal_guardian', 'source_platform', 'partner_relationship',
                               'support_coordinator', 'ma_number', 'goes_by', 'program_type',
                               'funding_source', 'distinguish_region', 'status', 'race', 'ethnicity',
                               'living_arrangement', 'primary_language', 'developmental_disability',
                               'intellectual_disability', 'mobility', 'commu_issue', 'sexual_orientation',
                               'religion', 'is_hispanic', 'is_mexican', 'is_puerto_rican', 'is_cuban',
                               'is_another_hispanic', 'is_other_race', 'is_self_describe', 'is_not_say',
                               'outcome_phrase', 'reason_for_outcome', 'outcome_statement',
                               'actions_taken', 'progress_status', 'date_referral', 'referral_meeting_date',
                               'project_auth_date', 'pre_auth_region', 'sc_phone_no', 'pre_auth_notes',
                               'projected_units', 'authorized_date', 'payer_program', 'payer']:
                if field_name == 'plan_tier':
                    if partner_id.plan_tier and not partner_id.plan_tier.isnumeric():
                        dict_updated[field_name] = partner_id.plan_tier
                else:
                    if getattr(partner_id, field_name) not in [False, '']:
                        dict_updated[field_name] = getattr(partner_id, field_name)
            for field_name in ['county_id', 'pre_auth_county_id']:
                if getattr(partner_id, field_name).id not in [False, '']:
                    dict_updated[field_name] = getattr(partner_id, field_name).id
            for field_name in ['ma_number']:
                if getattr(partner_id, field_name) not in [False, '']:
                    dict_updated[field_name] = getattr(partner_id, field_name)
            if dict_updated:
                vals.update(dict_updated)
        res = super(CrmLead, self).write(vals)
        return res

    def _handle_partner_assignment(self, force_partner_id=False, create_missing=True):
        """ Update customer (partner_id) of leads. Purpose is to set the same
        partner on most leads; either through a newly created partner either
        through a given partner_id.

        :param int force_partner_id: if set, update all leads to that customer;
        :param create_missing: for leads without customer, create a new one
          based on lead information;
        """
        for lead in self:
            if force_partner_id:
                crm_obj = self.env['crm.lead']
                partner_obj = self.env['res.partner'].sudo()
                if self.env.context and self.env.context.get('active_id'):
                    crm_id = crm_obj.browse(self.env.context.get('active_id'))
                    partner_id = partner_obj.browse(force_partner_id)
                    if self.env.context.get('from_crm') and crm_id:
                        dict_updated = {}
                        for field_name in ['gender', 'date_of_birth', 'mci_number',
                                           'plan_start_date', 'plan_end_date', 'status_of_plan', 'assessment_date',
                                           'plan_tier', 'is_person_graduating',
                                           'is_legal_guardian', 'source_platform', 'partner_relationship',
                                           'support_coordinator', 'ma_number', 'goes_by', 'program_type',
                                           'funding_source', 'distinguish_region', 'status', 'race', 'ethnicity',
                                           'living_arrangement', 'primary_language', 'developmental_disability',
                                           'intellectual_disability', 'mobility', 'commu_issue', 'sexual_orientation',
                                           'religion', 'is_hispanic', 'is_mexican', 'is_puerto_rican', 'is_cuban',
                                           'is_another_hispanic', 'is_other_race', 'is_self_describe', 'is_not_say',
                                           'outcome_phrase',  'reason_for_outcome', 'outcome_statement',
                                           'actions_taken', 'progress_status', 'date_referral', 'referral_meeting_date',
                                           'project_auth_date', 'pre_auth_region', 'sc_phone_no', 'pre_auth_notes',
                                           'projected_units', 'authorized_date', 'payer_program', 'payer']:
                            if field_name == 'plan_tier':
                                if lead.plan_tier and not lead.plan_tier.isnumeric():
                                    dict_updated[field_name] = lead.plan_tier
                            else:
                                if getattr(lead, field_name) not in [False, '']:
                                    dict_updated[field_name] = getattr(lead, field_name)
                        for field_name in ['county_id', 'pre_auth_county_id']:
                            if getattr(lead, field_name).id not in [False, '']:
                                dict_updated[field_name] = getattr(lead, field_name).id
                        if lead.is_won_stage:
                            for field_name in ['ma_number']:
                                if getattr(lead, field_name) not in [False, '']:
                                    dict_updated[field_name] = getattr(lead, field_name)
                        # isp_data_list = []
                        # if lead.isp_ids:
                        #     for isp_data in lead.isp_ids:
                        #         isp_data_list.append((0, 0, {'outcome_phrase': isp_data.outcome_phrase,
                        #                                     'product_id': isp_data.product_id.id}))
                        #     if isp_data_list:
                        #         dict_updated.update({'isp_ids': isp_data_list})
                        if dict_updated:
                            # if lead.partner_relationship != 'self':
                            #     pass
                                # dict_updated.update({'partner_type': 'patient',
                                #                      'type': 'contact',
                                #                      'child_ids': [(0, 0, {'firstname': lead.representative_firstname,
                                #                                            'lastname': lead.representative_lastname,
                                #                                            'email': lead.representative_email,
                                #                                            'phone': lead.representative_phone,
                                #                                            'mobile': lead.representative_mobile,
                                #                                            'street': lead.representative_street,
                                #                                            'street2': lead.representative_street2,
                                #                                            'city': lead.representative_city,
                                #                                            'state_id': lead.representative_state_id and lead.representative_state_id.id,
                                #                                            'zip': lead.representative_zip,
                                #                                            'country_id': lead.representative_country_id and lead.representative_country_id.id,
                                #                                            'comment': lead.representative_comment,
                                #                                            'partner_type': 'representative',
                                #                                            'type': 'other'
                                #                                            }
                                #                                     )]
                                #                      })
                            partner_id.write(dict_updated)
                            ctx = dict(self.env.context)
                            ctx['from_crm'] = False
                            self.env.context = ctx
                        if partner_id.child_ids:
                            lead.partner_relative_id = partner_id.child_ids[0].id
                        if crm_id.isp_ids:
                            for isp_data in crm_id.isp_ids:
                                isp_data.partner_id = partner_id.id
                lead.partner_id = force_partner_id
            if not lead.partner_id and create_missing:
                partner = lead._create_customer()
                lead.partner_id = partner.id

    def _create_customer(self):
        """ Create a partner from lead data and link it to the lead.

        :return: newly-created partner browse record
        """
        Partner = self.env['res.partner']
        contact_name = self.contact_name
        if not contact_name:
            contact_name = Partner._parse_partner_name(self.email_from)[0] if self.email_from else False

        if self.partner_name:
            partner_company = Partner.create(self._prepare_customer_values(self.partner_name, is_company=True))
        elif self.partner_id:
            partner_company = self.partner_id
        else:
            partner_company = None

        if contact_name:
            ctx = dict(Partner._context)
            ctx['from_crm'] = True
            self.env.context = ctx
            return Partner.with_context(self.env.context).create(self._prepare_customer_values(contact_name, is_company=False, parent_id=partner_company.id if partner_company else False))

        if partner_company:
            return partner_company
        return Partner.create(self._prepare_customer_values(self.name, is_company=False))

