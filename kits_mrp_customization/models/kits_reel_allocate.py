from odoo import models,fields,api

class kits_reel_allocate_line(models.Model):
    _name = 'kits.reel.allocate'
    _description = 'Reel Allocate'
    _rec_name = 'product_id'
    
    replenishment_id = fields.Many2one('stock.warehouse.orderpoint','Replenishment',ondelete="cascade")
    product_id = fields.Many2one('product.product','Product',related="replenishment_id.product_id")
    allocate_line_ids = fields.One2many('kits.reel.allocate.line','allocate_id','Allocation Lines')
    alternative_line_ids = fields.One2many('kits.reel.allocate.line','alternate_allocate_id','Alternate product lines')

    total_needed = fields.Integer('Total Needed',compute="compute_details")
    total_allocated = fields.Integer('Total Allocated',compute="compute_details")

    @api.depends('allocate_line_ids','alternative_line_ids','allocate_line_ids.qty_allocated','alternative_line_ids.qty_allocated')
    def compute_details(self):
        for record in self:
            qty_allocated = 0
            moves = self.env['stock.move'].search([('raw_material_production_id','!=',False),('product_id.is_reel','=',True),('location_id','=',record.replenishment_id.location_id.id),('raw_material_production_id.state','=','confirmed')])
            qty_needed = sum(moves.mapped('product_qty'))
            for line in record.allocate_line_ids:
                qty_allocated += line.qty_allocated
            for line in record.alternative_line_ids:
                qty_allocated += line.qty_allocated
            
            record.write({'total_needed':qty_needed,'total_allocated':qty_allocated})
