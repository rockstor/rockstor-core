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

SetroleDiskView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel',
        'click #redirect_part': 'redirect_part_changed',
        'click #delete_tick': 'delete_tick_toggle',
        'click #luks_tick': 'luks_tick_toggle'
    },

    initialize: function () {
        var _this = this;
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.disk_setrole_disks;
        this.disks = new DiskCollection();
        this.diskId = this.options.diskId;
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
        var disk_id = this.diskId;
        var disk_obj = this.disks.find(function(d) {
            return (d.get('id') == disk_id);
        });
        var serialNumber = disk_obj.get('serial');
        var diskRole = disk_obj.get('role');
        var disk_btrfs_uuid = disk_obj.get('btrfs_uuid');
        var disk_pool = disk_obj.get('pool');
        var diskName = disk_obj.get('name');
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
        // set local convenience flag if device is a LUKS container and note
        // if it's unlocked or not.
        var is_luks = false;
        // Default to appearing as if we are unlocked if we fail for
        // some reason to retrieve the obligatory unlocked flag. This
        // way we fail safe as unlocked containers can't be deleted.
        var is_unlocked = true;
        // While we are inside the LUKS role we can update current_crypttab
        // Assume we have no crypttab entry until we find otherwise.
        var current_crypttab_status = false;
        if (role_obj != null && role_obj.hasOwnProperty('LUKS')) {
            is_luks = true;
            // if we have an unlocked entry, extract it.
            if (role_obj['LUKS'].hasOwnProperty('unlocked')) {
                is_unlocked = role_obj['LUKS']['unlocked'];
            }
            // if we have a crypttab entry, extract it.
            if (role_obj['LUKS'].hasOwnProperty('crypttab')) {
                current_crypttab_status = role_obj['LUKS']['crypttab'];
            }
        }
        // additional convenience flag if device is an open LUKS volume.
        var is_open_luks;
        if (role_obj !== null && role_obj.hasOwnProperty('openLUKS')) {
            is_open_luks = true;
        } else {
            is_open_luks = false;
        }
        // convenience flag to indicate if a device is an LVM2 member.
        var is_lvm2member;
        if (role_obj !== null && role_obj.hasOwnProperty('LVM2member')) {
            is_lvm2member = true;
        }

        this.current_redirect = current_redirect;
        this.partitions = partitions;
        this.disk_btrfs_uuid = disk_btrfs_uuid;
        this.is_open_luks = is_open_luks;
        this.is_luks = is_luks;
        this.is_unlocked = is_unlocked;
        this.current_crypttab_status = current_crypttab_status;
        this.is_lvm2member = is_lvm2member;

        $(this.el).html(this.template({
            diskName: diskName,
            serialNumber: serialNumber,
            diskRole: diskRole,
            role_obj: role_obj,
            partitions: partitions,
            current_redirect: current_redirect,
            disk_btrfs_uuid: disk_btrfs_uuid,
            is_luks: is_luks,
            is_open_luks: is_open_luks,
            is_unlocked: is_unlocked,
            current_crypttab_status: current_crypttab_status,
            is_lvm2member: is_lvm2member
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
            var redirect_changed = false;
            if (redirect_role != current_redirect) {
                redirect_changed = true;
            }
            var redirect_support_msg = 'Redirection is only supported to ' +
                'a non btrfs partition when no btrfs partition exists on ' +
                'the same device.';
            // check to see if we are attempting to change an existing btrfs
            // redirect, if so refuse the action and explain why.
            if ((partitions[current_redirect] == 'btrfs') && redirect_changed) {
                err_msg = 'Active btrfs partition redirect found; if you ' +
                    'wish to change this redirect role first wipe the ' +
                    'partition and then re-assign. ' + redirect_support_msg;
                return false;
            }
            // check to see if an exiting btrfs partition exists and is not
            // the selected option after a change. As we default to whole disk
            // the 'after a change' clause allows for whole disk wipe.
            if ((disk_btrfs_uuid != null) && (partitions[redirect_role] != 'btrfs') && redirect_changed) {
                err_msg = 'Existing btrfs partition found; if you wish to ' +
                    'use the redirect role either select this btrfs partition ' +
                    'and import/use it, or wipe it (or the whole disk) and ' +
                    'then re-assign. ' + redirect_support_msg;
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
                        err_msg = 'Selected device is part of a Rockstor ' +
                            'managed pool. Use Pool resize to remove it from ' +
                            'the relevant pool which in turn will wipe it\'s ' +
                            'filesystem.';
                        return false;
                    }
                    if (is_luks && is_unlocked) {
                        // We block attempts to wipe unlocked LUKS containers
                        // as a safe guard, we have no direct way to know if
                        // they are backing any pool members but they are
                        // never-the-less active if open and a wipe would /
                        // should fail if we attempted it so just block and
                        // advise within the front end.
                        err_msg = 'Wiping an unlocked LUKS container is not ' +
                            'supported. First close the containers Open ' +
                            'LUKS Volume counterpart and ensure "No auto ' +
                            'unlock" is the active "Boot up configuration"';
                        return false;
                    }
                    // We shouldn't need this check but just in case our hide
                    // of the wipe link on the LUKS config page that lead the
                    // user hear has been circumvented.
                    if (current_crypttab_status !== false) {
                        err_msg = 'Wiping a LUKS container with an ' +
                            'existing crypttab entry is not supported. ' +
                            'First ensure "No auto unlock" is the active ' +
                            'selection on the LUKS configuration page.';
                        return false;
                    }
                }
            }
            return true;
        }, role_err_msg);

        $.validator.addMethod('validateLuksPassphrases', function (value) {
            var luks_tick = $('#luks_tick');
            var luks_pass_one = $('#luks_pass_one').val();
            var luks_pass_two = $('#luks_pass_two').val();
            if (luks_tick.prop('checked')) {
                if (luks_pass_one == '') {
                    err_msg = 'An empty LUKS passphrase is not supported';
                    return false;
                }
                if (luks_pass_one.length < 14) {
                    err_msg = 'LUKS passphrase should be at least 14 ' +
                        'characters long.';
                    return false;
                }
                if (luks_pass_one != luks_pass_two) {
                    err_msg = 'LUKS passphrases do not match, please try ' +
                        'again.';
                    return false;
                }
                // Reject non ASCII 7-bit & control characters ie only accept:
                // !"#$%&'()*+,-./0-9:;<=>?@A-Z[\]^_`a-z{|}~ plus space.
                // Equates to Decimal (32-126) or Hex (0x20-0x7E)
                // to include DEL (delete) char increase range to 7F.
                if (/^[\x20-\x7E]+$/.test(luks_pass_one) == false) {
                    err_msg = 'Invalid non ASCII(32-126) 7-bit character entered';
                    return false;
                }
            }
            return true;
        }, role_err_msg);

        this.$('#add-role-disk-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                redirect_part: 'validateRedirect',
                delete_tick: 'validateDeleteTick',
                luks_pass_one: 'validateLuksPassphrases'
            },

            submitHandler: function () {
                var button = $('#role-disk');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var submitmethod = 'POST';
                var posturl = '/api/disks/' + disk_id + '/role-drive';
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
        this.luks_tick_toggle();
        this.luks_options_show_hide();
    },

    delete_tick_toggle: function () {
        var delete_tick = this.$('#delete_tick');
        if (delete_tick.prop('checked')) {
            // show delete warning
            this.$('#delete_tick_warning').show();
            // un-tick and hide LUKS tick and passwords
            this.$('#luks_tick').removeAttr('checked');
            this.$('#luks_passwords').hide();
            this.$('#luks_options').hide();
        } else {
            // hide delete warning
            this.$('#delete_tick_warning').hide();
            // show LUKS options if appropriate
            // this.$('#luks_options').show();
            this.luks_options_show_hide();
        }
    },

    redirect_part_changed: function() {
        var part_selected = this.$('#redirect_part').val();
        var current_redirect = this.current_redirect;
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
            // we are showing the current redirect so re-enable the delete_tick
            this.$('#delete_tick').removeAttr('disabled');
            this.delete_tick_toggle();
        }
    },

    luks_tick_toggle: function () {
        var luks_tick = this.$('#luks_tick');
        if (luks_tick.prop('checked')) {
            // un-tick delete and hide it
            this.$('#delete_tick').removeAttr('checked');
            this.$('#delete_tick_group').hide();
            // show password entry and delete warning
            this.$('#luks_passwords').show();
            this.$('#delete_tick_warning').show();
        } else {
            // show delete tick
            this.$('#delete_tick_group').show();
            // hide password entry and delete warning
            this.$('#luks_passwords').hide();
            this.$('#delete_tick_warning').hide();
        }
    },

    luks_options_show_hide: function () {
        var luks_tick = this.$('#luks_tick');
        // Only enable and show the LUKS formatting options if there are no
        // partitions and we have no existing btrfs, imported or otherwise.
        // The latter clause is to covers whole disk btrfs but doesn't cover
        // non btrfs whole disk filesystems (these are unusual).
        // Also guard against creating a LUKS container within an open LUKS
        // volume as this is both redundant and not supported as we would then
        // have a device that was both a LUKS volume and a LUKS container.
        // Confusing and unnecessary. Likewise we only show LUKS format
        // options is we are not already a LUKS container (is_luks). This
        // helps to avoid some potential confusion when re-formatting a LUKS
        // container as it forces a traditional wipe first.
        if (_.isEmpty(this.partitions) && this.disk_btrfs_uuid == null
            && this.is_open_luks !== true && this.is_luks !== true
            && this.is_lvm2member !== true) {
            luks_tick.removeAttr('disabled');
            this.$('#luks_options').show();
        } else {
            luks_tick.attr('disabled', true);
            this.$('#luks_options').hide();
        }
    },

    initHandlebarHelpers: function () {
        // helper to fill dropdown with drive partitions and their fstype
        // eg by generating dynamically lines of the following format:
        // <option value="virtio-serial-6-part-2">part2 (ntfs)</option>
        Handlebars.registerHelper('display_disk_partitions', function () {
            var html = '';
            // Add our 'use whole disk' option which will allow for an existing
            // redirect to be removed, preparing for whole disk btrfs.
            // Also serves to indicate no redirect role in operation.
            var whole_disk_fstype;
            if ((this.disk_btrfs_uuid != null) && (_.isEmpty(this.partitions))) {
                whole_disk_fstype = 'btrfs';
            } else if (this.is_luks) {
                whole_disk_fstype = 'LUKS';
            } else if (this.is_lvm2member) {
                whole_disk_fstype = 'LVM2_member';
            } else {
                whole_disk_fstype = 'None';
            }
            var selected = '';
            if (this.current_redirect == '') {
                selected = ' selected="selected"';
            }
            html += '<option value=""' + selected + '> Whole Disk (' + whole_disk_fstype + ')';
            // if no current redirect role then select whole disk entry and
            // give indication of this " - active"
            if (selected != '') {
                html += ' - active';
            }
            // close the "Whole Disk" option
            html += '</option>';
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
                    html += ' - active';
                }
                // end this partition option
                html += '</option>';
            }
            return new Handlebars.SafeString(html);
        });
    },

    cancel: function (event) {
        event.preventDefault();
        this.$('#add-role-disk-form :input').tooltip('hide');
        app_router.navigate('disks', {trigger: true});
    }

});
