from odoo import models,fields


class product_template(models.Model):
    _inherit = 'product.template'

    is_reel = fields.Boolean('Is Reel?')
    kits_critico = fields.Boolean('Critinal (Critico)')
    kits_mandatory = fields.Boolean('Mandatory')
