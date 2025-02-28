{
    'name': 'Portal Attendance',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Employee Portal Attendance Management',
    'description': """
        Portal Attendance Management for Employees
        - Check-in and Check-out functionality
        - Location tracking
        - Attendance history
    """,
    'depends': [
        'portal',
        'hr_attendance',
        'web',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/portal_attendance_security.xml',
        'views/portal_attendance_templates.xml',
        'views/hr_attendance_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/portal_attendance/static/src/js/attendance_portal.js',
            '/portal_attendance/static/src/css/attendance.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}