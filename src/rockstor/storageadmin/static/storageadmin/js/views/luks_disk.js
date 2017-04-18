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
        'click #cancel': 'cancel',
        'click #crypttab_selection': 'crypttab_selection_changed'

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
        // and grab the luks_container_uuid if available
        var is_luks;
        // Establish a unique initial LUKS container uuid placeholder first,
        // just in case we end up some how without a LUKS role uuid key entry.
        // Important as we use this value to name keyfiles so must be clearly
        // identifiable and unique. UUID of actual container obviously better.
        var luks_container_uuid = disk_name;
        // While we are inside the LUKS role we can update current_crypttab
        // Assume we have no crypttab entry until we find otherwise.
        var current_crypttab_status = false;
        // Likewise we can also retrieve keyfile existence
        var keyfile_exists = false;
        if (role_obj != null && role_obj.hasOwnProperty('LUKS')) {
            is_luks = true;
            if (role_obj['LUKS'].hasOwnProperty('uuid')) {
                luks_container_uuid = role_obj['LUKS']['uuid'];
            }
            // if we have a crypttab entry, extract it.
            if (role_obj['LUKS'].hasOwnProperty('crypttab')) {
                current_crypttab_status = role_obj['LUKS']['crypttab'];
            }
            if (role_obj['LUKS'].hasOwnProperty('keyfileExists')) {
                keyfile_exists = role_obj['LUKS']['keyfileExists'];
            }
        } else {
            is_luks = false;
        }
        // Populate our crypttab_selection text object along with values.
        // A value of false is used to indicate no crypttab entry exists.
        // see display_crypttab_entry handlebar helper below.
        var crypttab_options = {
            'No auto unlock': false,
            'Manual passphrase via local console': 'none',
            'Auto unlock via keyfile': '/root/keyfile-' + luks_container_uuid
        };
        // additional convenience flag if device is an open LUKS volume.
        var is_open_luks;
        if (role_obj != null && role_obj.hasOwnProperty('openLUKS')) {
            is_open_luks = true;
        } else {
            is_open_luks = false;
        }

        this.current_redirect = current_redirect;
        this.partitions = partitions;
        this.disk_btrfs_uuid = disk_btrfs_uuid;
        this.is_luks = is_luks;
        this.keyfile_exists = keyfile_exists;

        $(this.el).html(this.template({
            diskName: this.diskName,
            serialNumber: serialNumber,
            diskRole: diskRole,
            role_obj: role_obj,
            partitions: partitions,
            current_redirect: current_redirect,
            disk_btrfs_uuid: disk_btrfs_uuid,
            is_luks: is_luks,
            is_open_luks: is_open_luks,
            crypttab_options: crypttab_options,
            current_crypttab_status: current_crypttab_status,
            keyfile_exists: keyfile_exists
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
        this.container_or_volume_mode();
        this.crypttab_selection_changed();
    },

    container_or_volume_mode: function () {
        if (this.is_luks) {
            // LUKS Container mode so show crypttab selection
            this.$('#crypttab_selection_group').show();
        } else {
            // Open LUKS volume mode assumed.
            this.$('#crypttab_selection_group').hide();
        }
    },

    crypttab_selection_changed: function () {
        var crypttab_selected = this.$('#crypttab_selection').val();
        var current_crypttab_status = this.current_crypttab_status;
        if (crypttab_selected !== 'false' && crypttab_selected !== 'none') {
            // Assuming not false and not none is keyfile entry.
            this.show_keyfile_options(true);
        } else {
            this.show_keyfile_options(false);
        }
    },

    show_keyfile_options: function(show) {
        if (show){
            this.$('#current_keyfile_group').show();
            if (!this.keyfile_exists) {
                // this.$('#no_keyfile_group').show();
            }
        } else {
            this.$('#current_keyfile_group').hide();
            //this.$('#no_keyfile_group').hidden();
        }
    },

    initHandlebarHelpers: function () {
        Handlebars.registerHelper('display_luks_container_or_volume', function () {
            var html = '';
            if (this.is_luks) {
                html += 'LUKS container configuration.'
            } else if (this.is_open_luks) {
                html += 'Open LUKS Volume information page.'
            } else {
                html += 'Warning: Non LUKS Device, please report bug on forum.'
            }
            return new Handlebars.SafeString(html);
        });
        Handlebars.registerHelper('display_crypttab_entry', function () {
            // Helper to fill dropdown with crypttab relevant entries,
            // generating dynamically lines of the following format:
            // <option value="false">No auto unlock (No crypttab entry)
            // </option>
            var html = '';
            var current_crypttab_status = this.current_crypttab_status;
            for (var entry in this.crypttab_options) {
                // cycle through the available known entries and construct our
                // drop down html; using 'selected' to indicate current value.
                if (this.crypttab_options[entry] == current_crypttab_status){
                    // we have found our current setting so indicate this by
                    // pre-selecting it
                    html += '<option value="' + this.crypttab_options[entry] + '" selected="selected">';
                    html += entry + ' - active</option>';
                } else {
                    // construct non current entry
                    html += '<option value="' + this.crypttab_options[entry] + '">' + entry + '</option>';
                }
            }
            return new Handlebars.SafeString(html);
        });
        Handlebars.registerHelper('display_keyfile_path', function () {
            var html = '';
            var keyfile = this.current_crypttab_status;
            // first check if we have a keyfile ie non false
            // we shouldn't be called if there isn't one but just in case:
            if (keyfile !== false && keyfile !== 'none') {
                html += 'Keyfile:&nbsp;&nbsp;'
                if (this.keyfile_exists) {
                    // green to denote existing keyfile
                    html += '<span style="color:darkgreen">'
                        + keyfile + '</span>';
                } else {
                    // red to denote missing keyfile
                    html += '<span style="color:darkred">'
                        + keyfile;
                    html += '<p><strong>WARNING: THE CONFIGURED KEY FILE DOES NOT EXIST</strong></span></p>';
                }
            }
            return new Handlebars.SafeString(html);
        });
    },

    cancel: function (event) {
        event.preventDefault();
        this.$('#luks-disk-form :input').tooltip('hide');
        app_router.navigate('disks', {trigger: true});
    }

});




