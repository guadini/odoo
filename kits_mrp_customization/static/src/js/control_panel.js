
odoo.define('kits_mrp_customization.ControlPanel', function (require) {
    "use strict";
    const MOMenu = require('kits_mrp_customization.MOMenu');
    const utils = require('web.utils');
    const patch = utils.patch;

    const { useAutofocus } = require('web.custom_hooks');
    const ControlPanel = require('web.ControlPanel');
    const ControlPanelModelExtension = require('web/static/src/js/control_panel/control_panel_model_extension.js')

    const { useState, useContext } = owl.hooks;
    
    patch(ControlPanelModelExtension.prototype, "web.Legacy.ControlPanel", {
        toggleFilter(filterId) {
            const index = this.state.query.findIndex(
                queryElem => queryElem.filterId === filterId
            );
            if (index >= 0) {
                this.state.query.splice(index, 1);
            } else {
                if(this.state.filters[filterId]){
                    var { groupId, type } = this.state.filters[filterId];
                }else{
                    var groupId = '';
                    var type = '';
                }
                if (type === 'favorite') {
                    this.state.query = [];
                }
                this.state.query.push({ groupId, filterId });
            }
        },
        _getGroups() {
            const groups = this.state.query.reduce(
                (groups, queryElem) => {
                    const { groupId, filterId } = queryElem;
                    let group = groups.find(group => group.id === groupId);
                    const filter = this.state.filters[filterId]?this.state.filters[filterId]:filterId;
                    if (!group) {
                        const { type } = filter;
                        group = {
                            id: groupId,
                            type,
                            activities: []
                        };
                        groups.push(group);
                    }
                    group.activities.push(queryElem);
                    return groups;
                },
                []
            );
            groups.forEach(g => this._mergeActivities(g));
            return groups;
        }
    });
    patch(ControlPanel, "kits_mrp_customization.MOMenu", {
        template : "web.Legacy.ControlPanel",
        components: {
            ...ControlPanel.components,
            MOMenu,
        },
    });
    
});
