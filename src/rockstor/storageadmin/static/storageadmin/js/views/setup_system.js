/*
 *
 * @licstart  The following is the entire license notice for the 
 * JavaScript code in this page.
 * 
 * Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
 * This file is part of RockStor.
 * 
 * RockStor is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published
 * by the Free Software Foundation; either version 2 of the License,
 * or (at your option) any later version.
 * 
 * RockStor is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 * 
 * @licend  The above is the entire license notice
 * for the JavaScript code in this page.
 * 
 */

SetupSystemView = Backbone.View.extend({
    tagName: 'div',

    initialize: function() {
        this.template = window.JST.setup_system;
        this.sysinfo = this.options.sysinfo;
    },

    render: function() {
        this.renderSystemSetup();
        return this;
    },

    renderSystemSetup: function() {
        var _this = this;
        $(this.el).html(this.template({
            sysinfo: this.sysinfo
        }));
        this.$('#set-hostname-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                hostname: 'required'
            },
            submitHandler: function() {
                RockStorGlobals.hostname = _this.$('#hostname').val();
                return false;
            }
        });
    }

});