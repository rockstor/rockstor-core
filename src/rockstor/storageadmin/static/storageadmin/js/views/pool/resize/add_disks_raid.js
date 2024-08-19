/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>
 *
 * Rockstor is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published
 * by the Free Software Foundation; either version 2 of the License,
 * or (at your option) any later version.
 *
 * Rockstor is distributed in the hope that it will be useful, but
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

PoolAddDisksRaid = RockstorWizardPage.extend({

    initialize: function() {
        this.template = window.JST.pool_resize_add_disks_raid;
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.initHandlebarHelpers();
    },

    save: function() {
        var _this = this;
        var json = this.$('#raid-change-form').getJSON();
        if (json.raidChange == 'yes') {
            this.model.set('raidChange', true);
        } else {
            this.model.set('raidChange', false);
        }
        return $.Deferred().resolve();
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_poolName_raidLevel', function() {
            var html = '';
            html += this.model.get('pool').get('name') + ' is ' + this.model.get('pool').get('raid');
            return new Handlebars.SafeString(html);
        });

    }
});