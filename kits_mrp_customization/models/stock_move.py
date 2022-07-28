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

        allocate_line_ids = self.env['kits.reel.allocate.line'].search([('mo_id','=',self.mapped('raw_material_production_id').id)])
        if allocate_line_ids:
            for reel_component in reel_components:
                allocate_line_id = False
                allocate_line_id = allocate_line_ids.filtered(lambda x: x.component_line_id == reel_component)

                if not allocate_line_id:
                    continue

                # Edit Line
                if allocate_line_id.move_line_id:
                    continue
                    # allocate_line_id.with_context(bypass_reservation_update=True).move_line_id.write({
                    #     'lot_id':allocate_line_id.lot_id,
                    #     'product_uom_qty':allocate_line_id.qty_allocated,
                    # })
                # Create line
                else:
                    lot_id = allocate_line_id.lot_id
                    quants = reel_component.location_id.quant_ids.filtered(lambda x: x.lot_id == lot_id and ((x.quantity - x.reserved_quantity) >= (reel_component.product_qty-reel_component.reserved_availability)))
                    if not quants:
                        continue
                    ml_id = self.env['stock.move.line'].create({
                        'move_id':reel_component.id,
                        'company_id':reel_component.company_id.id,
                        'date':fields.Datetime.now(),
                        'location_dest_id':reel_component.location_dest_id.id,
                        'location_id':reel_component.location_id.id,
                        'product_uom_id':allocate_line_id.product_id.uom_id.id,
                        'product_uom_qty':allocate_line_id.qty_allocated,
                        'product_id':allocate_line_id.product_id.id,
                        'lot_id':lot_id.id,
                        })
                    allocate_line_id.move_line_id = ml_id
                reel_component.with_context(confirm_reel=True)._action_assign()
        return res
