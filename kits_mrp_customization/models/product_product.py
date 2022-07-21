from odoo import models,fields

class product_product(models.Model):
    _inherit = 'product.product'

    multilocation_available = fields.Boolean('Available At Multiple Location')
    next_auto_lot_number = fields.Integer('Next Auto Lot Number',default=1)
