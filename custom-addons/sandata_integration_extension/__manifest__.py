
{
    'name': 'SANDATA Integration Extension',
    'version': '1.0.1',
    'category': '',
    'summary': '',
    'author': '',
    'license': '',
    'description': 'SANDATA Integrations Extension',
    'depends': [
       'sandata_integration', 'project', 'bista_timesheet_attendance'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/other_location_wizard.xml',
        'views/via_attendance_line_view.xml',
        'views/project_task_view.xml',
    ],
    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
