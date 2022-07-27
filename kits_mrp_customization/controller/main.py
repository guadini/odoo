import json
from odoo import http
from odoo.http import request

class Action(http.Controller):
    
    @http.route('/get-mo-ids', type='json',auth="public", website=True)
    def _get_mo_ids(self):
        mos = request.env['mrp.production'].search([('state','in',('confirmed','progress'))])
        # mos = request.env['mrp.production'].search([])
        mo_data = []
        for mo in mos:
            mo_data.append({'id':mo.id,'name':mo.name})
        return json.dumps(mo_data)
