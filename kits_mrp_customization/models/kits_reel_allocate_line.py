from odoo import models,fields,api,_
from odoo.exceptions import UserError

class kits_reel_allocate_line(models.Model):
    _name = 'kits.reel.allocate.line'
    _description = 'Reel Allocate Lines'
    _rec_name = 'product_id'

    allocate_id = fields.Many2one('kits.reel.allocate','Reel Allocation',ondelete="cascade")
    alternate_allocate_id = fields.Many2one('kits.reel.allocate','Alternate Reel Allocation',ondelete="cascade")
    
    product_id = fields.Many2one('product.product','Product',ondelete='restrict')
    mo_id = fields.Many2one('mrp.production','Manufacturing',ondelete='restrict')
    lot_id = fields.Many2one("stock.production.lot",'Lot Number',ondelete='restrict')
    component_line_id = fields.Many2one('stock.move','Component Line',ondelete='cascade')
    # qty_needed = fields.Float('Quantity Needed',related="component_line_id.product_uom_qty")
    qty_needed = fields.Float('Quantity Needed',compute="_compute_qty_needed")
    qty_allocated = fields.Float('Allocated Quantity')
    wh_quantity = fields.Float('Available Qty',related='lot_id.product_qty')

    allowed_alternate_product_ids = fields.Many2many('product.product','reel_allocate_line_alternate_products_rel','reel_allocate_line_id','product_product_id','Alternate products',compute="_compute_allowed_alternate_product_ids",store=True,compute_sudo=True)

    # For Lot Allocation
    quant_id = fields.Many2one('stock.quant','Allocated Stock')
    location_src_id = fields.Many2one('stock.location','Source Location',ondelete="restrict")
    move_line_id = fields.Many2one('stock.move.line','Move Line')
    move_id = fields.Many2one('stock.move','Main Product Component Line')

    @api.depends('product_id','product_id.mt_product_alternative_ids','allocate_id','alternate_allocate_id')
    def _compute_allowed_alternate_product_ids(self):
        for record in self:
            record.allowed_alternate_product_ids = [(6,0,record.alternate_allocate_id.product_id.mt_product_alternative_ids.mapped('mt_product_id').ids)]
    
    @api.depends('component_line_id','component_line_id.product_qty','move_id','move_id.product_qty')
    def _compute_qty_needed(self):
        for record in self:
            # needed = (record.move_id.product_uom_qty-record.move_id.reserved_availability) or (record.component_line_id.product_uom_qty - record.component_line_id.reserved_availability)
            needed = record.move_id.product_uom_qty or record.component_line_id.product_uom_qty
            record.qty_needed = needed

    @api.onchange('product_id','lot_id')
    def _onchange_product_id(self):
        stock_location_ids = self.env['stock.warehouse'].sudo().search([]).mapped('lot_stock_id')
        self.ensure_one()
        mo_obj = self.env['mrp.production']
        bom_line_obj = self.env['mrp.bom.line']
        mo_ids = mo_obj
        template_product_ids = bom_line_obj.search([('product_id','=',self.product_id.id)]).mapped('bom_id').mapped('product_tmpl_id')
        mo_ids = mo_obj.search([('state','in',('draft','confirmed','progress')),('product_id','in',template_product_ids.product_variant_ids.ids)])
        if self.alternate_allocate_id and self.product_id:
            mo_ids = self.alternate_allocate_id.replenishment_id.mo_ids

        domain = {
            'domain':{
                'mo_id':[('id','in',mo_ids.ids)],
                }
            }

        if self.alternate_allocate_id and self.product_id:
            lot_ids = self.env['stock.production.lot'].search([('product_id','=',self.product_id.id)])
            
            move_line_ids = self.env['stock.move.line'].search([('move_id','!=',False),('product_id','=',self.product_id.id),('state','in',('assigned','done')),('location_id','in',stock_location_ids.ids)])
            lot_ids -= move_line_ids.mapped('lot_id')

            domain['domain']['lot_id'] = [('id','in',lot_ids.ids)]
        return domain
    
    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        self.ensure_one()
        if self.lot_id:
            new_lot_quant_ids = self.env['stock.quant'].search([('on_hand','=',True),('product_id','=',self.product_id.id),('lot_id','=',self.lot_id.id)])
            new_lot_quant_id = new_lot_quant_ids[0] if len(new_lot_quant_ids) else False
            if new_lot_quant_id:
                self.qty_allocated = new_lot_quant_id.quantity - new_lot_quant_id.reserved_quantity
                self.quant_id = new_lot_quant_id

    # @api.model
    # def create(self,vals):
    #     res = super(kits_reel_allocate_line,self).create(vals)
    #     allocate_id = res.allocate_id or res.alternate_allocate_id
    #     if allocate_id.total_needed <= allocate_id.total_allocated:
    #         raise UserError(_('The need is satisfied. Please check allocated lines for extra stock.'))

    #     if res and (res.component_line_id or res.move_id):
    #         ml_vals = {
    #             'move_id':res.component_line_id.id,
    #             'company_id':res.component_line_id.company_id.id,
    #             'date':fields.Datetime.now(),
    #             'location_dest_id':res.component_line_id.location_dest_id.id,
    #             'location_id':res.quant_id.location_id.id,
    #             'product_uom_id':res.product_id.uom_id.id,
    #             'product_uom_qty':res.qty_allocated,
    #             'product_id':res.product_id.id,
    #             'lot_id':res.lot_id.id,
    #             }

    #         if res.alternate_allocate_id:
    #             # Remove Existing
    #             qty_pending = res.move_id.product_qty - res.move_id.reserved_availability

    #             # Change demand in main product's component line
    #             res.move_id.with_context(bypass_reservation_update=True).product_uom_qty = res.move_id.product_qty - qty_pending
                
    #             component_line_id = self.mo_id.move_raw_ids.filtered(lambda x: x.product_id == self.product_id and x.location_id == res.quant_id.location_id and x.product_uom_qty == qty_pending and (self.lot_id in x.move_line_ids.mapped('lot_id') or not x.move_line_ids.mapped('lot_id')) and x.product_uom_qty > x.quantity_done)
    #             if not component_line_id:
    #                 # Extra component line for Alternate product
    #                 component_line_id = self.env['stock.move'].sudo().create({
    #                     'raw_material_production_id':res.mo_id.id,
    #                     'location_id':res.quant_id.location_id.id,
    #                     'location_dest_id':res.mo_id.location_dest_id.id,
    #                     'company_id':res.mo_id.company_id.id,
    #                     'product_uom_qty':qty_pending,
    #                     'product_id':res.product_id.id,
    #                     'name':res.product_id.display_name,
    #                     'product_uom':res.product_id.uom_id.id,
    #                     'date':fields.Datetime.now(),
    #                     'procure_method':'make_to_stock',
    #                     'should_consume_qty':0,
    #                 })
    #             else:
    #                 component_line_id.write({
    #                     'product_uom_qty':qty_pending,
    #                 })
                
    #             # Confirm Alternate product move
    #             component_line_id._action_assign()
                
    #             res.with_context(bypass=True).component_line_id = component_line_id

    #             ml_vals.update({
    #                 'move_id':component_line_id.id,
    #                 'product_id':res.product_id.id,
    #                 'location_id':res.quant_id.location_id.id,
    #                 'location_dest_id':res.mo_id.location_dest_id.id,
    #                 'product_uom_qty':qty_pending,
    #             })

    #         move_line_id = self.env['stock.move.line'].with_context(bypass=True).create(ml_vals)
    #         res.with_context(bypass=True).move_line_id = move_line_id
    #     return res

    # def write(self,vals):
    #     res = super(kits_reel_allocate_line,self).write(vals)
    #     if not self._context.get('bypass') and res:
    #         if self.move_line_id:
    #             self.move_line_id.with_context(bypass_reservation_update=True).write({
    #                 'lot_id':self.lot_id.id,
    #                 'location_id':self.quant_id.location_id.id,
    #                 'product_uom_qty':self.qty_allocated,
    #             })
    #     return res

    # def unlink(self):
    #     to_delete = self.env['stock.move.line']
    #     for record in self:
    #         record.move_line_id.with_context(bypass_reservation_update=True).product_uom_qty = 0
    #         if record.alternate_allocate_id:
    #             record.move_id.write({'product_uom_qty':record.move_id.product_uom_qty+record.component_line_id.product_uom_qty})
    #             record.component_line_id.unlink()
    #             continue
    #         to_delete |= record.move_line_id
    #     res = super(kits_reel_allocate_line,self).unlink()
    #     if res:
    #         to_delete.unlink()
    #     return res

    @api.onchange('mo_id')
    def _onchange_mo_id(self):
        self.ensure_one()
        if self.mo_id and self.product_id :
            # Find the component line to remove replace with alternate product
            mo_ids = self.alternate_allocate_id.replenishment_id.mo_ids or self.allocate_id.replenishment_id.mo_ids

            # Alternate main products
            if self.alternate_allocate_id:
                main_template_ids = self.env['mt.product.product'].search([('mt_product_id','=',self.product_id.id)]).mapped('mt_product_tmpl_id')
                component_line_ids = mo_ids.mapped('move_raw_ids').filtered(lambda x: x.product_id in main_template_ids.product_variant_ids)
                # Find auto allocation lines
                self.move_id = component_line_ids[0] if len(component_line_ids) else False
                existing_component_lines = mo_ids.mapped('move_raw_ids').filtered(lambda x: x.product_id == self.product_id)
                self.component_line_id = existing_component_lines[0] if len(existing_component_lines) else False
            else:
                component_line_ids = mo_ids.mapped('move_raw_ids').filtered(lambda x: x.product_id == self.product_id)
                self.component_line_id = component_line_ids[0] if len(component_line_ids) else False
