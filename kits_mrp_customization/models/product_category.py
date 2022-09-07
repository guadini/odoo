from odoo import models,fields

class product_category(models.Model):
    _inherit = 'product.category'

    description = fields.Text('Description')