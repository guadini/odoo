from odoo import models,fields,_


class product_product(models.Model):
    _inherit = 'product.product'

    multilocation_available = fields.Boolean('Available At Multiple Location')
    next_auto_lot_number = fields.Integer('Next Auto Lot Number', default=1)

    def onchange_tracking(self):
        if not self.product_tmpl_id.is_reel and any(product.tracking != 'none' and product.qty_available > 0 for product in self):
            return {
                'warning': {
                    'title': _('Warning!'),
                    'message': _("You have product(s) in stock that have no lot/serial number. You can assign lot/serial numbers by doing an inventory adjustment.")}}
