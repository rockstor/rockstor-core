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

SpindownDiskView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel'
    },

    initialize: function () {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.disk_spindown_disks;
        this.disks = new DiskCollection();
        this.diskName = this.options.diskName;
        this.dependencies.push(this.disks);
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
        var serialNumber = this.disks.find(function (d) {
            return (d.get('name') == disk_name);
        }).get('serial');


        $(this.el).html(this.template({
            diskName: this.diskName,
            serialNumber: serialNumber
        }));

        this.$('#add-spindown-disk-form :input').tooltip({
            html: true,
            placement: 'right'
        });

        var err_msg = '';
        var spindown_err_msg = function () {
            return err_msg;
        };


        this.$('#add-spindown-disk-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
               // spindown_time: 'validateSpindown',
            },

            submitHandler: function () {
                var button = $('#spindown-disk');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var submitmethod = 'POST';
                var posturl = '/api/disks/' + disk_name + '/spindown-drive';
                $.ajax({
                    url: posturl,
                    type: submitmethod,
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(_this.$('#add-spindown-disk-form').getJSON()),
                    success: function () {
                        enableButton(button);
                        _this.$('#add-spindown-disk-form :input').tooltip('hide');
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
        // helper to fill dropdown with drive spindown values
        Handlebars.registerHelper('display_spindown_time', function () {
            var html = '',
                _this = this;
            var spindownTimes = ['30 seconds', '1 minute', '5 minutes', '10 minutes', '20 minutes', '30 minutes', '1 hour', '2 hours', '3 hours', '4 hours', '6 hours', '8 hours'];
            _.each(spindownTimes, function (timeString, index) {
                // need to programatically retrieve current setting for previously set spindownTime ie read from systemd file
                // note it is not possible to use smart or hdparm to read what was set previously hence read from sys file.
                if (timeString == '20 minutes') {
                    html += '<option value="' + timeString + '" selected="selected">';
                    html += timeString + '</option>';
                } else {
                    html += '<option value="' + timeString + '">' + timeString + '</option>';
                }
            });
            return new Handlebars.SafeString(html);
        });
    },

    cancel: function (event) {
        event.preventDefault();
        this.$('#add-smartcustom-disk-form :input').tooltip('hide');
        app_router.navigate('disks', {trigger: true});
    }

});
