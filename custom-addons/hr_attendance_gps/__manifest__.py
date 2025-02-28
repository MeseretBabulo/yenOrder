{
    'name': 'HR Attendance GPS',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'GPS Location for Attendance',
    'depends': ['hr_attendance', 'web'],
    'data': [
        'views/hr_attendance_view.xml',
        'views/template.xml',
        
    ],
    'assets': {
        'web.assets_backend': [
            'static/src/js/my_attendances.js',
            'static/src/js/attendance_geolocation.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}