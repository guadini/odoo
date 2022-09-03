from odoo import models,fields,_
import logging
_logger = logging.getLogger(__name__)


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    def action_show_replenishments(self):
        replenishment_obj = self.env['stock.warehouse.orderpoint'].sudo()
        self.ensure_one()
        replenishment_id = replenishment_obj.search([('product_id','=',self.product_id.id),('location_id','=',self.location_dest_id.id)])
        components_replenishment_ids = replenishment_obj.search([('product_id','in',self.bom_id.bom_line_ids.mapped('product_id').ids),('location_id','=',self.location_src_id.id)])
        return {
            'name':_('Replenishments'),
            'type':'ir.actions.act_window',
            'res_model':'stock.warehouse.orderpoint',
            'view_mode':'tree,form',
            'domain':[('id','in',replenishment_id.ids+components_replenishment_ids.ids)],
            'context':{'mo_id':self.id},
            'target':'self',
        }


    def filter_replenishments(self,itemId,action_id,domains,clear=False):
        Actions = self.env['ir.actions.actions']
        value = False
        domain = []
        if domains.get('filter'):
            domain.extend(eval(domains.get('filter')))

        grouplist = domains.get('groupBy') if domains.get('groupBy') else {}
        try:
            action_id = int(action_id)
        except ValueError:
            try:
                action = self.env.ref(action_id)
                assert action._name.startswith('ir.actions.')
                action_id = action.id
            except Exception:
                action_id = 0   # force failed read
        base_action = Actions.browse([action_id]).sudo().read(['type'])
        if base_action:
            action_type = base_action[0]['type']
            action = self.env[action_type].sudo().browse([action_id]).read()
            if action:
                value = self.kits_clean_action(action[0], env=self.env)
                value['target']='main'
                if clear:
                    value['domain'] = False
                else:
                    manufacturing_order = self.env['mrp.production'].search([('id','=',itemId)])
                    replenishment_obj = self.env['stock.warehouse.orderpoint'].sudo()
                    replenishment_id = replenishment_obj.search([('product_id','=',manufacturing_order.product_id.id),('location_id','=',manufacturing_order.location_dest_id.id)])
                    components_replenishment_ids = replenishment_obj.search([('product_id','in',manufacturing_order.bom_id.bom_line_ids.mapped('product_id').ids),('location_id','=',manufacturing_order.location_src_id.id)])
                    domain.extend([('id','in',replenishment_id.ids+components_replenishment_ids.ids)])
                    value['domain'] = str(domain) if domain else False
                    value['context'] = grouplist if grouplist else  value.get('context',"{}")
            return value


    def kits_clean_action(self,action, env):
        action_type = action.setdefault('type', 'ir.actions.act_window_close')
        if action_type == 'ir.actions.act_window':
            action = self.kits_fix_view_modes(action)

        # When returning an action, keep only relevant fields/properties
        readable_fields = env[action['type']]._get_readable_fields()
        action_type_fields = env[action['type']]._fields.keys()

        cleaned_action = {
            field: value
            for field, value in action.items()
            # keep allowed fields and custom properties fields
            if field in readable_fields or field not in action_type_fields
        }

        # Warn about custom properties fields, because use is discouraged
        action_name = action.get('name') or action
        custom_properties = action.keys() - readable_fields - action_type_fields
        if custom_properties:
            _logger.warning("Action %r contains custom properties %s. Passing them "
                "via the `params` or `context` properties is recommended instead",
                action_name, ', '.join(map(repr, custom_properties)))

        return cleaned_action

    def kits_fix_view_modes(self,action):
        if 'view_mode' in action:
            action['view_mode'] = ','.join(
                mode if mode != 'tree' else 'list'
                for mode in action['view_mode'].split(','))
        action['views'] = [
            [id, mode if mode != 'tree' else 'list']
            for id, mode in action['views']
        ]

        return action
