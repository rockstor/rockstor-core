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
        Handlebars.registerHelper('display_disks_tbody', function () {

            var html = '',
                warning = 'Disk names may change unfavourably upon reboot leading to inadvertent drive reallocation and potential data loss. This error is caused by the source of these disks such as your Hypervisor or SAN. Please ensure that disks are provided with unique serial numbers before proceeding further.';

            this.collection.each(function (disk, index) {
                var diskName = disk.get('name'),
                    diskOffline = disk.get('offline'),
                    diskSize = humanize.filesize(disk.get('size') * 1024),
                    diskModel = disk.get('model'),
                    diskTransport = disk.get('transport'),
                    diskVendor = disk.get('vendor'),
                    smartAvailable = disk.get('smart_available'),
                    poolName = disk.get('pool_name'),
                    serial = disk.get('serial'),
                    btrfsUId = disk.get('btrfs_uuid'),
                    diskParted = disk.get('parted'),
                    smartEnabled = disk.get('smart_enabled'),
                    diskRole = disk.get('role'),
                    smartOptions = disk.get('smart_options'),
                    powerState = disk.get('power_state'),
                    hdparmSetting = disk.get('hdparm_setting'),
                    apmLevel = disk.get('apm_level');

                html += '<tr>';
                html += '<td><a href="#disks/' + diskName + ' "><i class="glyphicon glyphicon-hdd"></i> ' + diskName + '</a>&nbsp';
                if (diskOffline) {
                    html += '<a href="#" class="delete" data-disk-name="' + diskName + '" title="Disk is unusable because it is offline.Click to delete it from the system" rel="tooltip"><i class="glyphicon glyphicon-trash"></i></a>';
                } else if (diskRole == 'isw_raid_member' || diskRole == 'linux_raid_member') {
                    html += '<a href="#" class="raid_member" data-disk-name="' + diskName + '" title="Disk is a mdraid member." rel="tooltip">';
                    html += '<i class="glyphicon glyphicon-info-sign"></i></a>';
                } else if (diskParted) {
                    html += '<a href="#" class="wipe" data-disk-name="' + diskName + '" title="Disk is unusable because it has some other filesystem on it.';
                    html += 'Click to wipe it clean." rel="tooltip"><i class="glyphicon glyphicon-cog"></i></a>';
                } else if (btrfsUId && _.isNull(poolName)) {
                    html += '<a href="#" class="btrfs_wipe" data-disk-name="' + diskName + '" title="Disk is unusable because it has BTRFS filesystem(s) on it.Click to wipe it clean." rel="tooltip">';
                    html += '<i class="fa fa-eraser"></i></a>&nbsp;<a href="#" class="btrfs_import" data-disk-name="' + diskName + '" title="Click to automatically import data (pools, shares and snapshots) on this disk" rel="tooltip">';
                    html += '<i class="glyphicon glyphicon-circle-arrow-down"></i></a>';
                }

                html += '</td>';
                // begin Serial number column
                html += '<td>';
                if (serial == null || serial == '' || serial == diskName || serial.length == 48) {
                    html += '<div class="alert alert-danger">' +
                        '<h4>Warning! Disk serial number is not legitimate or unique.</h4>' + warning + '</div>';
                } else {
                    html += serial;
                    if (serial) {
                        html += '&nbsp;&nbsp;&nbsp;&nbsp;<a href="#disks/blink/' + diskName + '" title="A tool to physically identify the hard drive with this serial number" rel="tooltip"><i class="fa fa-lightbulb-o fa-lg"></i></a>&nbsp';
                    }
                }
                html += '</td>';
                // begin Capacity column
                html += '<td>' + diskSize + '</td>';
                // begin Pool column
                html += '<td>';
                if (!_.isNull(poolName)) {
                    html += '<a href="#pools/' + poolName + '">' + poolName + '</a>';
                }
                html += '</td>';
                // begin Spin Down / Power Status column
                html += '<td>';
                if (powerState == 'unknown' || powerState == null ) {
                    html += '<i class="glyphicon glyphicon-pause"></i>';
                    html += powerState + ' ';
                    html += '<i class="glyphicon glyphicon-hourglass"></i>';
                } else {
                    if (powerState == 'active/idle') {
                        html += '<a href="#" class="pause" data-disk-name="' + diskName + '" title="Force drive into Standby mode." rel="tooltip">';
                        html += '<i class="glyphicon glyphicon-pause"></i></a>';
                    } else {
                        html += '<i class="glyphicon glyphicon-pause"></i>';
                    }
                    html += powerState + ' ';
                    html += '<a href="#disks/spindown/' + diskName + '" title="Click to configure Spin Down." rel="tooltip">';
                    html += '<i class="glyphicon glyphicon-hourglass"></i></a>';
                }
                if (hdparmSetting != null) {
                    html += hdparmSetting;
                }
                html += ' ';
                html += '</td>';
                // begin APM column
                html += '<td>';
                if (apmLevel == 0 || apmLevel == null) {
                    html += '???';
                } else {
                    if (apmLevel == 255) {
                        html += 'off';
                    } else {
                        html += apmLevel;
                    }
                }
                html += ' ';
                html += '</td>';
                // begin Model column
                html += '<td>' + diskModel + '</td>';
                // begin Transport column
                html += '<td>' + diskTransport + '</td>';
                // begin Vendor column
                html += '<td>' + diskVendor + '</td>';
                // begin smart table data cell contents
                html += '<td>';
                if (smartOptions != null) {
                    html += smartOptions + ' ';
                } else {
                    html += ' ';
                }
                html += '<a href="#disks/smartcustom/' + diskName + '" title="Click to add/edit Custom SMART options. Rescan to Apply." rel="tooltip">';
                html += '<i class="glyphicon glyphicon-pencil"></i></a> ';
                if (!smartAvailable) {
                    html += 'Not Supported</td>';
                } else {
                    if (smartEnabled) {
                        html += '<input type="checkbox" data-disk-name="' + diskName + '" data-size="mini" checked></input>';
                    } else {
                        html += '<input type="checkbox" data-disk-name="' + diskName + '" data-size="mini"></input>';
                    }
                    html += '</td>';
                }
                html += '</tr>';
            });
            return new Handlebars.SafeString(html);
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
