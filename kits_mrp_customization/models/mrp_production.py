from odoo import models,_


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    def action_show_replenishments(self):
        replenishment_obj = self.env['stock.warehouse.orderpoint'].sudo()
        self.ensure_one()
        replenishment_id = replenishment_obj.search([('product_id','=',self.product_id.id),('location_id','=',self.location_dest_id.id)])
        components_replenishment_ids = replenishment_obj.search([('product_id','in',self.bom_id.bom_line_ids.mapped('product_id').ids),('location_id','=',self.location_src_id.id)])
        return {
            'name':_('Replenishments'),
            'type':'ir.actions.act_window',
            'res_model':'stock.warehouse.orderpoint',
            'view_mode':'tree,form',
            'domain':[('id','in',replenishment_id.ids+components_replenishment_ids.ids)],
            'target':'self',
        }