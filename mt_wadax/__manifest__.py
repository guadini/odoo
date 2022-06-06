# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Mt - Wadax Customizations",
    'summary': 'Base Addon to customize Odoo',
    'description': "Base Addon to customize Odoo",
    'author': "Luis Felipe",
    'website': "https://www.linkedin.com/in/dev-felipevalencia",
    'category': 'Technical',
    'version': '15.0.0.1',
    'depends': ['sale'],
    'data': [
        #'security/mt_security.xml',
        'security/ir.model.access.csv',
        'views/models_views.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
