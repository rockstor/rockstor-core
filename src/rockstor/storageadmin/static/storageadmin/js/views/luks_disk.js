/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
 * This file is part of RockStor.
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

LuksDiskView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel'
    },

        initialize: function () {
        var _this = this;
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.disk_luks_disk;
        this.disks = new DiskCollection();
        this.diskName = this.options.diskName;
        this.dependencies.push(this.disks);
        this.initHandlebarHelpers();
    },

    render: function () {
        this.fetch(this.renderDisksForm, this);
        return this;
    },


    renderDisksForm: function () {
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }
        var _this = this;
        var disk_name = this.diskName;
        // retrieve local copy of disk serial number
        var serialNumber = this.disks.find(function (d) {
            return (d.get('name') == disk_name);
        }).get('serial');
        // retrieve local copy of current disk role
        var diskRole = this.disks.find(function (d) {
            return (d.get('name') == disk_name);
        }).get('role');
        // get the btrfsuuid for this device
        var disk_btrfs_uuid = this.disks.find(function(d) {
            return (d.get('name') == disk_name);
        }).get('btrfs_uuid');
        // get the pool for this device
        var disk_pool = this.disks.find(function(d) {
            return (d.get('name') == disk_name);
        }).get('pool');
        // parse the diskRole json to a local object
        try {
            var role_obj = JSON.parse(diskRole);
        } catch (e) {
                // as we can't convert this drives role to json we assume
                // it's isRoleUsable status by false
            role_obj = null;
        }
        // extract our partitions obj from the role_obj if there is one.
        var partitions;
        if (role_obj != null && role_obj.hasOwnProperty('partitions')) {
            partitions = role_obj.partitions;
        } else {
            // else we set our partitions to be an empty object
            partitions = {};
        }
        // extract any existing redirect role value.
        var current_redirect;
        if (role_obj != null && role_obj.hasOwnProperty('redirect')) {
            // if there is a redirect role then set our current role to it
            current_redirect = role_obj['redirect'];
        } else {
            current_redirect = '';
        }
        // set local convenience flag if device is a LUKS container.
        var is_luks;
        if (role_obj != null && role_obj.hasOwnProperty('LUKS')) {
            is_luks = true;
        } else {
            is_luks = false;
        }

        this.current_redirect = current_redirect;
        this.partitions = partitions;
        this.disk_btrfs_uuid = disk_btrfs_uuid;

        $(this.el).html(this.template({
            diskName: this.diskName,
            serialNumber: serialNumber,
            diskRole: diskRole,
            role_obj: role_obj,
            partitions: partitions,
            current_redirect: current_redirect,
            disk_btrfs_uuid: disk_btrfs_uuid,
            is_luks: is_luks
        }));

        this.$('#luks-disk-form :input').tooltip({
            html: true,
            placement: 'right'
        });

        var err_msg = '';
        var luks_err_msg = function () {
            return err_msg;
        };

        this.$('#luks-disk-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {

            },

            submitHandler: function () {
                var button = $('#role-disk');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var submitmethod = 'POST';
                var posturl = '/api/disks/' + disk_name + '/luks-drive';
                $.ajax({
                    url: posturl,
                    type: submitmethod,
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(_this.$('#luks-disk-form').getJSON()),
                    success: function () {
                        enableButton(button);
                        _this.$('#luks-disk-form :input').tooltip('hide');
                        app_router.navigate('disks', {trigger: true});
                    },
                    error: function (xhr, status, error) {
                        enableButton(button);
                    }
                });
                return false;
            }
        });
    },

    initHandlebarHelpers: function () {
        Handlebars.registerHelper('display_luks_container_or_volume', function () {
            var html = '';
            return new Handlebars.SafeString(html);
        });
    },

    cancel: function (event) {
        event.preventDefault();
        this.$('#luks-disk-form :input').tooltip('hide');
        app_router.navigate('disks', {trigger: true});
    }

});




