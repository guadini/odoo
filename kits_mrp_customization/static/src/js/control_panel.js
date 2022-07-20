
odoo.define('kits_mrp_customization.ControlPanel', function (require) {
    "use strict";
    const MOMenu = require('kits_mrp_customization.MOMenu');
    const utils = require('web.utils');
    const patch = utils.patch;
    const ControlPanel = require('web.ControlPanel');
    
    patch(ControlPanel, "kits_mrp_customization.MOMenu", {
        template : "web.Legacy.ControlPanel",
        components: {
            ...ControlPanel.components,
            MOMenu,
        },
    });
    
});
