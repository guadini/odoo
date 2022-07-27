odoo.define('kits_mrp_customization.MOMenu', function (require) {
    "use strict";
    
    var rpc = require('web.rpc');
    const { useModel } = require('web.Model');
    const { Component } = owl;

    class MOMenu extends Component {

        constructor() {
            super(...arguments);
            if(this.env.searchModel.config.modelName){
                this.modelName = this.env.searchModel.config.modelName;
            }
            if($(".o_mo_menu").find(".o_item_option.focus")){
                this.selectedMO = $(".o_mo_menu").find(".o_item_option.focus").text();
            }
            this.mos = this._getMoDetails();
            this.model = useModel('searchModel');
        }

        //---------------------------------------------------------------------
        // Getters
        //---------------------------------------------------------------------

        async _getMoDetails(){
            var mos = await this.rpc({
                route: '/get-mo-ids',
            })
            if(mos){
                this.mosData = JSON.parse(mos)
                return JSON.parse(mos)
            }
        }
        /**
         * @override
         */
        get items() {
            return this.mosData;
        }

        //---------------------------------------------------------------------
        // Handlers
        //---------------------------------------------------------------------

        /**
         * @private
         * @param {OwlEvent} ev
         */
        onMOBySelected(ev) {
            var self = this;
            ev.stopPropagation();
            const { itemId } = ev.detail.payload;
            var domains = {
                'filter':this.model.get("irFilterValues").domain ? this.model.get("irFilterValues").domain : false,
                'groupBy':this.model.get("irFilterValues").context ? this.model.get("irFilterValues").context : false,
            }
            if (itemId) {
                return rpc.query({
                    model: 'mrp.production',
                    method: 'filter_replenishments',
                    args: [itemId,itemId,this.env.action.id,domains],
                }).then(function (action) {
                    if(action){
                        self.trigger('do-action', {
                            action: action,
                            options: {
                                on_close: () => this.trigger('reload'),
                            },
                        });
                    }
                });

            }
        }
        onClearMOFilter(ev){
            var self = this;
            ev.stopPropagation();
            const { itemId } = false;
            var domains = {
                'filter':this.model.get("irFilterValues").domain ? this.model.get("irFilterValues").domain : false,
                'groupBy':this.model.get("irFilterValues").context ? this.model.get("irFilterValues").context : false,
            }
            const clear = true;
            return rpc.query({
                model: 'mrp.production',
                method: 'filter_replenishments',
                args: [itemId, itemId, this.env.action.id, domains, clear],
            }).then(function (action) {
                if(action){
                    self.trigger('do-action', {
                        action: action,
                        options: {
                            on_close: () => this.trigger('reload'),
                        },
                    });
                }
            });

        }
    }

    MOMenu.components = { };
    MOMenu.props = { fields: Object };
    MOMenu.template = "kits_mrp_customization.MOMenu";

    return MOMenu;
});
