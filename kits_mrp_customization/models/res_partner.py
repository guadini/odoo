from odoo import models,fields

class res_partner(models.Model):
    _inherit = 'res.partner'

    kits_commercial_name = fields.Char('TRADE NAME')
