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
    	Handlebars.registerHelper('displayInfo', function (role) {
    		if(role == 'isw_raid_member' || role == 'linux_raid_member'){
    			return true;
    		}
    		return false;
    	});
    	
    	Handlebars.registerHelper('displayBtrfs', function (btrfsUid, poolName) {
    		if(btrfsUid && _.isNull(poolName)){
    			return true;
    		}
    		return false;
    	});
    	
    	Handlebars.registerHelper('findSerial', function (serial, diskName) {
    		if(serial == null || serial == '' || serial == diskName || serial.length == 48){
    			return true;
    		}
    		return false;
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
