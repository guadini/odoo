# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Keypress - Manufacturing Customizations",
    'summary': 'Manufacturing Customization',
    'description': "Manufacturing Customization",
    'author': "",
    'website': "",
    'category': 'Manufacturing',
    'version': '15.0.0.0',
    'depends': ['product','stock','mrp','mt_wadax'],
    'data': [
        # data
        'data/ir_cron.xml',
        # views
        'views/stock_move_line_view.xml',
        'views/product_product_view.xml',
        'views/product_template_view.xml',
        'views/stock_warehouse_view.xml',
        'views/stock_location_route_view.xml',
        'views/stock_location_orderpoint_view.xml',
        'views/mrp_production_view.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
