from odoo import models,_
from odoo.exceptions import UserError

class stock_picking(models.Model):
    _inherit = 'stock.picking'


    def button_validate(self):
        if self.picking_type_code == 'incoming':
            for move in self.move_ids_without_package:
                if move.product_id.is_reel and move.product_id.tracking == 'lot' and move.move_line_ids:
                    for move_line in move.move_line_ids.filtered(lambda x: x.qty_done):
                        if move_line.is_reel and not move_line.type:
                            raise UserError(_('Type is not selected for reel product.'))
                        if move_line.type:
                            lot_name = 'Reel-' if move_line.type == 'reel' else 'Strip-' if move_line.type == 'strip' else 'SA-'
                            lot_name += str(move_line.product_id.id)+'-'
                            next_auto_number = move_line.product_id.next_auto_lot_number
                            if not next_auto_number:
                                next_auto_number = 1
                            lot_name += format(next_auto_number,'04')
                            move_line.lot_name = lot_name
                            move_line.product_id.next_auto_lot_number = next_auto_number+1
        res = super(stock_picking,self).button_validate()
        return res