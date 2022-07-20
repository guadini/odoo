odoo.define('kits_mrp_customization.MOMenu', function (require) {
    "use strict";
    const { useModel } = require('web.Model');
    var rpc = require('web.rpc');
    // var ajax = require("web.ajax");

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
            const data = this.model.get('filters').filter(f=>f.isActive === true)
            var filterDomain = [];
            var groupByField = [];
            $.each(data, function (key, value) {
                if (value.type === 'filter') {
                    filterDomain.push(value.domain);
                } else if (value.type === 'groupBy') {
                    groupByField.push(value.fieldName);
                }
            })
            var domains = {
                'filter':filterDomain,
                'groupBy':groupByField
            }
            if (itemId) {
                return rpc.query({
                    model: 'mrp.production',
                    method: 'filter_replenishments',
                    args: [itemId,itemId,this.env.action.id,domains],
                }).then(function(value) {
                    if(value.action){
                        self.trigger('do-action', {
                            action: value.action,
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
            const data = this.model.get('filters').filter(f=>f.isActive === true)
            var filterDomain = [];
            var groupByField = [];
            $.each(data, function (key, value) {
                if (value.type === 'filter') {
                    filterDomain.push(value.domain);
                } else if (value.type === 'groupBy') {
                    groupByField.push(value.fieldName);
                }
            })
            var domains = {
                'filter':filterDomain,
                'groupBy':groupByField
            }
            const clear = true;
            return rpc.query({
                model: 'mrp.production',
                method: 'filter_replenishments',
                args: [itemId, itemId, this.env.action.id, domains, clear],
            }).then(function (value) {
                if(value.action){
                    self.trigger('do-action', {
                        action: value.action,
                        options: {
                            on_close: () => this.trigger('reload'),
                        },
                    });
                }
                if(value.domains){
                }
            });

        }
    }

    MOMenu.components = { };
    MOMenu.props = { fields: Object };
    MOMenu.template = "kits_mrp_customization.MOMenu";

    return MOMenu;
});
