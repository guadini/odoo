from odoo import models,fields,api,_
from odoo.exceptions import UserError

class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'

    system_default = fields.Boolean('Deafult Warehouse ?')

    @api.constrains('system_default')
    def _check_system_default(self):
        wh_obj = self.env['stock.warehouse']
        for record in self:
            if wh_obj.search([('id','!=',record.id),('system_default','=',True)],limit=1):
                raise UserError(_('There can only be one default Warehouse !'))
