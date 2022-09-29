from odoo import models,fields,api,_
from lxml import etree

class stock_warehouse_orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    alternate_product_ids = fields.Many2many('mt.product.product','replenishment_alternate_products_rel','replenishment_id','alternate_product_id','Alternate Products',compute="_compute_details",store=True,compute_sudo=True)
    purchase_uom_id = fields.Many2one('uom.uom','Purchase UoM',related="product_id.uom_po_id")
    have_bom = fields.Boolean('Have BOM ?',compute='_compute_have_bom',store=True,compute_sudo=True)
    vendor_ids = fields.Many2many('product.supplierinfo','replenishment_supplierinfo_rel','replenishment_id','supplier_id','Vendors',compute='_compute_details',store=True,compute_sudo=True)
    kits_on_hand = fields.Float('On Hand',compute="_compute_details",store=True,compute_sudo=True)
    mo_ids = fields.Many2many('mrp.production','replenishment_manufacturing_rel','replenishment_id','manufacturing_id','Manufacutring Orders',compute="_compute_total")
    qty_total_consume = fields.Float('Total Consume',compute="_compute_total")
    qty_to_consume = fields.Float('To Consume',compute="_compute_total")
    is_reel = fields.Boolean('Is reel ?',compute="_compute_is_reel",store=True,compute_sudo=True)

    @api.depends('product_id','product_id.is_reel')
    def _compute_is_reel(self):
        for record in self:
            record.is_reel = record.product_id.is_reel

    # @api.depends('allocate_ids','allocate_ids.total_needed','allocate_ids.total_allocated')
    def _compute_total(self):
        mo_obj = self.env['mrp.production'].sudo()
        for record in self:
            moves = self.env['stock.move'].search([('raw_material_production_id','!=',False),('location_id','=',record.location_id.id),('product_id','=',record.product_id.id),('raw_material_production_id.state','in',('confirmed','progress'))])
            done_moves = moves.filtered(lambda x: x.product_uom_qty <= x.reserved_availability)
            moves -= done_moves
            manufacturing_ids = moves.mapped('raw_material_production_id')
            record.mo_ids = [(6,0,manufacturing_ids.ids)]

    #         total_needed = sum(record.allocate_ids.mapped('total_needed'))
    #         total_allocated = sum(record.allocate_ids.mapped('total_allocated'))
    #         record.qty_satisfied = True if total_allocated and (total_needed <= total_allocated) else True if not moves and done_moves else False

            qty = sum(moves.mapped('product_qty'))-sum(moves.mapped('reserved_availability'))
            record.qty_total_consume = qty
            to_consume = 0
            mo_id = record._context.get('mo_id')
            # if record.product_id.is_reel and mo_id:
            if mo_id:
                mo = mo_obj
                if isinstance(mo_id,int):
                    mo = mo_obj.browse(mo_id)
                if mo.id:
                    qty_in_moves = mo.move_raw_ids.filtered(lambda x: x.product_id == record.product_id).mapped('product_uom_qty')
                    to_consume = sum(qty_in_moves) if len(qty_in_moves) else 0
            record.qty_to_consume = to_consume
    #         record.qty_to_order = total_allocated

    @api.depends('product_id','product_id.mt_product_alternative_ids','product_id.seller_ids','location_id')
    def _compute_details(self):
        for record in self:
            record.alternate_product_ids = [(6,0,record.product_id.mt_product_alternative_ids.ids)]
            record.vendor_ids = [(6,0,record.product_id.seller_ids.ids)]
            on_hand = 0.0
            for stock in record.location_id.quant_ids.filtered(lambda x: x.product_id == record.product_id):
                on_hand += stock.quantity
            record.kits_on_hand = on_hand
    
    @api.depends('product_id','bom_id')
    def _compute_have_bom(self):
        for record in self:
            record.have_bom = bool(self.env['mrp.bom'].search([('product_tmpl_id','=',record.product_id.product_tmpl_id.id)],limit=1))
    
    def cron_auto_create_replanishment(self):
        warehouse_obj = self.env['stock.warehouse'].sudo()
        route_obj = self.env['stock.location.route'].sudo()
        locations = warehouse_obj.search([]).mapped('lot_stock_id')
        default_wh_id = warehouse_obj.search([('system_default','=',True)],limit=1)

        default_buying_route = route_obj.search([('buying_default','=',True)],limit=1)
        default_manufacture_route = route_obj.search([('manufacture_default','=',True)],limit=1)

        if default_wh_id and default_buying_route and default_manufacture_route:
            for product in self.env['product.product'].sudo().search([]):
                for location in locations:
                    route_id = route_obj
                    replenishment_id = self.sudo().search([('product_id','=',product.id),('location_id','=',location.id),('active','in',(True,False))],limit=1)
                    if self.env['mrp.bom'].sudo().search([('product_tmpl_id','=',product.product_tmpl_id.id)],limit=1):
                        route_id = default_manufacture_route
                    else:
                        if location == default_wh_id.lot_stock_id:
                            route_id = default_buying_route
                        else:
                            spfw_route = route_obj.search([
                                ('supplier_wh_id','=',default_wh_id.id),
                                ('supplied_wh_id','=',location.warehouse_id.id)
                                ],limit=1)
                            if not spfw_route:
                                continue
                            route_id = spfw_route
                    if not replenishment_id:
                        replenishment_id = self.sudo().create({
                            'product_id':product.id,
                            'location_id':location.id,
                            'route_id':route_id.id,
                            'trigger':'manual',
                            'product_max_qty':0,
                            'product_min_qty':0,
                            'qty_to_order':0,
                            })
                        replenishment_id._onchange_location_id() # #Onchange call to set warehouse from location.
                    else:
                        # ###Set warehouse if not set.
                        replenishment_id._onchange_location_id()
                        replenishment_id._compute_have_bom() # #Check bom each time in existing replenishments.
                        # #Set Route in existing Replenishment - According Requirement.
                        if route_id and route_id.id:
                            replenishment_id.route_id = route_id.id


