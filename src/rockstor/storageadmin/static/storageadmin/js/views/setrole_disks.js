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

SetroleDiskView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel',
        'click #redirect_part': 'redirect_part_changed',
        'click #delete_tick': 'delete_tick_toggle'
    },

    initialize: function () {
        var _this = this;
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.disk_setrole_disks;
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
            this.$("[rel=tooltip]").tooltip('hide');
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
                console.log('diskRole in setrole_disks.js failed json convert')
                role_obj = null;
            }
        // extract our partitions obj from the role_obj if there is one.
        if (role_obj != null && role_obj.hasOwnProperty('partitions')) {
            var partitions = role_obj.partitions;
        } else {
            // else we set our partitions to be an empty object
            var partitions = {};
        }
        // extract any existing redirect role value.
        if (role_obj != null && role_obj.hasOwnProperty('redirect')) {
            // if there is a redirect role then set our current role to it
            var current_redirect = role_obj['redirect'];
        } else {
            var current_redirect = '';
        }
        this.current_redirect = current_redirect;

        $(this.el).html(this.template({
            diskName: this.diskName,
            serialNumber: serialNumber,
            diskRole: diskRole,
            role_obj: role_obj,
            partitions: partitions,
            current_redirect: current_redirect,
            disk_btrfs_uuid: disk_btrfs_uuid
        }));

        this.$('#add-role-disk-form :input').tooltip({
            html: true,
            placement: 'right'
        });

        var err_msg = '';
        var role_err_msg = function () {
            return err_msg;
        };

        $.validator.addMethod('validateRedirect', function (value) {
            var redirect_role = $('#redirect_part').val();
            // check to see if we are attempting to change an existing btrfs
            // redirect, if so refuse the action and explain why.
            if ((partitions[current_redirect] == 'btrfs') && (redirect_role != current_redirect)) {
                err_msg = 'Existing btrfs partition found; if you wish to ' +
                    'use the redirect role either select this btrfs partition ' +
                    'or remove the btrfs partition or whipe the whole disk and re-assign.' +
                    'Redirecting is only supported to a non btrfs partiton when ' +
                    'no btrfs partition exists on the same device.';
                return false;
            }
            return true;
        }, role_err_msg);

        $.validator.addMethod('validateDeleteTick', function (value) {
            var delete_tick = $('#delete_tick');
            var redirect_role = $('#redirect_part').val();
            if (delete_tick.prop('checked')) {
                if (redirect_role != current_redirect) {
                    err_msg = 'Please first submit your new Redirect Role ' +
                        'before selecting delete, or Cancel and start over.';
                    return false;
                } else {
                    // we have redirect_role == current_redirect
                    // now check if the device is in an active Rockstor pool
                    // Un-remark next line to test backend validation of same.
                    // disk_pool = null;
                    if (disk_pool != null) {
                        // device is part of Rockstor pool, reject wipe request
                        err_msg = "Selected device is part of a Rockstor " +
                            "managed pool. Use Pool resize to remove it from " +
                            "the relevant pool which in turn will wipe it's " +
                            "filesystem.";
                        return false;
                    }
                }
            }
            return true;
        }, role_err_msg);

        this.$('#add-role-disk-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                // redirect_part: 'required',
                redirect_part: 'validateRedirect',
                delete_tick: 'validateDeleteTick'
            },

            submitHandler: function () {
                var button = $('#role-disk');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var submitmethod = 'POST';
                var posturl = '/api/disks/' + disk_name + '/role-drive';
                $.ajax({
                    url: posturl,
                    type: submitmethod,
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(_this.$('#add-role-disk-form').getJSON()),
                    success: function () {
                        enableButton(button);
                        _this.$('#add-role-disk-form :input').tooltip('hide');
                        app_router.navigate('disks', {trigger: true});
                    },
                    error: function (xhr, status, error) {
                        enableButton(button);
                    }
                });
                return false;
            }
        });
        this.delete_tick_toggle();
        this.redirect_part_changed();
    },

    delete_tick_toggle: function () {
        var delete_tick = this.$('#delete_tick');
        if (delete_tick.prop('checked')) {
            this.$('#delete_tick_warning').css('visibility', 'visible');
        } else {
            this.$('#delete_tick_warning').css('visibility', 'hidden');
        }
    },

    redirect_part_changed: function() {
        var part_selected = this.$('#redirect_part').val();
        var current_redirect = this.current_redirect;
        console.log('redirect_part_changed, part_selected = ' + part_selected);
        console.log('current_redirect=' + current_redirect);
        if (part_selected != current_redirect) {
            if (this.$('#delete_tick').prop('checked')) {
                // un-tick to reassure user & remove the warning via tick_toggle
                // Un-Remark the following line to test backend redirect
                // & wipe validation by enabling their combination in the UI.
                this.$('#delete_tick').removeAttr('checked');
                this.delete_tick_toggle();
            }
            // now disable delete_tick to avoid it being activated on an
            // as yet uninitialized / un-applied redirect.
            this.$('#delete_tick').attr('disabled', true);
        } else {
            console.log('part_selected == current_redirect =' + current_redirect);
            // we are showing the current redirect so re-enable the delete_tick
            this.$('#delete_tick').removeAttr('disabled');
            this.delete_tick_toggle();
        }
    },

    initHandlebarHelpers: function () {
        // helper to fill dropdown with drive partitions and their fstype
        // eg by generating dynamicaly lines of the following
        // <option value="virtio-serial-6-part-2">part2 (ntfs)</option>
        Handlebars.registerHelper('display_disk_partitions', function () {
            var html = '';
            // Add our 'use whole disk' option which will allow for an existing
            // redirect to be removed, preparing for whole disk btrfs.
            // Also serves to indicate no redirect role in operation.
            console.log('disk_btrfs_uuid=' + this.disk_btrfs_uuid);
            console.log('partitions=' + this.partitions);
            if ( (this.disk_btrfs_uuid != null) && (_.isEmpty(this.partitions)) ) {
                var uuid_message = 'btrfs'
            } else {
                var uuid_message = 'None';
            }
            var selected = '';
            if (this.current_redirect == '') {
                var selected = ' selected="selected"';
            }
            html += '<option value=""' + selected + '> Whole Disk (' + uuid_message + ')';
            // if no current redirect role then select whole disk entry and
            // give indication of this " - active"
            if (selected != '') {
                html += ' - active';
            }
            // close the "Whole Disk" option
            html += '</option>';
            console.log('current html=' + html);
            // loop through this devices partitions and mark one as selected
            // if it equals the current redirect role, hence defaulting to the
            // partition of the current redirect settings.
            // for each partition in our partitions set our selector value as
            // the partition name and add it's value which is the fstype.
            // Default to the partition matching a current redirect, if any.
            for (var part in this.partitions) {
                var active_redirect = false;
                if (part == this.current_redirect) {
                    html += '<option value="' + part + '" selected="selected">';
                    active_redirect = true;
                } else {
                    html += '<option value="' + part + '">';
                }
                // add our fstype held as the value against this partition
                var partition_fstype = this.partitions[part];
                if (partition_fstype == '') {
                    partition_fstype = 'None';
                }
                // strip the last part of our by-id name to get our partition
                // ie virtio-serial-part2 but we want part2
                var short_part_name = part.split('-').slice(-1)[0];
                html += short_part_name + ' (' + partition_fstype + ')';
                // if this is our active setting then indicate in text
                if (active_redirect) {
                    html += ' - active'
                }
                // end this partition option
                html += '</option>';
            }
            console.log('final html=' + html);
            return new Handlebars.SafeString(html);
        });
    },

    cancel: function (event) {
        event.preventDefault();
        this.$('#add-spindown-disk-form :input').tooltip('hide');
        app_router.navigate('disks', {trigger: true});
    }

});
