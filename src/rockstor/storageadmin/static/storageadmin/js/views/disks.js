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

DisksView = Backbone.View.extend({
    events: {
        "click #setup": "setupDisks",
        'click .wipe': 'wipeDisk',
        'click .delete': 'deleteDisk',
        'click .btrfs_wipe': 'btrfsWipeDisk',
        'click .btrfs_import': 'btrfsImportDisk',
        'click .pause': 'pauseDisk',
        'switchChange.bootstrapSwitch': 'smartToggle'
    },

    initialize: function () {
        this.template = window.JST.disk_disks;
        this.disks_table_template = window.JST.disk_disks_table;
        this.collection = new DiskCollection;
        this.collection.on("reset", this.renderDisks, this);
        this.initHandlebarHelpers();
    },

    render: function () {
        this.collection.fetch();
        return this;
    },

    renderDisks: function () {
        // remove existing tooltips
        if (this.$('[rel=tooltip]')) {
            this.$("[rel=tooltip]").tooltip('hide');
        }
        $(this.el).html(this.template({collection: this.collection}));
        this.$("#disks-table-ph").html(this.disks_table_template({
            diskCollection: this.collection.toJSON(),
            collection: this.collection,
            collectionNotEmpty: !this.collection.isEmpty()
        }));

        this.$("#disks-table").tablesorter();
        this.$("[rel=tooltip]").tooltip({
            placement: "right",
            container: '#disks-table'
        });

        //initialize bootstrap switch
        this.$("[type='checkbox']").bootstrapSwitch();
        this.$("[type='checkbox']").bootstrapSwitch('onColor', 'success'); //left side text color
        this.$("[type='checkbox']").bootstrapSwitch('offColor', 'danger'); //right side text color

    },

    setupDisks: function () {
        var _this = this;
        $.ajax({
            url: "/api/disks/scan",
            type: "POST"
        }).done(function () {
            // reset the current page
            _this.collection.page = 1;
            _this.collection.fetch();
        });
    },

    pauseDisk: function (event) {
        var _this = this;
        if (event) event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var diskName = button.data('disk-name');
        if (confirm('Are you sure you want to force the following device into Standby mode ' + diskName + '?')) {
            $.ajax({
                url: '/api/disks/' + diskName + '/pause',
                type: 'POST',
                success: function (data, status, xhr) {
                    _this.render();
                },
                error: function (xhr, status, error) {
                    enableButton(button);
                }
            });
        }
    },

    wipeDisk: function (event) {
        var _this = this;
        if (event) event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var diskName = button.data('disk-name');
        if (confirm('Are you sure you want to completely delete all data on the disk ' + diskName + '?')) {
            $.ajax({
                url: '/api/disks/' + diskName + '/wipe',
                type: 'POST',
                success: function (data, status, xhr) {
                    _this.render();
                },
                error: function (xhr, status, error) {
                    enableButton(button);
                }
            });
        }
    },

    btrfsWipeDisk: function (event) {
        var _this = this;
        if (event) event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var diskName = button.data('disk-name');
        if (confirm('Are you sure you want to erase BTRFS filesystem(s) on the disk ' + diskName + '?')) {
            $.ajax({
                url: '/api/disks/' + diskName + '/btrfs-wipe',
                type: 'POST',
                success: function (data, status, xhr) {
                    _this.render();
                },
                error: function (xhr, status, error) {
                    enableButton(button);
                }
            });
        }
    },

    btrfsImportDisk: function (event) {
        var _this = this;
        if (event) event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var diskName = button.data('disk-name');
        if (confirm('Are you sure you want to automatically import pools, shares and snapshots that may be on the disk ' + diskName + '?')) {
            $.ajax({
                url: '/api/disks/' + diskName + '/btrfs-disk-import',
                type: 'POST',
                success: function (data, status, xhr) {
                    _this.render();
                },
                error: function (xhr, status, error) {
                    enableButton(button);
                }
            });
        }
    },

    deleteDisk: function (event) {
        var _this = this;
        if (event) event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var diskName = button.data('disk-name');
        if (confirm('Are you sure you want to delete the disk ' + diskName + '?')) {
            $.ajax({
                url: '/api/disks/' + diskName,
                type: 'DELETE',
                success: function (data, status, xhr) {
                    _this.render();
                },
                error: function (xhr, status, error) {
                    enableButton(button);
                }
            });
        }
    },

    cleanup: function () {
        this.$("[rel='tooltip']").tooltip('hide');
    },

    initHandlebarHelpers: function () {
        // Helper to display APM value after merger with upstream changes
        // where the above helper is replaced by many smaller ones like this.
        // N.B. untested. Presumably we do {{humanReadableAPM this.apm_level}}
        // in upstream disks_table.jst
        Handlebars.registerHelper('humanReadableAPM', function (apm) {
            var apmhtml = '';
            if (apm == 0 || apm == null) {
                apmhtml = '???';
            } else {
                if (apm == 255) {
                    apmhtml = 'off';
                } else {
                    apmhtml = apm;
                }
            }
            return new Handlebars.SafeString(apmhtml);
        });
        // Simple helper to return true / false on powerState = null or unknown
        // Untested. Presumably we do:
        // {{#if (powerstateNullorUnknown this.power_state)}}
        // in upstream disks_table.jst
        Handlebars.registerHelper('powerStateNullorUnknown', function (pstate) {
            if (pstate == 'unknown' || pstate == null ) {
                return true;
            }
            return false;
        });
        // Simple helper to return true / false on powerState = active/idle
        // Untested. Presumably we do:
        // {{#if (powerStateActiveIdle this.power_state)}}
        // in upstream disks_table.jst
        Handlebars.registerHelper('powerStateActiveIdle', function (pstate) {
            if (pstate == 'active/idle') {
                return true;
            }
            return false;
        });
        Handlebars.registerHelper('displayInfo', function (role) {
            // check for the legacy / pre json formatted role field contents.
            if (role == 'isw_raid_member' || role == 'linux_raid_member') {
                return true;
            }
            // now check if our role is null = db default
            if (role == null) {
                return false;
            }
            // try json conversion and return false if it fails
            // @todo not sure if this is redundant?
            try {
                var roleAsJson = JSON.parse(role);
            } catch (e) {
                return false;
            }
            // We have a json string ie non legacy role info so we can examine:
            if (roleAsJson.hasOwnProperty('mdraid')) {
                // in the case of an mdraid property we are assured it is an
                // mdraid member, the specific type is not important here.
                // Non mdraid members will have no mdraid property.
                return true;
            }
            // In all other cases return false.
            return false;
        });

        Handlebars.registerHelper('displayBtrfs', function (btrfsUid, poolName) {
            if (btrfsUid && _.isNull(poolName)) {
                return true;
            }
            return false;
        });

        Handlebars.registerHelper('checkSerialStatus', function (serial, diskName, opts) {
            // We need to warn the user if any of the following exist as they
            // are all unreliable. The fake-serial- is generated by scan_disks
            // and should have overwritten any null, empty or diskName serial.
            // @todo should be possible to remove null, '' and diskName soon.
            if (serial == null || serial == '' || serial == diskName ||
                serial.substring(0, 12) == 'fake-serial-' ||
                serial == '000000000000') {
                return opts.fn(this);
            }
            return opts.inverse(this);
        });

        Handlebars.registerHelper('humanReadableSize', function (size) {
            return humanize.filesize(size * 1024);
        });
    },

    smartToggle: function (event, state) {
        var disk_name = $(event.target).attr('data-disk-name');
        if (state) {
            this.smartOn(disk_name);
        } else {
            this.smartOff(disk_name);
        }
    },

    smartOff: function (disk_name) {
        var _this = this;
        $.ajax({
            url: '/api/disks/' + disk_name + '/disable-smart',
            type: 'POST',
            success: function (data, status, xhr) {
                _this.render();
            }
        });
    },

    smartOn: function (disk_name) {
        var _this = this;
        $.ajax({
            url: '/api/disks/' + disk_name + '/enable-smart',
            type: 'POST',
            success: function (data, status, xhr) {
                _this.render();
            }
        });
    }
});

// Add pagination
Cocktail.mixin(DisksView, PaginationMixin);
