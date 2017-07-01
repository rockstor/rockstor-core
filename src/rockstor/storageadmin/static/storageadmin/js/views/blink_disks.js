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

BlinkDiskView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.disk_blink_disks;
        this.disks = new DiskCollection();
        this.diskId = this.options.diskId;
        this.dependencies.push(this.disks);
    },

    render: function() {
        this.fetch(this.renderDisksForm, this);
        return this;
    },

    renderDisksForm: function() {
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }
        var _this = this;
        var disk_id = this.diskId;
        var diskObj = this.disks.find(function(d) {
            return (d.get('id') == disk_id);
        });
        var diskName = diskObj.get('name');
        var serialNumber = diskObj.get('serial');

        $(this.el).html(this.template({
            diskName: diskName,
            serialNumber: serialNumber
        }));

        this.$('#add-blink-disk-form :input').tooltip({
            html: true,
            placement: 'right'
        });

        var err_msg = '';
        var raid_err_msg = function() {
            return err_msg;
        };

        $.validator.addMethod('validateTotalTime', function(value) {
            var total_time = $('#total_time').val();

            if (total_time == '') {
                err_msg = 'Please enter Total time';
                return false;
            } else
            if (total_time > 90) {
                err_msg = 'Total time must not exceed more than 90 sec';
                return false;
            } else
            if (/^[0-9\b]+$/.test(total_time) == false) {
                err_msg = 'Total time must be an number and must be less than 90';
                return false;
            }

            return true;
        }, raid_err_msg);

        $.validator.addMethod('validateBlinkTime', function(value) {
            var blink_time = $('#blink_time').val();
            var total_time = $('#total_time').val();

            if (blink_time == '') {
                err_msg = 'Please enter Blink time';
                return false;
            } else
            if (blink_time > total_time) {
                err_msg = 'Blink time must not exceed total time';
                return false;
            } else
            if (/^[0-9\b]+$/.test(blink_time) == false) {
                err_msg = 'Blink time must be an number and must be less than total time';
                return false;
            }

            return true;
        }, raid_err_msg);

        $.validator.addMethod('validateSleepTime', function(value) {
            var sleep_time = $('#sleep_time').val();
            var total_time = $('#total_time').val();

            if (sleep_time == '') {
                err_msg = 'Please enter Sleep time';
                return false;
            } else
            if (sleep_time > total_time) {
                err_msg = 'Sleep time must not exceed total time';
                return false;
            } else
            if (/^[0-9\b]+$/.test(sleep_time) == false) {
                err_msg = 'Sleep time must be an number and must be less than 90';
                return false;
            }

            return true;
        }, raid_err_msg);

        this.$('#add-blink-disk-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                total_time: 'validateTotalTime',
                blink_time: 'validateBlinkTime',
                sleep_time: 'validateSleepTime'
            },

            submitHandler: function() {
                var button = $('#blink-disk');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var submitmethod = 'POST';
                var posturl = '/api/disks/' + disk_id + '/blink-drive';
                $.ajax({
                    url: posturl,
                    type: submitmethod,
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(_this.$('#add-blink-disk-form').getJSON()),
                    success: function() {
                        enableButton(button);
                        _this.$('#add-blink-disk-form :input').tooltip('hide');
                        app_router.navigate('disks', {
                            trigger: true
                        });
                    },
                    error: function(xhr, status, error) {
                        enableButton(button);
                    }
                });

                return false;
            }
        });
    },

    cancel: function(event) {
        event.preventDefault();
        this.$('#add-blink-disk-form :input').tooltip('hide');
        app_router.navigate('disks', {
            trigger: true
        });
    }

});
