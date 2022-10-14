from odoo import models,fields

class stock_move(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        move_obj = self.env['stock.move']
        reel_components = move_obj
        if self.raw_material_production_id:
            if not self._context.get('confirm_reel'):
                for record in self:
                    if record.product_id.is_reel:
                        reel_components |= record
        self -= reel_components
        res = super(stock_move,self)._action_assign()
        return res
    
    def _do_unreserve(self):
        return super(stock_move,self.with_context(bypass_reservation_update=True))._do_unreserve()
