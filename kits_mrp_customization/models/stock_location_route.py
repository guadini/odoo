from odoo import models,fields,api,_
from odoo.exceptions import UserError

class stock_location_route(models.Model):
    _inherit = 'stock.location.route'

    buying_default = fields.Boolean('Default BUYING ?')
    manufacture_default = fields.Boolean('Default Manufacturing ?')


    @api.constrains('buying_default','manufacture_default')
    def _check_default_route_values(self):
        route_obj = self.env['stock.location.route']
        for record in self:
            if record.buying_default and route_obj.search([('id','!=',record.id),('buying_default','=',True)],limit=1):
                raise UserError(_('There can be only one default BUYING route !'))
            if record.manufacture_default and route_obj.search([('id','!=',record.id),('manufacture_default','=',True)],limit=1):
                raise UserError(_('There can be only one default Manufacture route !'))

