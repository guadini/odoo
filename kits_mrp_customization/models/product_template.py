from odoo import models,fields,api

class product_template(models.Model):
    _inherit = 'product.template'

    # is_reel = fields.Boolean('Is Reel?')
    kits_critico = fields.Boolean('Critinal (Critico)')
    kits_mandatory = fields.Boolean('Mandatory')
    multilocation_available = fields.Boolean('Available At Multiple Location')

    # @api.onchange('is_reel')
    # def _onchange_is_reel(self):
    #     for record in self:
    #         if record.is_reel:
    #             record.type = 'product'
    #             record.tracking = 'lot'
    #         else:
    #             record.tracking = 'none'
