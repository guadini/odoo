# -*- coding: utf-8 -*-

from odoo import _, models
from odoo.addons.product.report import product_label_report


class ReportProductTemplateLabel_2_5x5(models.AbstractModel):
    _name = 'report.product_print_label_wadax.producttemplatelabel_2_5x5'
    _description = 'Product Label Report'

    def _get_report_values(self, docids, data):
        return product_label_report._prepare_data(self.env, data)
