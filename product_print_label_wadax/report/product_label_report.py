# -*- coding: utf-8 -*-
import time

from odoo import _, models
from odoo.addons.product.report import product_label_report


class ReportProductTemplateLabel_2_5x5(models.AbstractModel):
    _name = 'report.product_print_label_wadax.producttemplatelabel_2_5x5'
    _description = 'Product Label Report'

    def _get_report_values(self, docids, data):
        values = product_label_report._prepare_data(self.env, data)
        # handler of report multiple generator
        quantity = sum([value for k, value in data.get('quantity_by_product').items()])
        if quantity <= 100:
            sleep = 5
        if quantity <= 250:
            sleep = 10
        elif quantity <= 300:
            sleep = 15
        elif quantity > 500:
            sleep = 60
        else:
            sleep = 5
        time.sleep(sleep)
        # end of handler delay
        return values
