# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mt_equipment_manufacturer = fields.Char(string='Manufacturer Equipment')
    mt_ref_manufacturer = fields.Char(string='Manufacturer Ref')
    mt_product_alternative_ids = fields.One2many('mt.product.product', 'mt_product_tmpl_id',
                                                 string="Alternative Products")


class MTProductAlternative(models.Model):
    _name = "mt.product.product"
    _description = 'Product Product'

    mt_product_id = fields.Many2one("product.product", string="Name")
    name = fields.Char(string='Product', related='mt_product_id.name')
    mt_default_code = fields.Char(string='Default Code', related='mt_product_id.default_code')
    mt_qty_available = fields.Float('Product On Hand Quantity', related='mt_product_id.qty_available')
    mt_product_tmpl_id = fields.Many2one("product.template", string="Product Tmpl id")


class ProductProduct(models.Model):
    _inherit = "product.product"

    mt_equipment_manufacturer = fields.Char(string='Manufacturer Equipment')
    mt_ref_manufacturer = fields.Char(string='Manufacturer Ref')
