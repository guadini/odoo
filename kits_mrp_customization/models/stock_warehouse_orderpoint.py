from odoo import models,fields,api,_

class stock_warehouse_orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    alternate_product_ids = fields.Many2many('mt.product.product','replenishment_alternate_products_rel','replenishment_id','alternate_product_id','Alternate Products',compute="_compute_details",store=True,compute_sudo=True)
    purchase_uom_id = fields.Many2one('uom.uom','Purchase UoM',related="product_id.uom_po_id")
    have_bom = fields.Boolean('Have BOM ?',compute='_compute_have_bom',store=True,compute_sudo=True)
    vendor_ids = fields.Many2many('product.supplierinfo','replenishment_supplierinfo_rel','replenishment_id','supplier_id','Vendors',compute='_compute_details',store=True,compute_sudo=True)
    kits_on_hand = fields.Float('On Hand',compute="_compute_details",store=True,compute_sudo=True)

    allocate_ids = fields.One2many('kits.reel.allocate','replenishment_id','#Lot Allocate')
    qty_satisfied = fields.Boolean('Total Allocated',compute="_compute_total")
    mo_ids = fields.Many2many('mrp.production','replenishment_manufacturing_rel','replenishment_id','manufacturing_id','Manufacutring Orders',compute="_compute_total")
    qty_to_consume = fields.Float('To Consume',compute="_compute_total")

    @api.depends('allocate_ids','allocate_ids.total_needed','allocate_ids.total_allocated')
    def _compute_total(self):
        for record in self:
            moves = self.env['stock.move'].search([('raw_material_production_id','!=',False),('location_id','=',record.location_id.id),('product_id','=',record.product_id.id),('raw_material_production_id.state','in',('confirmed','progress'))])
            done_moves = moves.filtered(lambda x: x.product_uom_qty <= x.reserved_availability)
            moves -= done_moves
            manufacturing_ids = moves.mapped('raw_material_production_id')
            record.mo_ids = [(6,0,manufacturing_ids.ids)]

            total_needed = sum(record.allocate_ids.mapped('total_needed'))
            total_allocated = sum(record.allocate_ids.mapped('total_allocated'))
            record.qty_satisfied = True if total_allocated and (total_needed <= total_allocated) else True if not moves and done_moves else False

            qty = sum(moves.mapped('product_qty'))-sum(moves.mapped('reserved_availability'))
            record.qty_to_consume = qty
            record.qty_to_order = total_allocated

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

    def action_auto_allocate_reels(self):
        reel_allocate_obj = self.env['kits.reel.allocate']
        allocate_line_obj = self.env['kits.reel.allocate.line']
        stock_quant_obj = self.env['stock.quant'].sudo()
        wa_location_id = self.env['stock.warehouse'].search([('system_default','=',True)],limit=1).lot_stock_id
        stock_location_ids = self.env['stock.warehouse'].search([]).mapped('lot_stock_id')

        def _get_allocation_vals(allocate_id,product_id,quant_id,move_id):
            #### Return Allocation line vals
            #### If the lot of Quant is not already assigned OR the quantity of lot it not reserved.
            existing_lines = self.env['stock.move.line'].search([('move_id','!=',False),('product_id','=',record.product_id.id),('state','in',('assigned','done')),('location_id','in',stock_location_ids.ids)])
            existing_lines = existing_lines.filtered(lambda x: x.product_uom_qty > x.qty_done)
            if not allocate_line_obj.search([('lot_id', '=', quant_id.lot_id.id)],limit=1) and quant_id.lot_id not in existing_lines.mapped('lot_id'):
                return {
                    'allocate_id':allocate_id.id,
                    'product_id':product_id.id,
                    'lot_id':quant_id.lot_id.id,
                    'component_line_id':move_id.id,
                    'mo_id':move_id.raw_material_production_id.id,
                    'qty_needed':move_id.product_qty-move_id.reserved_availability,
                    'qty_allocated':quant_id.quantity-quant_id.reserved_quantity,
                    'quant_id':quant_id.id,
                    'location_src_id':quant_id.location_id.id,
                }
            else:
                return False

        for record in self.filtered(lambda x: x.product_id.is_reel):
            allocated_quant_ids = stock_quant_obj
            stock_quant_ids = stock_quant_obj.search([('product_id','=',record.product_id.id),('on_hand','=',True),('quantity','>=',1),('lot_id','!=',False),('lot_id.name','like','Reel%')])

            move_ids = self.env['stock.move'].search([('product_id','=',record.product_id.id),('raw_material_production_id','!=',False),('product_id.is_reel','=',True),('location_id','=',record.location_id.id),('raw_material_production_id.state','in',('confirmed','progress'))])
            move_ids = move_ids.filtered(lambda x: x.product_uom_qty > x.quantity_done) # Remove assigned moves.

            allocate_id = reel_allocate_obj.search([('replenishment_id','=',record.id)],limit=1)
            if not allocate_id:
                allocate_id = reel_allocate_obj.create({
                    'replenishment_id':record.id,
                })

            # Remove all allocated lines.
            if allocate_id.allocate_line_ids:
                allocate_id.allocate_line_ids.unlink()
            
            # Remove all alternate lines
            if allocate_id.alternative_line_ids:
                allocate_id.alternative_line_ids.unlink()
            allocate_lines = []

            # Remove Moves which have Lot assigned already,
            for move_id in move_ids:
                if move_id.move_line_ids and move_id.product_qty <= move_id.reserved_availability:
                    move_ids -= move_id
                else:
                    qty_needed = move_id.product_qty - move_id.reserved_availability
                    qty_allocated = 0

                    if stock_quant_ids:
                        locations = stock_quant_ids.mapped('location_id')

                        if len(locations) > 1:
                            # Find WA/STOCK quants First.
                            stock_quant_ids = stock_quant_ids - allocated_quant_ids
                            wa_stock_ids = stock_quant_ids.filtered(lambda x: x.location_id == wa_location_id)
                            if wa_stock_ids:
                                if (qty_allocated < qty_needed) and ((qty_needed - qty_allocated) <= sum(wa_stock_ids.mapped('quantity'))):
                                    exact_match_stocks = wa_stock_ids.filtered(lambda x: x.quantity == (qty_needed - qty_allocated))
                                    for quant_id in exact_match_stocks:
                                        # Allocate this lot
                                        vals = _get_allocation_vals(allocate_id,record.product_id,quant_id,move_id)
                                        if vals:
                                            allocate_lines.append(vals)
                                            allocated_quant_ids |= quant_id
                                            qty_allocated += qty_needed
                                            break

                            # Exact Matching Lot at INS/MON location.
                            stock_quant_ids = stock_quant_ids - allocated_quant_ids
                            exact_match_ids = stock_quant_ids.filtered(lambda x: x.quantity == (qty_needed-qty_allocated))
                            if (qty_allocated < qty_needed) and len(exact_match_ids):
                                for quant in exact_match_ids:
                                    vals = _get_allocation_vals(allocate_id,record.product_id,quant,move_id)
                                    if vals:
                                        allocate_lines.append(vals)
                                        allocated_quant_ids |= quant
                                        qty_allocated += quant.quantity
                                        break

                            stock_quant_ids = stock_quant_ids - wa_stock_ids
                            for quant in stock_quant_ids.sorted(lambda x: x.quantity - x.reserved_quantity):
                                if (qty_allocated < qty_needed):
                                    vals = _get_allocation_vals(allocate_id,record.product_id,quant,move_id)
                                    if vals:
                                        allocate_lines.append(vals)
                                        allocated_quant_ids |= quant
                                        qty_allocated += quant.quantity
                                elif qty_allocated >= qty_needed:
                                    break
                        
                        elif len(locations) == 1:
                            # Check Need and allocate
                            if qty_allocated < qty_needed:
                                # Exact Matching Lot At WA location.
                                stock_quant_ids = stock_quant_ids - allocated_quant_ids
                                wa_stock_ids = stock_quant_ids.filtered(lambda x: x.location_id == wa_location_id and x.quantity == (qty_needed-qty_allocated))
                                if len(wa_stock_ids):
                                    vals = _get_allocation_vals(allocate_id,record.product_id,wa_stock_ids[0],move_id)
                                    if vals:
                                        allocate_lines.append(vals)
                                        allocated_quant_ids |= wa_stock_ids[0]
                                        qty_allocated += wa_stock_ids[0].quantity
                                
                                # Find -> Other Locations Exact Match Lot
                                stock_quant_ids = stock_quant_ids - allocated_quant_ids
                                exact_match_ids = stock_quant_ids.filtered(lambda x: x.quantity == (qty_needed-qty_allocated))
                                for quant in exact_match_ids:
                                    vals = _get_allocation_vals(allocate_id,record.product_id,quant,move_id)
                                    if vals:
                                        allocate_lines.append(vals)
                                        allocated_quant_ids |= quant
                                        qty_allocated += quant.quantity
                                        break
                                
                                # For not Exact qty Stock
                                stock_quant_ids = stock_quant_ids - allocated_quant_ids
                                for quant in stock_quant_ids.sorted(lambda x: x.quantity - x.reserved_quantity):
                                    if (qty_allocated < qty_needed):
                                        vals = _get_allocation_vals(allocate_id,record.product_id,quant,move_id)
                                        if vals:
                                            allocate_lines.append(vals)
                                            qty_allocated += quant.quantity
                                            allocated_quant_ids |= quant
                                    else:
                                        break
                        else:
                            # Ignore Replenishment
                            pass

            if len(allocate_lines):
                allocate_id.allocate_line_ids = [(0,0,l)for l in allocate_lines]

            record.qty_to_order = sum(allocate_id.allocate_line_ids.mapped('qty_allocated'))+sum(allocate_id.alternative_line_ids.mapped('qty_allocated'))


    def action_open_reel_allocated(self):
        # Open Wizard -> Show Allocated Reel Lines.
        self.ensure_one()
        allocate_id = self.env['kits.reel.allocate'].search([('replenishment_id','=',self.id)],limit=1)
        if allocate_id and allocate_id.id:
            return {
                'name':_('Reels Allocated'),
                'type':'ir.actions.act_window',
                'res_model':'kits.reel.allocate',
                'view_mode':'form',
                'res_id':allocate_id.id,
                'target':'new',
            }

    def action_replenish(self):
        res = super(stock_warehouse_orderpoint,self).action_replenish()
        # for record in self:
            # if record.allocate_id and record.allocate_id.qty_satisfied:
            #     # Allocate the Lots to Component Lines.
            #     pass
        return res
