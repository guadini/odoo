from odoo import models,fields,api

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
    qty_needed = fields.Float('Quantity Needed',related="component_line_id.product_qty")
    qty_allocated = fields.Float('Allocated Quantity')
    # wh_quantity = fields.Float('Available Qty',compute="_compute_wh_quantity")
    wh_quantity = fields.Float('Available Qty',related='lot_id.product_qty')

    allowed_alternate_product_ids = fields.Many2many('product.product','reel_allocate_line_alternate_products_rel','reel_allocate_line_id','product_product_id','Alternate products',compute="_compute_allowed_alternate_product_ids",store=True,compute_sudo=True)

    # For Lot Allocation
    quant_id = fields.Many2one('stock.quant','Allocated Stock')
    location_src_id = fields.Many2one('stock.location','Source Location',ondelete="restrict")
    move_line_id = fields.Many2one('stock.move.line','Move Line',ondelete="restrict")

    # @api.depends('product_id','allocate_id','alternate_allocate_id')
    # def _compute_wh_quantity(self):
    #     for record in self:
    #         allocate_id = record.allocate_id or record.alternate_allocate_id or False
    #         total_available = 0
    #         if allocate_id:
    #             quant_ids = self.env['stock.quant'].search([('product_id','=',allocate_id.product_id.id),('on_hand','=',True),('location_id','=',allocate_id.replenishment_id.location_id.id),('quantity','>=',1)])
    #             total_available = sum(quant_ids.mapped('quantity'))
    #         record.wh_quantity = total_available
                
    @api.depends('product_id','product_id.mt_product_alternative_ids')
    def _compute_allowed_alternate_product_ids(self):
        for record in self:
            record.allowed_alternate_product_ids = [(6,0,record.product_id.mt_product_alternative_ids.mapped('mt_product_id').ids)]

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        template_product_ids = self.env['mrp.bom.line'].search([('product_id','=',self.product_id.id)]).mapped('bom_id').mapped('product_tmpl_id')
        
        mo_ids = self.env['mrp.production'].search([('state','in',('draft','confirmed','progress')),('product_id','in',template_product_ids.product_variant_ids.ids)])
        return {
            'domain':{'mo_id':[('id','in',mo_ids)]}
        }

    @api.model
    def create(self,vals):
        res = super(kits_reel_allocate_line,self).create(vals)
        # if res and res.component_line_id:
        #     move_line_id = self.env['stock.move.line'].create({
        #         'move_id':res.component_line_id.id,
        #         'company_id':res.component_line_id.company_id.id,
        #         'date':fields.Datetime.now(),
        #         'location_dest_id':res.component_line_id.location_dest_id.id,
        #         'location_id':res.component_line_id.location_id.id,
        #         'product_uom_id':res.product_id.uom_id.id,
        #         'product_uom_qty':res.qty_allocated,
        #         'product_id':res.product_id.id,
        #         'lot_id':res.lot_id.id,
        #         })
        #     res.move_line_id = move_line_id
        return res

    def write(self,vals):
        res = super(kits_reel_allocate_line,self).write(vals)
        return res

    def unlink(self):
        # to_delete = self.env['stock.move.line']
        # for record in self:
        #     to_delete |= record.move_line_id

        res = super(kits_reel_allocate_line,self).unlink()
        # if res:
        #     to_delete.unlink()

        return res
