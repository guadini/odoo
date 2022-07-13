odoo.define('kits_mrp_customization.MOMenu', function (require) {
    "use strict";
    // const CustomGroupByItem = require('web.CustomGroupByItem');
    const { useModel } = require('web.Model');

    const { Component } = owl;

    class MOMenu extends Component {

        constructor() {
            super(...arguments);
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
            ev.stopPropagation();
            const { itemId } = ev.detail.payload;
            if (itemId) {
                this.model.dispatch('toggleFilter', itemId);
            }
        }
    }

    // MOMenu.components = { CustomGroupByItem };
    MOMenu.components = { };
    MOMenu.props = { fields: Object };
    MOMenu.template = "kits_mrp_customization.MOMenu";

    return MOMenu;
});
