# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
# from uszipcode import SearchEngine
from odoo.http import request


class ResPartner(models.Model):
    _inherit = "res.partner"

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

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company")
    user_id = fields.Many2one(string="Support Coordinator")
    via_company_type = fields.Selection(related='company_id.via_company_type',
                                string="Company Type")
    partner_type = fields.Selection([
                                ('person_support', 'Person Supported'),
                                ('physician', 'Physician'),
                                ('representative', 'Representative'),
                                ('support_coordinator', 'Support Coordinator'),
                                ('other', 'Other')],
                                copy=False,
                                string="Contact Type")
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
    #                              copy=False)
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
    plan_tier = fields.Selection([('A', 'A'),
                                  ('Aa', 'Aa'),
                                  ('B', 'B'),
                                  ('Ba', 'Ba'),
                                  ('C', 'C'),
                                  ('Ca', 'Ca'),
                                  ('D', 'D'),
                                  ('Da', 'Da'),
                                  ('E', 'E'),
                                  ('Ea', 'Ea'),
                                  ('Fa', 'Fa')], string="Tier",
                                  copy=False)
    source_platform = fields.Selection([
                            ('irecord', 'iRecord'),
                            ('hcsis', 'HCSIS')],
                            string="Source Platform", copy=False, default=_get_default_source_platform, compute='_compute_user_company_ids')
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
                            string="Relationship to Presenter")
    firstname = fields.Char(string="First Name")
    lastname = fields.Char(string="Last Name")
    internal_unique_id_code = fields.Char(string="Internal Unique ID",
                                 copy=False)
    ma_number = fields.Char(string="MA Number",
                                 copy=False)
    goes_by = fields.Char(string="Goes by")
    program_type = fields.Selection(_program_type_selection,
                                string="Program Type",
                                 copy=False)
    funding_source = fields.Selection([
                            ('pfds', 'PFDS'),
                            ('community_living', 'Community Living,'),
                            ('consolidated', 'Consolidated'),
                            ('base', 'Base'),
                            ('other', 'Other')],
                            string="Funding Source",
                                 copy=False)
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
    is_need_to_update = fields.Boolean(string="Is Need To Update",
                                 copy=False)
    isp_ids = fields.One2many('via.isp', 'partner_id')
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
    physician_ids = fields.Many2many('res.partner',
        'partner_physician_rel',"partner_id",
        "physician_id", string="Physicians",
        domain="[('partner_type', '=', 'physician')]",
        copy=False)
    service_ids = fields.Many2many('product.template',
            'partner_product_rel',
            'product_id', 'partner_id',
            string='Services',
            copy=False)
    company_type = fields.Selection(default='person')

    _sql_constraints = [
        ('internal_unique_id_code_uniq', 'unique (internal_unique_id_code)', 'The tt Internal Unique ID of the contact must be unique per company!')
    ]

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


    @api.constrains('mci_number', 'ma_number')
    def _check_mis_medicaid_numbers(self):
        for partner in self:
            ma_number_counts = self.search_count([('ma_number', '=', partner.ma_number),
                                                        '|', ('company_id', '=', self.env.company.id),
                                                        ('company_id', '=', False),
                                                        ('id', '!=', partner.id)])
            mci_numbers_counts = self.search_count([('mci_number', '=', partner.mci_number),
                                                    '|', ('company_id', '=', self.env.company.id),
                                                    ('company_id', '=', False),
                                                    ('id', '!=', partner.id)])
            if partner.mci_number and mci_numbers_counts > 0:
                raise ValidationError(_("""MCI number should be unique."""))
            if partner.ma_number and ma_number_counts > 0:
                raise ValidationError(_("""MA number should be unique."""))

    # @api.onchange('zip')
    # def _onchange_county_zip(self):
    #     self.ensure_one()
    #     uscounty_search_engine = SearchEngine()
    #     counties = uscounty_search_engine.by_zipcode(self.zip)
    #     if counties:
    #         if isinstance(counties, list):
    #             county = counties[0].county.split(' ')[0]
    #         else:
    #             county = counties.county.split(' ')[0]
    #         county_search = self.env['via.res.county'].search([('name', 'ilike', county)],
    #                                                     limit=1)
    #         self.county_id = county_search.id
    #     else:
    #         self.county_id = False

    @api.model
    def create(self, vals):
        crm_obj = self.env['crm.lead']
        partner_obj = self.env['res.partner']
        crm_id = False
        if not self._context.get('import_file'):
            if self.env.context and self.env.context.get('active_id'):
                crm_id = crm_obj.browse(self.env.context.get('active_id'))
                if self.env.context.get('from_crm') and crm_id:
                    vals.update({
                        'gender': crm_id.gender,
                        'date_of_birth': crm_id.date_of_birth,
                        'county_id': crm_id.county_id and crm_id.county_id.id,
                        'mci_number': crm_id.mci_number,
                        'plan_start_date': crm_id.plan_start_date,
                        'plan_end_date': crm_id.plan_end_date,
                        'status_of_plan': crm_id.status_of_plan,
                        'assessment_date': crm_id.assessment_date,
                        'is_person_graduating': crm_id.is_person_graduating,
                        'is_legal_guardian': crm_id.is_legal_guardian,
                        # 'medicaid_date_in_service': crm_id.medicaid_date_in_service,
                        # 'medicaid_date_out_service': crm_id.medicaid_date_out_service,
                        'plan_tier': crm_id.plan_tier,
                        'source_platform': crm_id.source_platform,
                        'partner_relationship': crm_id.partner_relationship,
                        'firstname': crm_id.firstname,
                        'lastname': crm_id.lastname,
                        'internal_unique_id_code': crm_id.internal_unique_id_code,
                        'ma_number': crm_id.ma_number,
                        'goes_by': crm_id.goes_by,
                        'program_type': crm_id.program_type,
                        'funding_source': crm_id.funding_source,
                        'distinguish_region': crm_id.distinguish_region,
                        'status': crm_id.status,
                        'race': crm_id.race,
                        'ethnicity': crm_id.ethnicity,
                        'living_arrangement': crm_id.living_arrangement,
                        'primary_language': crm_id.primary_language,
                        'developmental_disability': crm_id.developmental_disability,
                        'intellectual_disability': crm_id.intellectual_disability,
                        'mobility': crm_id.mobility,
                        'commu_issue': crm_id.commu_issue,
                        'sexual_orientation': crm_id.sexual_orientation,
                        'religion': crm_id.religion,
                        'is_hispanic': crm_id.is_hispanic,
                        'is_mexican': crm_id.is_mexican,
                        'is_puerto_rican': crm_id.is_puerto_rican,
                        'is_cuban': crm_id.is_cuban,
                        'is_another_hispanic': crm_id.is_another_hispanic,
                        'is_other_race': crm_id.is_other_race,
                        'is_self_describe': crm_id.is_self_describe,
                        'is_not_say': crm_id.is_not_say,
                        'outcome_phrase': crm_id.outcome_phrase,
                        'reason_for_outcome': crm_id.reason_for_outcome,
                        'outcome_statement': crm_id.outcome_statement,
                        'actions_taken': crm_id.actions_taken,
                        'progress_status': crm_id.progress_status,
                        'date_referral': crm_id.date_referral,
                        'referral_meeting_date': crm_id.referral_meeting_date,
                        'project_auth_date': crm_id.project_auth_date,
                        'pre_auth_region': crm_id.pre_auth_region,
                        'pre_auth_county_id': crm_id.pre_auth_county_id and \
                                              crm_id.pre_auth_county_id.id,
                        'support_coordinator': crm_id.support_coordinator or '',
                        # 'pre_auth_sc_user_id': crm_id.pre_auth_sc_user_id and \
                        #                        crm_id.pre_auth_sc_user_id.id,
                        'sc_phone_no': crm_id.sc_phone_no,
                        'pre_auth_notes': crm_id.pre_auth_notes,
                        'projected_units': crm_id.projected_units,
                        'authorized_date': crm_id.authorized_date,
                        'partner_type': 'person_support',
                        'type': 'contact',
                        'payer_program': crm_id.payer_program,
                        'payer': crm_id.payer,
                    })
                    # isp_data_list = []
                    # if crm_id.isp_ids:
                    #     for isp_data in crm_id.isp_ids:
                    #         isp_data_list.append((0, 0, {'outcome_phrase': isp_data.outcome_phrase,
                    #                                      'product_id': isp_data.product_id.id}))
                    #     if isp_data_list:
                    #         vals.update({'isp_ids': isp_data_list})
                    if crm_id.partner_relationship != 'self':
                        vals.update({'child_ids': [(0, 0, {
                            'firstname': crm_id.representative_firstname,
                            'lastname': crm_id.representative_lastname,
                            'email': crm_id.representative_email,
                            'phone': crm_id.representative_phone,
                            'mobile': crm_id.representative_mobile,
                            'street': crm_id.representative_street,
                            'street2': crm_id.representative_street2,
                            'city': crm_id.representative_city,
                            'state_id': crm_id.representative_state_id and \
                                        crm_id.representative_state_id.id,
                            'zip': crm_id.representative_zip,
                            'country_id': crm_id.representative_country_id and \
                                          crm_id.representative_country_id.id,
                            'comment': crm_id.representative_comment,
                            'partner_type': 'representative',
                            'type': 'other',
                            'partner_relationship': crm_id.partner_relationship or ''
                        })]})
                    ctx = dict(self.env.context)
                    ctx['from_crm'] = False
                    self.env.context = ctx
        else:
            return super().create(vals)
        res = super(ResPartner, self).create(vals)
        if res.child_ids and crm_id:
            crm_id.partner_relative_id = res.child_ids[0].id
        if crm_id and crm_id.isp_ids:
            for isp_data in crm_id.isp_ids:
                isp_data.partner_id = res.id
        return res

    @api.depends('company_id')
    def _compute_user_company_ids(self):
        for rec in self:
            if rec.company_id.via_company_type == 'nj':
                rec.source_platform = 'irecord'
            else:
                rec.source_platform = 'hcsis'
    def write(self, vals):
        if vals.get('street') or vals.get('street2') or vals.get('country_id') or vals.get('city') or vals.get('state_id') \
                or vals.get('zip') or vals.get('firstname') or vals.get('lastname') or vals.get('payer') or \
                vals.get('payer_program') or vals.get('phone'):
            vals.update({'is_need_to_update': True})
        return super(ResPartner, self).write(vals)

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     context = self._context or {}
    #     args = args or []
    #     if self.env.user.sale_team_id:
    #         if self.env.user.has_group('base.group_system'):
    #             args += []
    #         else:
    #             args += [('team_id', '=', self.env.user.sale_team_id.id)]
    #     else:
    #         args += [('team_id', 'in', [])]
    #     return super(ResPartner, self).search(args, offset, limit, order, count=count)


class VIAIsp(models.Model):
    _name = 'via.isp'
    _description = 'VIA ISP Data'
    _rec_name = 'outcome_phrase'

    outcome_phrase = fields.Html(string="Outcome Phrase", compute='_compute_outcome_phrase', readonly=False, store=True)
    reason_for_outcome = fields.Text(string="Reason for Outcome")
    outcome_statement = fields.Text(string="Outcome Statement")
    actions_taken = fields.Text(string="Actions")
    progress_status = fields.Text(string="Progress")
    partner_id = fields.Many2one('res.partner', string="Partner")
    product_id = fields.Many2one('product.product', string="Service")
    crm_lead_id = fields.Many2one('crm.lead', string="Lead")

    @api.onchange('product_id')
    def onchange_product_id(self):
        for record in self:
            record.outcome_phrase = record.product_id.isp_description

    @api.depends('product_id')
    def _compute_outcome_phrase(self):
        for record in self:
            record.outcome_phrase = record.product_id.isp_description
