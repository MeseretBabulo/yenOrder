
{
    "name": "Web Notify",
    "summary": """
        Send notification messages to user""",
    "version": "17.0.1.0.1",
    "license": "AGPL-3",
    "author": ")",
    "development_status": "Production/Stable",
    "website": "",
    "depends": ["web", "bus", "base", "mail"],
    "assets": {
        "web.assets_backend": [
            "web_notify/static/src/js/services/*.js",
        ]
    },
    "demo": ["views/res_users_demo.xml"],
    "installable": True,
}
