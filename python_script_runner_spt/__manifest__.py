{
    "name": "Python Script Runner",
    "description": """
    Installing this module, user will able to run python code from Odoo.
""",
    "version": "13.0.0.1",
    'author': 'SnepTech',
    'license': 'AGPL-3',
    'website': 'https://www.sneptech.com',
    "depends": ['base'],
    "data": [
        'security/ir.model.access.csv',
        'views/python_script_runner_view.xml',
    ],
    "demo_xml": [],
    "installable": True,
}
