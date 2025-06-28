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

PoolRemoveDisksComplete = RockstorWizardPage.extend({
    initialize: function() {
        this.template = window.JST.pool_resize_remove_disks_complete;
        this.initHandlebarHelpers();
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_breadCrumbs', function() {
            var html = '';
            if (this.model.get('choice') == 'add') {
                html += '<div>Change RAID level?</div><div>Select disks to add</div>';
            } else if (this.model.get('choice') == 'remove') {
                html += '<div>Select disks to remove</div>';
            } else if (this.model.get('choice') == 'raid') {
                html += '<div>Select RAID level and add disks</div>';
            }
            return new Handlebars.SafeString(html);
        });

    }

});