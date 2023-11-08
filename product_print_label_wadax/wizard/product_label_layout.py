# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(selection_add=[('2.5x5', '2.5 x 5')], ondelete={'2.5x5': 'set default'})

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
    
            if self.picking_quantity == 'picking' and self.move_line_ids:
                data['location_dest'] = self.move_line_ids.picking_id.location_dest_id.display_name
            if self.picking_quantity == 'picking' and not self.move_line_ids:
                if self.product_tmpl_ids:
                    products = self.product_tmpl_ids.ids
                elif self.product_ids:
                    products = self.product_ids.ids
                else:
                    raise UserError(_("No product to print, if the product is archived please unarchive it before printing its label."))
                data['quantity_by_product'] = {p: 0 for p in products}

        return xml_id, data
