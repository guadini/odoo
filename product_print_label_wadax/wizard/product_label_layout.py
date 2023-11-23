# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(selection_add=[('2.5x5', '2.5 x 5')], ondelete={'2.5x5': 'set default'})

    product_select_ids = fields.Many2many('product.product', 'product_label_layout_product_id_rel', string="Products")

    is_multiple_label_in_paper = fields.Boolean(string='Multiple Label in Paper')

    is_generate_unmarked_line_type = fields.Boolean(string="Generate Unmarked Line Type")

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
            data['is_multiple_label_in_paper'] = self.is_multiple_label_in_paper
            if self.is_multiple_label_in_paper:
                xml_id = 'product_print_label_wadax.report_product_template_label_2_5x5_multiple'
                self.rows = 9
                self.columns = 2
            location_destination = defaultdict(list)
            line_qty_done = defaultdict(list)
            line_purchase_amount = defaultdict(list)
            custom_barcodes = defaultdict(list)
            uom_unit = self.env.ref('uom.product_uom_categ_unit', raise_if_not_found=False)
            product_with_lots = []
            data["has_type"] = True if self.move_line_ids.filtered(lambda l:l.type) else False

            # with type
            # Picking... Transfer Quantities - this will prevail
            if self.picking_quantity in ['picking', 'custom'] and self.move_line_ids and self.move_line_ids.filtered(lambda l:l.type) or self.is_generate_unmarked_line_type:
                move_line_ids = self.move_line_ids.filtered(lambda l:l.type)
                if self.is_generate_unmarked_line_type:
                    move_line_ids = self.move_line_ids
                    data["has_type"] = True
                data['quantity_by_product'] = {k: 1 for k, v in data.get('quantity_by_product').items()}
                for line in move_line_ids:
                    # with type and serial number
                    if line.product_uom_id.category_id == uom_unit:
                        if (line.lot_id or line.lot_name) and int(line.qty_done):
                            location_destination[line.product_id.id].append((line.lot_id.name or line.lot_name, line.location_dest_id.display_name))
                            line_qty_done[line.product_id.id].append(("", line.qty_done))
                            line_purchase_amount[line.product_id.id].append(("", "{:,}".format(round(line.qty_done * sum(line.move_id.purchase_line_id.filtered(lambda p:p.product_id == line.product_id).mapped('price_unit')), 2))))
                            # we intend to print only 1 label
                            custom_barcodes[line.product_id.id].append((line.lot_id.name or line.lot_name, int(1)))
                            continue
                    # with type and no serial number
                    if not (line.lot_id or line.lot_name) and int(line.qty_done):
                        location_destination[line.product_id.id].append(("", line.location_dest_id.display_name))
                        line_qty_done[line.product_id.id].append(("", line.qty_done))
                        line_purchase_amount[line.product_id.id].append(("", "{:,}".format(round(line.qty_done * sum(line.move_id.purchase_line_id.filtered(lambda p:p.product_id == line.product_id).mapped('price_unit')), 2))))
                        continue

            # with no type
            # Picking... Transfer Quantities
            if self.picking_quantity == 'picking' and self.move_line_ids and not self.move_line_ids.filtered(lambda l:l.type):
                move_line_ids = self.move_line_ids
                if self.product_select_ids:
                    move_line_ids = self.move_line_ids.filtered(lambda l: l.product_id in self.product_select_ids)
                    if move_line_ids.filtered(lambda l: not l.lot_id or not l.lot_name):
                        data['quantity_by_product'] = {k: v for k, v in data.get('quantity_by_product').items() if k in self.product_select_ids.ids}
                for line in move_line_ids:
                    if line.product_uom_id.category_id == uom_unit:
                        if (line.lot_id or line.lot_name) and int(line.qty_done):
                            location_destination[line.product_id.id].append((line.lot_id.name or line.lot_name, line.location_dest_id.display_name))
                            custom_barcodes[line.product_id.id].append((line.lot_id.name or line.lot_name, int(line.qty_done)))
                            continue
                    if not (line.lot_id or line.lot_name) and int(line.qty_done):
                        location_destination[line.product_id.id].append(("", line.location_dest_id.display_name ))
                        continue

            # Custom
            if self.picking_quantity == 'custom' and self.move_line_ids and not self.move_line_ids.filtered(lambda l:l.type):
                move_line_ids = self.move_line_ids
                if self.product_select_ids:
                    move_line_ids = self.move_line_ids.filtered(lambda l: l.product_id in self.product_select_ids)
                    if move_line_ids.filtered(lambda l: not l.lot_id or not l.lot_name):
                        data['quantity_by_product'] = {k: v for k, v in data.get('quantity_by_product').items() if k in self.product_select_ids.ids}
                for line in move_line_ids:
                    if line.product_uom_id.category_id == uom_unit:
                        if (line.lot_id or line.lot_name) and int(line.qty_done):
                            location_destination[line.product_id.id].append((line.lot_id.name or line.lot_name, line.location_dest_id.display_name))
                            qty_done = line.qty_done
                            if line.qty_done >= self.custom_quantity:
                                qty_done = self.custom_quantity
                            if line.product_id.id not in product_with_lots:
                                product_with_lots.append(line.product_id.id)
                            custom_barcodes[line.product_id.id].append((line.lot_id.name or line.lot_name, int(qty_done)))
                            continue
                    if not (line.lot_id or line.lot_name) and int(line.qty_done):
                        location_destination[line.product_id.id].append(("", line.location_dest_id.display_name ))
                        continue
                # clear quantity_by_product
                if data.get('quantity_by_product') and product_with_lots:
                    for product in product_with_lots:
                        data.get('quantity_by_product').pop(product)

            if self.picking_quantity == 'picking' and not self.move_line_ids:
                if self.product_tmpl_ids:
                    products = self.product_tmpl_ids.ids
                elif self.product_ids:
                    products = self.product_ids.ids
                else:
                    raise UserError(_("No product to print, if the product is archived please unarchive it before printing its label."))
                data['quantity_by_product'] = {p: 0 for p in products}
            data['custom_barcodes'] = custom_barcodes
            data['location_dest_by_product'] = location_destination
            data['line_qty_done_by_product'] = line_qty_done
            data['line_purchase_amount_by_product'] = line_purchase_amount
            data['location_destination_temp'] = line.picking_id.location_dest_id.display_name
        return xml_id, data

    @api.onchange('print_format')
    def _onchange_product_select_ids(self):
        if self.print_format == "2.5x5" and self.move_line_ids:
            domain = [('id', '=', self.product_ids.ids)]
            return {'domain': {'product_select_ids': domain}}
        else:
            return {'domain': {'product_select_ids': False}}
