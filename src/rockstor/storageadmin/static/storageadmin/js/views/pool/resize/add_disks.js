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

PoolAddDisks = RockstorWizardPage.extend({

    events: {
        'click #checkAll': 'selectAllCheckboxes',
        'click [class="diskid"]': 'clickCheckbox'
    },

    initialize: function () {
        this.disks = new DiskCollection();
        this.disks.setPageSize(100);
        this.template = window.JST.pool_resize_add_disks;
        this.disks_template = window.JST.common_disks_table;
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.disks.on('reset', this.renderDisks, this);
        this.initHandlebarHelpers();
    },

    render: function () {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        $(this.el).html(this.template({
            model: this.model.toJSON(),
            raidLevel: this.model.get('pool').get('raid')
        }));
        this.disks.fetch();
        return this;
    },

    renderDisks: function () {
        var disks = this.disks.filter(function (disk) {
            return disk.available() && disk.isSerialUsable() && disk.isRoleUsable();
        }, this);
        //convert the array elements which are backbone models/collections to JSON object
        for (var i = 0; i < disks.length; i++) {
            disks[i] = disks[i].toJSON();
        }
        this.$('#ph-disks-table').html(this.disks_template({disks: disks}));
        this.$('#add-disks-form').validate({
            rules: {
                'raid-level': {
                    required: true
                }
            },
            messages: {
                'raid-level': 'Please select a RAID level'
            }
        });
    },

    selectAllCheckboxes: function (event) {
        $('#checkAll').change(function () {
            $('input:checkbox').prop('checked', $(this).prop('checked'));
            $('input:checkbox').closest('tr').toggleClass('row-highlight', this.checked);
        });
    },

    clickCheckbox: function (event) {
        $('input:checkbox').change(function () {
            $(this).closest('tr').toggleClass('row-highlight', this.checked);
        });
    },

    /* valid() can be applied on any form element but validate() has to applied on the form.
     * valid calls validate function internally
     */
    save: function () {
        var valid = this.$('#add-disks-form').valid();
        if(!valid){
            return $.Deferred().reject();
        }
        var _this = this;
        var checked = this.$('.diskid:checked').length;
        var diskIds = [];
        this.$('.diskid:checked').each(function (i) {
            diskIds.push($(this).val());
        });
        this.model.set('diskIds', diskIds);
        if (this.model.get('raidChange')) {
            this.model.set('raidLevel', this.$('#raid-level').val());
        }
        return $.Deferred().resolve();
    },

    initHandlebarHelpers: function () {

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

        Handlebars.registerHelper('display_raid_levels', function(){
            var html = '';
            var _this = this;
            // var levels = ['single', 'raid0', 'raid1', 'raid10', 'raid5', 'raid6'];
            var levels = ['single', 'single-dup', 'raid0', 'raid1', 'raid10', 'raid5', 'raid6',
                'raid1c3', 'raid1c4', "raid1-1c3", "raid1-1c4", "raid10-1c3",
                "raid10-1c4", "raid5-1", "raid5-1c3", "raid6-1c3", "raid6-1c4"];
            _.each(levels, function(level) {
                if (_this.raidLevel != level) {
                    html += '<option value="' + level + '">' + level + '</option>';
                }
            });
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('mathHelper', function (value, options) {
            return parseInt(value) + 1;
        });

        Handlebars.registerHelper('humanReadableSize', function (diskSize) {
            return humanize.filesize(diskSize * 1024);
        });
    }
});
