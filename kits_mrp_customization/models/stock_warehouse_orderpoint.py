from odoo import models,fields,api,_

class stock_warehouse_orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    alternate_product_ids = fields.Many2many('mt.product.product','replenishment_alternate_products_rel','replenishment_id','alternate_product_id','Alternate Products',compute="_compute_details",store=True,compute_sudo=True)
    purchase_uom_id = fields.Many2one('uom.uom','Purchase UoM',related="product_id.uom_po_id")
    have_bom = fields.Boolean('Have BOM ?',compute='_compute_have_bom',store=True,compute_sudo=True)
    vendor_ids = fields.Many2many('product.supplierinfo','replenishment_supplierinfo_rel','replenishment_id','supplier_id','Vendors',compute='_compute_details',store=True,compute_sudo=True)
    kits_on_hand = fields.Float('On Hand',compute="_compute_details",store=True,compute_sudo=True)

  
   
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
        default_wh_loc_id = warehouse_obj.search([('system_default','=',True)],limit=1)

        default_buying_route = route_obj.search([('buying_default','=',True)],limit=1)
        default_manufacture_route = route_obj.search([('manufacture_default','=',True)],limit=1)
        default_spfw_route = route_obj.search([('spfw_default','=',True)],limit=1)

        if default_wh_loc_id and default_buying_route and default_manufacture_route and default_spfw_route:
            for product in self.env['product.product'].sudo().search([]):
                for location in locations:
                    route_id = route_obj
                    replenishment_id = self.sudo().search([('product_id','=',product.id),('location_id','=',location.id),('active','in',(True,False))],limit=1)
                    if self.env['mrp.bom'].sudo().search([('product_tmpl_id','=',product.product_tmpl_id.id)],limit=1):
                        route_id = default_manufacture_route
                    else:
                        if location == default_wh_loc_id.lot_stock_id:
                            route_id = default_buying_route
                        else:
                            route_id = default_spfw_route
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
                        # #Set warehouse if not set.
                        replenishment_id.qty_to_order = 0
                        replenishment_id._onchange_location_id()
                        replenishment_id._compute_have_bom() # #Check bom each time in existing replenishments.
                        # #Set Route in existing Replenishment - According Requirement.
                        if route_id and route_id.id:
                            replenishment_id.route_id = route_id.id

   
