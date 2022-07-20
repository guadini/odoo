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

    def compute_details(self):
        for record in self:
            counted = []
            qty_nededed = 0
            qty_allocated = 0
            for line in record.allocate_line_ids:
                if line.component_line_id not in counted:
                    qty_nededed += line.qty_needed
                    counted.append(line.component_line_id)
                qty_allocated += line.qty_allocated
            for line in record.alternative_line_ids:
                if line.component_line_id not in counted:
                    qty_nededed += line.qty_needed
                    counted.append(line.component_line_id)
                qty_allocated += line.qty_allocated
            record.total_needed = qty_nededed
            record.total_allocated = qty_allocated
