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

AddPoolView = Backbone.View.extend({
    events: {
        "click #js-cancel": "cancel",
        'click [class="disk"]': 'clickCheckbox',
        "click #checkAll": "selectAllCheckboxes",
        "change #raid_level": "clickCheckbox"
    },

    initialize: function () {

        this.template = window.JST.pool_add_pool_template;

        // dont paginate disk selection table for now
        //this.pagination_template = window.JST.common_pagination;
        this.collection = new DiskCollection();
        // we do this as a workaround until we fix the add pool form properly.
        // with default page size, only upto 15 drives are shown.
        // @todo: fix this properly.
        this.collection.setPageSize(100);
        this.filteredCollection = new DiskCollection();
        this.collection.on("reset", this.renderDisks, this);
        this.initHandlebarHelpers();
    },

    render: function () {
        this.collection.fetch();
        return this;
    },

    renderDisks: function () {
        $(this.el).empty();
        var _this = this;
        this.filteredCollection = _.reject(this.collection.models, function (disk) {
            return _.isNull(disk.get('pool')) && !disk.get('parted') && !disk.get('offline') && _.isNull(disk.get('btrfs_uuid')) && isSerialUsable(disk.get('serial'));
        });

        // N.B. the isSerialUsable() code below is now duplicated in the
        // Backbone Disk model as the property isSerialUsable()
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

        this.collection.remove(this.filteredCollection);
        $(_this.el).append(_this.template({
            disks: this.collection.toJSON(),
        }));

        var err_msg = 'Incorrect number of disks';
        var raid_err_msg = function () {
            return err_msg;
        }

        $.validator.addMethod('validatePoolName', function (value) {
            var pool_name = $('#pool_name').val();
            if (/^[A-Za-z0-9_.-]+$/.test(pool_name) == false) {
                err_msg = 'Invalid characters in Pool name.';
                return false;
            }
            return true
        }, raid_err_msg);


        $.validator.addMethod('validateRaid', function (value) {
            var raid_level = $('#raid_level').val();
            var n = $("input:checked.disk").length;
            if (raid_level == 'single') {
                if (n < 1) {
                    err_msg = 'At least one disk must be selected';
                    return false;
                }
            } else if (raid_level == 'raid0') {
                if (n < 2) {
                    err_msg = 'Raid0 requires at least 2 disks to be selected';
                    return false;
                }
            } else if (raid_level == 'raid1') {
                if (n < 2) {
                    err_msg = 'Raid1 requires at least 2 disks to be selected';
                    return false;
                }
            } else if (raid_level == 'raid5') {
                if (n < 2) {
                    err_msg = 'Raid5 requires at least 2 disks to be selected';
                    return false;
                }
            } else if (raid_level == 'raid6') {
                if (n < 3) {
                    err_msg = 'Raid6 requires at least 3 disks to be selected';
                    return false;
                }
            } else if (raid_level == 'raid10') {

                if (n < 4) {
                    err_msg = 'Raid10 requires at least 4 disks to be selected';
                    return false;
                }
            }
            return true;
        }, raid_err_msg);


        this.$("#disks-table").tablesorter({
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
            title: "Desired RAID level of the pool<br><strong>Single</strong>: No software raid. (Recommended while using hardware raid).<br><strong>Raid0</strong>, <strong>Raid1</strong>, <strong>Raid10</strong>, <strong>Raid5</strong> and <strong>Raid6</strong> are similar to conventional implementations with key differences.<br>See documentation for more information"
        });

        this.$('#compression').tooltip({
            html: true,
            placement: 'right',
            title: "Choose a compression algorithm for this Pool.<br><strong>zlib: </strong>slower but higher compression ratio.<br><strong>lzo: </strong>faster compression/decompression, but ratio smaller than zlib.<br>Enabling compression at the pool level applies to all Shares carved out of this Pool.<br>Don't enable compression here if you like to have finer control at the Share level.<br>You can change the algorithm, disable or enable it later, if necessary."
        });


        $('#add-pool-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                pool_name: "validatePoolName",
                raid_level: "validateRaid"
            },

            submitHandler: function () {
                var button = $('#create_pool');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var pool_name = $('#pool_name').val();
                var raid_level = $('#raid_level').val();
                var compression = $('#compression').val();
                if (compression == 'no') {
                    compression = null;
                }
                var mnt_options = $('#mnt_options').val();
                if (mnt_options == '') {
                    mnt_options = null;
                }
                var disk_names = [];
                var n = $("input:checked.disk").length;
                $("input:checked.disk").each(function (i) {
                    if (i < n) {
                        disk_names.push($(this).val());
                    }
                });

                var jqxhr = $.ajax({
                    url: '/api/pools',
                    type: 'POST',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        "disks": disk_names, "raid_level": raid_level,
                        "pname": pool_name, "compression": compression,
                        "mnt_options": mnt_options,
                    }),
                });

                jqxhr.done(function () {
                    enableButton(button);

                    _this.$('#add-pool-form input').tooltip('hide');
                    app_router.navigate('pools', {trigger: true})
                });

                jqxhr.fail(function (xhr, status, error) {
                    enableButton(button);
                });

            }

        });

        return this;
    },

    cancel: function (event) {
        event.preventDefault();
        this.$('#add-pool-form :input').tooltip('hide');
        app_router.navigate('pools', {trigger: true});
    },

    selectAllCheckboxes: function (event) {
        $("#checkAll").change(function () {
            $("input:checkbox").prop('checked', $(this).prop("checked"));
            $("input:checkbox").closest("tr").toggleClass("row-highlight", this.checked);
        });
        if ($('#checkAll').prop("checked")) {
            var _this = this;
            var allDisks = {};
            _this.collection.each(function (disk, index) {
                var capacity = disk.get('size') * 1024;
                if (capacity in allDisks) {
                    allDisks[capacity] += 1;
                } else {
                    allDisks[capacity] = 1;
                }
            });
            var diskSummary = this.diskSummaryTable(allDisks);
            $("#SelectedDisksTable").html(diskSummary);
        } else {
            $("#SelectedDisksTable").empty();
        }
    },

    clickCheckbox: function (event) {
        $("input:checkbox").change(function () {
            $(this).closest("tr").toggleClass("row-highlight", this.checked);
        });
        var _this = this;
        var n = $("input:checked.disk").length;
        var singleDisk = {};
        $("input:checked.disk").each(function (index) {
            var capacity = _this.collection.get(this.id).get('size') * 1024;
            if (capacity in singleDisk) {
                singleDisk[capacity] += 1;
            } else {
                singleDisk[capacity] = 1;
            }
        });
        var diskSummary = this.diskSummaryTable(singleDisk);
        if (n > 0) {
            $("#SelectedDisksTable").html(diskSummary);
        } else {
            $("#SelectedDisksTable").empty();
        }
    },

    diskSummaryTable: function (diskObj) {
        var formStyle = "<div class=" + "'form-group'" + "><label class=" + "'col-sm-4 control-label'" + " >Selected disks summary</label><div class='col-sm-6'>";
        var diskSummary = formStyle + "<table class= 'table table-condensed table-bordered share-table tablesorter'>";
        var grandTotal = 0;
        for (var key in diskObj) {
            var readableCapacity = humanize.filesize(key);
            var totalCapacity = key * diskObj[key];
            diskSummary += "<tr>";
            diskSummary += "<td>" + diskObj[key] + " X " + readableCapacity + "</td>";
            diskSummary += "<td>" + humanize.filesize(totalCapacity) + "</td>";
            diskSummary += "</tr>";
            grandTotal += totalCapacity;
        }
        var diskUsableCapacity = this.getUsableCapacity(diskObj, humanize.filesize(grandTotal));
        diskSummary += "<tr><td><b>Total Raw Capacity</b></td><td style='color:#EB6841;'><b>" + humanize.filesize(grandTotal) + "</td></b></tr>";
        diskSummary += "<tr><td><b>Total Usable Capacity</b></td>" + "<td style='color:green;'><b>" + diskUsableCapacity + "</b></td></tr>";
        diskSummary += "</table>";
        return diskSummary;
    },

    getUsableCapacity: function (diskObject, rawCapacity) {
        var raidConfig = $('#raid_level').val();

        //get all the keys and convert them to numbers to get the disk size correctly.
        var keysArr = Object.keys(diskObject);
        var numericKeysArr = keysArr.map(function (key) {
            return Number(key);
        });
        //calculate least disk size from all the keys.
        var minDiskSize = Math.min.apply(Math, numericKeysArr);

        var totalSelectedDisks = 0;
        for (var key in diskObject) {
            totalSelectedDisks += diskObject[key];
        }

        var usableCapacity;
        switch (raidConfig) {
            case "single":
                usableCapacity = rawCapacity;
                break;
            case "raid0":
                usableCapacity = humanize.filesize(minDiskSize * totalSelectedDisks);
                break;
            case "raid1":
                usableCapacity = humanize.filesize(minDiskSize * totalSelectedDisks / 2);
                break;
            case "raid5":
                usableCapacity = humanize.filesize(minDiskSize * (totalSelectedDisks - 1));
                break;
            case "raid6":
                usableCapacity = humanize.filesize(minDiskSize * (totalSelectedDisks - 2));
                break;
            case "raid10":
                usableCapacity = humanize.filesize(minDiskSize * totalSelectedDisks / 2);
                break;
        }

        return usableCapacity;

    },

    initHandlebarHelpers: function () {
        Handlebars.registerHelper("mathHelper", function (value, options) {
            return parseInt(value) + 1;
        });

        Handlebars.registerHelper('humanReadableSize', function (diskSize) {
            return humanize.filesize(diskSize * 1024);
        });
    }

});

//Add pagination
Cocktail.mixin(AddPoolView, PaginationMixin);
