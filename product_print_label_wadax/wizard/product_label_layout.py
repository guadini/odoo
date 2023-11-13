# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(selection_add=[('2.5x5', '2.5 x 5')], ondelete={'2.5x5': 'set default'})

    product_select_ids = fields.Many2many('product.product', 'product_label_layout_product_id_rel', string="Products")

    @api.depends('print_format')
    def _compute_dimensions(self):
        for wizard in self:
            if '2.5x5' in wizard.print_format:
                wizard.columns, wizard.rows = 1, 1
            else:
                return super()._compute_dimensions()

    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()

        if self.print_format == '2.5x5':
            xml_id = 'product_print_label_wadax.report_product_template_label_2_5x5'
            location_destination = defaultdict(str)
            if self.picking_quantity in ['picking', 'custom'] and self.move_line_ids:
                if self.product_select_ids:
                    data['quantity_by_product'] = {k: v for k, v in data.get('quantity_by_product').items() if k in self.product_select_ids.ids}
                for line in self.move_line_ids:
                    location_destination[line.product_id.id] += line.location_dest_id.display_name or line.picking_id.location_dest_id.display_name
                data['location_dest_by_product'] = {p: str(loc) for p, loc in location_destination.items()}
                data['location_destination_temp'] = line.picking_id.location_dest_id.display_name
            if self.picking_quantity == 'picking' and not self.move_line_ids:
                if self.product_tmpl_ids:
                    products = self.product_tmpl_ids.ids
                elif self.product_ids:
                    products = self.product_ids.ids
                else:
                    raise UserError(_("No product to print, if the product is archived please unarchive it before printing its label."))
                data['quantity_by_product'] = {p: 0 for p in products}

        return xml_id, data

    @api.onchange('print_format')
    def _onchange_product_select_ids(self):
        if self.print_format == "2.5x5" and self.move_line_ids:
            domain = [('id', '=', self.product_ids.ids)]
            return {'domain': {'product_select_ids': domain}}
        else:
            return {'domain': {'product_select_ids': False}}
