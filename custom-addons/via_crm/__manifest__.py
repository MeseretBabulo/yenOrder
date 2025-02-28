# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


{
    'name': 'VIA CRM',
    'version': '1.0.1',
    'category': 'CRM',
    'summary': '',
    'author': 'Bista Solutions',
    'license': 'AGPL-3',
    'description': 'CRM Related Customization.',
    'depends': [
       'base','web','crm', 'contacts', 'partner_firstname', 'website', 'sale_crm', 'project', 'bista_timesheet_attendance', 'timesheet_grid', 'industry_fsm', 'project_enterprise'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/via_import_lead_view.xml',
        'views/via_res_county_view.xml',
        'views/res_config_settings_views.xml',
        'views/res_company_view.xml',
        'views/crm_stage_view.xml',
        'views/crm_view.xml',
        # 'views/res_partner_view.xml',
        'data/ir_model_data.xml',
        'views/project_view.xml',
        
    ],

    'demo': [],
    'test': [],
    'qweb': [],
    'assets': {
        'web.assets_qweb': [
            'via_crm/static/src/xml/lead_tree_generate_leads_views.xml',
        ],
        'web.assets_backend': [
            'via_crm/static/src/js/crm_state_clickable.js'
        ],
        'web.assets_frontend': [
            'via_crm/static/src/js/crm_form.js',
            'via_crm/static/src/js/website_crm_form_editor.js',
        ],
        'website.assets_wysiwyg': ['via_crm/static/src/snippets/s_website_form/crm_form_options.js']
    },
    'installable': True,
    'auto_install': True,
}
