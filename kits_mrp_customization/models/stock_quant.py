
from odoo import models,api,fields,_
from odoo.exceptions import UserError

class stock_quant(models.Model):
    _inherit = 'stock.quant'

    is_reel = fields.Boolean('Is reel ?',related='product_id.is_reel')
    reel_type = fields.Selection([('reel','Reel'),('strip','Strip'),('stand_alone','Stand Alone Units')],string='Reel Type')

    def action_apply_inventory(self):
        for record in self.filtered(lambda x: x.product_id.tracking == 'lot' and x.is_reel and not x.lot_id):
            if not record.reel_type:
                raise UserError(_('Please select Reel Type for product "{}".'.format(record.product_id.display_name)))
            lot_name = 'Reel-' if record.reel_type == 'reel' else 'Strip-' if record.reel_type == 'strip' else 'SA-'
            lot_name+= str(record.product_id.id)+'-'
            next_auto_number = record.product_id.next_auto_lot_number
            if not next_auto_number:
                next_auto_number = 1
            lot_name += format(next_auto_number,'04')
            # Create Lot- With Custom Lot number
            lot_id = self.env['stock.production.lot'].create({
                'name':lot_name,
                'product_id':record.product_id.id,
                'company_id':self.env.company.id,
            })
            record.lot_id = lot_id
            record.product_id.next_auto_lot_number = next_auto_number+1
        res = super(stock_quant,self).action_apply_inventory()
        return res
    
    def _get_inventory_fields_create(self):
        res = super(stock_quant,self)._get_inventory_fields_create()
        if isinstance(res,list):
            res.append('reel_type')
        return res
    
    def _get_inventory_fields_write(self):
        res = super(stock_quant,self)._get_inventory_fields_write()
        if isinstance(res,list):
            res.append('reel_type')
        return res
