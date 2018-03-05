/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
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

AddPoolView = Backbone.View.extend({
    events: {
        'click #js-cancel': 'cancel',
        'change [class="disk"]': 'updateSelection',
        'change #checkAll': 'selectAllCheckboxes',
        'change #raid_level': 'renderSummary'
    },

    initialize: function () {
        this.template = window.JST.pool_add_pool_template;

        // dont paginate disk selection table for now
        //this.pagination_template = window.JST.common_pagination;
        // we do this as a workaround until we fix the add pool form properly.
        // with default page size, only upto 15 drives are shown.
        // @todo: fix this properly.
        this.collection = new DiskCollection();
        this.collection.setPageSize(100);
        this.filteredCollection = new DiskCollection();
        this.collection.on('reset', this.renderDisks, this);
        this.initHandlebarHelpers();
        _.bindAll(this, 'submit');

        // Also respond to selection changes using a collection:
        this.selectedDisks = new DiskCollection();
        this.selectedDisks.on('reset', this.renderSummary, this);

        // Validation
        var err_msg = 'Incorrect number of disks.';
        var raid_err_msg = function() {
            return err_msg;
        };

        $.validator.addMethod('validatePoolName', function (pool_name) {
            if (/^[A-Za-z0-9_.-]+$/.test(pool_name) == false) {
                err_msg = 'Invalid characters in Pool name.';
                return false;
            }
            return true;
        }, raid_err_msg);

        $.validator.addMethod('validateRaid', function (raid_level) {
            var n = $('input:checked.disk').length;
            var min = 1;
            if (raid_level == 'single') {
                err_msg = 'At least one disk is required.';
            } else {
                if (_.contains(['raid0', 'raid1', 'raid5'], raid_level))
                    min = 2;
                else if (raid_level == 'raid6')
                    min = 3;
                else if (raid_level == 'raid10')
                    min = 4;
                err_msg = $.validator.format(
                    'At least {0} disks are required for {1} mode.',
                    min, raid_level
                );
            }
            return n >= min;
        }, raid_err_msg);
    },

    render: function () {
        this.collection.fetch();
        return this;
    },

    renderDisks: function () {
        $(this.el).empty();
        var _this = this;
        this.filteredCollection = _.reject(this.collection.models, function (disk) {
            return _.isNull(disk.get('pool')) &&
                !disk.get('offline') && _.isNull(disk.get('btrfs_uuid')) &&
                isSerialUsable(disk.get('serial')) &&
                isRoleUsable(disk.get('role'));
        });

        // N.B. isSerialUsable() and isRoleUsable() are duplicated in the
        // Backbone Disk model as the property isSerialUsable() isRoleUsable()
        // storageadmin/static/storageadmin/js/models/models.js
        // It would be better not to have this duplication if possible.
        function isSerialUsable(diskSerialNumber) {
            // Simple disk serial validator to return true unless the given disk
            // serial number looks fake or untrustworthy.
            // In the case of a repeat or missing serial scan_disks() will use a
            // placeholder of fake-serial-<uuid4> so look for this signature text.
            if (diskSerialNumber.substring(0, 12) == 'fake-serial-') {
                return false;
            }
            // Observed in a 4 bay ORICO USB 3.0 enclosure that obfuscated all it's
            // disk serial numbers and replaced them with '000000000000'.
            if (diskSerialNumber == '000000000000') {
                return false;
            }
            return true;
        }

        // Using the disk.role system we can filter drives on their usability.
        // Roles for inclusion: openLUKS containers
        // Roles to dismiss: LUKS containers, mdraid members, the 'root' role,
        // and partitions (if not accompanied by a redirect role).
        // Defaults to reject (return false)
        function isRoleUsable(role) {
            // check if our role is null = db default
            // A drive with no role shouldn't present a problem for use.
            if (role == null) {
                return true;
            }
            // try json conversion and return false if it fails
            // @todo not sure if this is redundant?
            try {
                var roleAsJson = JSON.parse(role);
            } catch (e) {
                // as we can't read this drives role we play save and exclude
                // it's isRoleUsable status by false
                return false;
            }
            // We have a json object, look for acceptable roles in the keys
            //
            // Accept use of 'openLUKS' device
            if (roleAsJson.hasOwnProperty('openLUKS')) {
                return true;
            }
            // Accept use of 'partitions' device but only if it is accompanied
            // by a 'redirect' role, ie so there is info to 'redirect' to the
            // by-id name held as the value to the 'redirect' role key.
            if (roleAsJson.hasOwnProperty('partitions') && roleAsJson.hasOwnProperty('redirect')) {
                // then we need to confirm if the fstype of the redirected
                // partition is "" else we can't use it
                if (roleAsJson.partitions.hasOwnProperty(roleAsJson.redirect)) {
                    if (roleAsJson.partitions[roleAsJson.redirect] == '') {
                        return true;
                    }
                }
            }
            // In all other cases return false, ie:
            // reject roles of for example root, mdraid, LUKS,
            // partitioned (when not accompanied by a valid redirect role) etc
            return false;
        }

        this.collection.remove(this.filteredCollection);
        $(_this.el).append(_this.template({
            disks: this.collection.toJSON(),
        }));
        this.renderSummary();

        this.$('#disks-table').tablesorter({
            headers: {
                // assign the first column (we start counting zero)
                0: {
                    // disable it by setting the property sorter to false
                    sorter: false
                },
                // assign the third column (we start counting zero)
                3: {
                    // disable it by setting the property sorter to false
                    sorter: false
                }
            }
        });

        this.$('#add-pool-form input').tooltip({placement: 'right'});

        this.$('#raid_level').tooltip({
            html: true,
            placement: 'right',
            title: 'Software RAID level<br><strong>Single</strong>: No RAID - one or more devices (-m dup enforced).<br><strong>Raid0</strong>, <strong>Raid1</strong>, <strong>Raid10</strong>, and the parity based <strong>Raid5</strong> & <strong>Raid6</strong> levels are all similar to conventional raid but chunk based, not device based. See docs for more info.<br><strong>WARNING: Raid5 and Raid6 are not production-ready</strong>'
        });

        this.$('#compression').tooltip({
            html: true,
            placement: 'right',
            title: 'Choose a Pool compression algorithm.<br><strong>zlib: </strong>slower than lzo but higher compression ratio.<br><strong>lzo: </strong>faster than zlib but lower compression ratio.<br>Pool level compression applies to all it\'s Shares.<br>Alternatively: consider Share level compression.<br>This setting can be changed at any time.'
        });

        $('#add-pool-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                pool_name: 'validatePoolName',
                raid_level: 'validateRaid'
            },
            submitHandler: this.submit
        });

        return this;
    },

    renderSummary: function() {
        // Extract various data from currently selected disks for display
        var diskSizes = this.selectedDisks.map(function(disk) {
            return disk.get('size') * 1024;
        });
        var total = _.reduce(diskSizes, function(total, element) {
            return total + element;
        });
        var sizeCounts = _.countBy(diskSizes, function(size) {
            return size;
        });
        var data = _.map(sizeCounts, function(count, size) {
            return {
                count: count,
                size: humanize.filesize(size),
                sum: humanize.filesize(count * size)
            };
        });
        // Render
        this.$('#selected-disks-table').html(
            window.JST.pool_selected_disks({
                data: data,
                total: humanize.filesize(total)
            })
        );
        // Request usage bound calculation
        if (diskSizes) {
            $.ajax({
                url: '/api/pools/usage_bound',
                contentType: 'application/json',
                data: {
                    disk_sizes: diskSizes,
                    raid_level: $('#raid_level').val()
                }
            })
            .done(function(result) {
                target = $('#usable > b');
                if (result) {
                    target.text(humanize.filesize(result));
                    target.css('color', 'green');
                } else {
                    target.text('Not enough disks selected.');
                    target.css('color', 'red');
                }
            });
        }
        return this;
    },

    updateSelection: function(event) {
        if (!event.currentTarget.checked)
            $('#checkAll').prop('checked', false);
        var checkboxes = $('input:checkbox.disk');
        checkboxes.each(function() {
            $(this).closest('tr').toggleClass('row-highlight', this.checked);
        });
        var diskIds = checkboxes.filter(':checked').map(function() {
            return this.id;
        }).get();
        var disks = _.map(diskIds, function(id) {
            return this.collection.get(id);
        }, this);

        // Update and trigger re-validation of selected raid level
        this.selectedDisks.reset(disks);
        $('#raid_level').valid();
    },

    submit: function() {
        var button = $('#create_pool');
        if (buttonDisabled(button))
            return false;
        disableButton(button);
        var compression = $('#compression').val();
        if (compression == 'no') {
            compression = null;
        }
        var mnt_options = $('#mnt_options').val();
        if (mnt_options == '') {
            mnt_options = null;
        }
        $.ajax({
            url: '/api/pools',
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                disks: this.selectedDisks.pluck('name'),
                raid_level: $('#raid_level').val(),
                pname: $('#pool_name').val(),
                compression: compression,
                mnt_options: mnt_options
            })
        })
        .done(function() {
            enableButton(button);
            $('#add-pool-form input').tooltip('hide');
            app_router.navigate('pools', {trigger: true});
        })
        .fail(function() {
            enableButton(button);
        });
    },

    cancel: function (event) {
        event.preventDefault();
        this.$('#add-pool-form :input').tooltip('hide');
        app_router.navigate('pools', {trigger: true});
    },

    selectAllCheckboxes: function(event) {
        $('input:checkbox').prop('checked', $('#checkAll').prop('checked'));
        this.updateSelection(event);
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

        Handlebars.registerHelper('mathHelper', function (value, options) {
            return parseInt(value) + 1;
        });

        Handlebars.registerHelper('humanReadableSize', function (diskSize) {
            return humanize.filesize(diskSize * 1024);
        });
    }
});

//Add pagination
Cocktail.mixin(AddPoolView, PaginationMixin);

