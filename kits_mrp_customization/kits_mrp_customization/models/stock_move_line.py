from odoo import models,fields,api

class stock_move_line(models.Model):
    _inherit = 'stock.move.line'

    type = fields.Selection([('reel','Reel of'),('strip','Strip Of'),('stand_alone','Stand Alone Units')],string="Type")
    is_reel = fields.Boolean('Is Reel?',related="product_id.is_reel")