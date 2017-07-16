/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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

DisksView = RockstorLayoutView.extend({
    events: {
        'click #setup': 'setupDisks',
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
        this.collection.on('reset', this.renderDisks, this);
        this.initHandlebarHelpers();
    },

    render: function () {
        this.collection.fetch();
        return this;
    },

    renderDisks: function () {
        // remove existing tooltips
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }
        $(this.el).html(this.template({collection: this.collection}));
        this.$('#disks-table-ph').html(this.disks_table_template({
            diskCollection: this.collection.toJSON(),
            collection: this.collection,
            collectionNotEmpty: !this.collection.isEmpty()
        }));

        this.$('[rel=tooltip]').tooltip({
            placement: 'right',
            container: '#disks-table'
        });
        this.$('[rel=tooltip-top]').tooltip({
            placement: 'top',
            container: '#disks-table'
        });
        //initialize bootstrap switch
        this.$('[type=\'checkbox\']').bootstrapSwitch();
        this.$('[type=\'checkbox\']').bootstrapSwitch('onColor', 'success'); //left side text color
        this.$('[type=\'checkbox\']').bootstrapSwitch('offColor', 'danger'); //right side text color


      //added ext func to sort over SMART input checkboxes
        $.fn.dataTable.ext.order['dom-checkbox'] = function ( settings, col ) {
            return this.api().column( col, {order:'index'} ).nodes().map( function ( td, i ) {
                return $('input', td).prop('checked') ? '1' : '0';
            });
        };
        //Added columns definition for sorting purpose
        var customs = {
            columnDefs: [
                { type: 'file-size', targets: 2 }
            ],
            columns: [
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                { 'orderDataType': 'dom-checkbox' }
            ]
        };

        this.renderDataTables(customs);
    },

    setupDisks: function () {
        var _this = this;
        $.ajax({
            url: '/api/disks/scan',
            type: 'POST'
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
        var diskId = button.data('disk-id');
        if (confirm('Are you sure you want to force the device into Standby mode ?')) {
            $.ajax({
                url: '/api/disks/' + diskId + '/pause',
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
        var diskId = button.data('disk-id');
        if (confirm('Are you sure you want to completely delete all data on the disk ?')) {
            $.ajax({
                url: '/api/disks/' + diskId + '/wipe',
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
        var diskId = button.data('disk-id');
        if (confirm('Are you sure you want to erase BTRFS filesystem(s) on the disk ?')) {
            $.ajax({
                url: '/api/disks/' + diskId + '/btrfs-wipe',
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
        var diskId = button.data('disk-id');
        if (confirm('Are you sure you want to automatically import pools, shares and snapshots that may be on the disk ?')) {
            $.ajax({
                url: '/api/disks/' + diskId + '/btrfs-disk-import',
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
        var diskId = button.data('disk-id');
        if (confirm('Are you sure you want to delete the disk ?')) {
            $.ajax({
                url: '/api/disks/' + diskId,
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
        this.$('[rel=\'tooltip\']').tooltip('hide');
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

        // Helper to display APM value
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

        Handlebars.registerHelper('isMdraidMember', function (role) {
            // check for the legacy / pre json formatted role field contents.
            if (role == 'isw_raid_member' || role == 'linux_raid_member') {
                return true;
            }
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
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

        // Identify root device by return of true / false.
        // Works by examining the Disk.role field. Based on sister handlebars
        // helper 'isMdraidMember'.
        // true = device hosts the / partition
        // false = root not found on this device
        Handlebars.registerHelper('isRootDevice', function (role) {
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
            // We have a json string ie non legacy role info so we can examine:
            if (roleAsJson.hasOwnProperty('root')) {
                // Only the system device will have a 'root' role entry, we
                // are not interested in the associated value, only the key.
                // Non root members will have no 'root' property.
                return true;
            }
            // In all other cases return false.
            return false;
        });

        // Identify LUKS container by return of true / false.
        // Works by examining the Disk.role field. Based on sister handlebars
        // helper 'isRootDevice'
        Handlebars.registerHelper('isLuksContainer', function (role) {
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
            // We have a json string ie non legacy role info so we can examine:
            if (roleAsJson.hasOwnProperty('LUKS')) {
                // Once a container is created it has an fstype of crypto_LUKS
                // and we attribute it the role of 'LUKS' as a result.
                return true;
            }
            // In all other cases return false.
            return false;
        });

        // Works by examining the Disk.role field and if a LUKS role is found
        // we examine the roles value to see if it reports having an open
        // counterpart ie is this container mapped to an OpenLuks volume
        // which is expressed as unlocked having a true value.
        Handlebars.registerHelper('isLuksContainerUnlocked', function (role) {
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
            // We have a json string ie non legacy role info so we can examine:
            if (roleAsJson.hasOwnProperty('LUKS')) {
                // here we deviate from isLuksContainer by unpacking
                // our LUKS role's value:
                if (roleAsJson['LUKS'].hasOwnProperty('unlocked') == true) {
                    return roleAsJson['LUKS']['unlocked'];
                }
            }
            // In all other cases return false.
            return false;
        });

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

        // Identify bcache backing devices by return of true / false.
        // Works by examining the Disk.role field. Based on sister handlebars
        // helper 'isRootDevice'
        Handlebars.registerHelper('isBcache', function (role) {
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
            // We have a json string ie non legacy role info so we can examine:
            if (roleAsJson.hasOwnProperty('bcache')) {
                // We have a bcache backing device which must now be accessed
                // indirectly via a virtual device, hence we tag it to avoid
                // accidental re-use / delete.
                return true;
            }
            // In all other cases return false.
            return false;
        });

        // Identify bcache caching devices by return of true / false.
        // Works by examining the Disk.role field. Based on sister handlebars
        // helper 'isBcache'
        Handlebars.registerHelper('isBcacheCdev', function (role) {
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
            // We have a json string ie non legacy role info so we can examine:
            if (roleAsJson.hasOwnProperty('bcachecdev')) {
                // We have a bcache caching device which we tag to avoid
                // it's accidental re-use / delete.
                return true;
            }
            // In all other cases return false.
            return false;
        });

        // Identify LVM2_member devices by return of true / false.
        // Works by examining the Disk.role field. Based on sister handlebars
        // helper 'isBcache'
        Handlebars.registerHelper('isLVM2member', function (role) {
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
            // We have a json string ie non legacy role info so we can examine:
            if (roleAsJson.hasOwnProperty('LVM2member')) {
                // We have an LVM2 member (Physical Volume) which we tag to
                // avoid it's accidental re-use / delete.
                return true;
            }
            // In all other cases return false.
            return false;
        });

        // Identify User assigned role disks by return of true / false.
        // Works by examining the Disk.role field. Based on sister handlebars
        // helper 'isBcache'
        // Initially only the redirect role was considered a User assigned
        // role but this was expanded to include LUKS container and bcache
        // backing and caching devices.
        Handlebars.registerHelper('hasUserRole', function (role) {
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
            // We have a json string ie non legacy role info so we can examine:
            // Test for each type of User role, essential a user requested
            // purpose, ie use this partition, or make this a LUKS container.
            // If found we can tag via this helper to avoid it's accidental
            // re-use / deletion.
            // Test for redirection (partition selection) role:
            if (roleAsJson.hasOwnProperty('redirect')) {
                return true;
            }
            // Test for LUKS container role:
            if (roleAsJson.hasOwnProperty('LUKS')) {
                return true;
            }
            // Test for bcache backing or caching roles:
            if (roleAsJson.hasOwnProperty('bcache') ||
                roleAsJson.hasOwnProperty('bcachecdev')) {
                return true;
            }
            // In all other cases return false.
            return false;
        });

        Handlebars.registerHelper('isNullPoolBtrfs', function (btrfsUid, poolName) {
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
        var disk_id = $(event.target).attr('data-disk-id');
        if (state) {
            this.smartOn(disk_id);
        } else {
            this.smartOff(disk_id);
        }
    },

    smartOff: function (disk_id) {
        var _this = this;
        $.ajax({
            url: '/api/disks/' + disk_id + '/disable-smart',
            type: 'POST',
            success: function (data, status, xhr) {
                _this.render();
            }
        });
    },

    smartOn: function (disk_id) {
        var _this = this;
        $.ajax({
            url: '/api/disks/' + disk_id + '/enable-smart',
            type: 'POST',
            success: function (data, status, xhr) {
                _this.render();
            }
        });
    }
});
