{
    'name': 'Bista Timesheet Attendance',
    'version': '1.0.1',
    'category': 'HR',
    'summary': '',
    'author': 'Bista Solutions',
    'license': 'AGPL-3',
    'description': 'To Create Timsheet from the Attendance.',
    'depends': [
       'web', 'hr_timesheet', 'project', 'crm','web_cohort','web_map','knowledge'
    ],
    'data': [
        "data/location_data.xml",
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/project_view.xml',
        'wizard/attendance_confirm_msg_wizard_view.xml',
        'views/project_view.xml',
        'views/attendance_confirm_msg_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bista_timesheet_attendance/static/src/js/widget_location_lat_lng.js',
            # 'bista_timesheet_attendance/static/src/js/timesheet_buttons.js',
            # 'bista_timesheet_attendance/static/src/js/manifest.js',
            'bista_timesheet_attendance/static/src/xml/base.xml',
        ],
        # 'web.assets_qweb': [
        #     'bista_timesheet_attendance/static/src/xml/base.xml',
        # ],

    },




    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': True,
}
