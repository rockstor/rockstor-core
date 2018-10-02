/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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

PoolRemoveDisks = RockstorWizardPage.extend({
    events: {
        'click #checkAll': 'selectAllCheckboxes',
        'click [class="diskid"]': 'clickCheckbox'
    },

    initialize: function() {
        this.disks = new DiskCollection();
        this.disks.setPageSize(100);
        this.template = window.JST.pool_resize_remove_disks;
        this.disks_template = window.JST.common_disks_table;
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.disks.on('reset', this.renderDisks, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        this.disks.fetch();
        return this;
    },

    renderDisks: function() {
        var disks = this.disks.filter(function(disk) {
            return disk.get('pool_name') == this.model.get('pool').get('name');
        }, this);
        //convert the array elements which are backbone models/collections to JSON object
        for (var i = 0; i < disks.length; i++) {
            disks[i] = disks[i].toJSON();
        }
        this.$('#ph-disks-table').html(this.disks_template({
            disks: disks
        }));
    },

    selectAllCheckboxes: function(event) {
        $('#checkAll').change(function() {
            $('input:checkbox').prop('checked', $(this).prop('checked'));
            $('input:checkbox').closest('tr').toggleClass('row-highlight', this.checked);
        });
    },

    clickCheckbox: function(event) {
        $('input:checkbox').change(function() {
            $(this).closest('tr').toggleClass('row-highlight', this.checked);
        });
    },

    save: function() {
        var _this = this;
        var checked = this.$('.diskid:checked').length;
        var diskIds = [];
        this.$('.diskid:checked').each(function(i) {
            diskIds.push($(this).val());
        });
        this.model.set('diskIds', diskIds);
        return $.Deferred().resolve();
    },

    initHandlebarHelpers: function() {

        asJSON = function (role) {
            // Simple wrapper to test for not null and JSON compatibility,
            // returns the json object if both tests pass, else returns false.
            if (role == null) { // db default
                return false;
            }
            // try json conversion and return false if it fails
            // @todo not sure if this is redundant?
            try {
                return JSON.parse(role);
            } catch (e) {
                return false;
            }
        };

        // Identify Open LUKS container by return of true / false.
        // Works by examining the Disk.role field. Based on sister handlebars
        // helper 'isRootDevice'
        Handlebars.registerHelper('isOpenLuks', function (role) {
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
            // We have a json string ie non legacy role info so we can examine:
            if (roleAsJson.hasOwnProperty('openLUKS')) {
                // Once a LUKS container is open it has a type of crypt
                // and we attribute it the role of 'openLUKS' as a result.
                return true;
            }
            // In all other cases return false.
            return false;
        });

        Handlebars.registerHelper('mathHelper', function(value, options) {
            return parseInt(value) + 1;
        });
        Handlebars.registerHelper('humanReadableSize', function(diskSize) {
            return humanize.filesize(diskSize * 1024);
        });
    }
});
