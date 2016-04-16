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
        var _this = this;
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.disk_spindown_disks;
        this.disks = new DiskCollection();
        this.diskName = this.options.diskName;
        this.dependencies.push(this.disks);
        this.tickFormatter = function (d) {
            var formatter = d3.format(",.0f");
            if (d > 254.5) {
                return formatter(d) + " off";
            }
            if (d < 0.5) {
                return "remove"
            }
            return formatter(d);
        }
        this.tickFormatterText = function (d) {
            var formatter = d3.format(",.0f");
            return formatter(d);
        }
        this.slider = null;
        this.sliderCallback = function (slider) {
            var value = slider.value();
            _this.$('#apm_value').val(_this.tickFormatterText(value));
        }
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
        var spindownTimes = {
            '30 seconds': 6,
            '1 minute': 12,
            '5 minutes': 60,
            '10 minutes': 120,
            '20 minutes': 240,
            '30 minutes': 241,
            '1 hour': 242,
            '2 hours': 244,
            '4 hours': 248,
            'Vendor defined (8-12h)': 253,
            'No spin down': 0
        };
        // retrieve local copy of disk serial number
        var serialNumber = this.disks.find(function (d) {
            return (d.get('name') == disk_name);
        }).get('serial');
        // retrieve local copy of current hdparm settings
        var hdparmSetting = this.disks.find(function (d) {
            return (d.get('name') == disk_name);
        }).get('hdparm_setting');
        // retrieve local copy of current apm level
        var apmLevel = this.disks.find(function (d) {
            return (d.get('name') == disk_name);
        }).get('apm_level');

        $(this.el).html(this.template({
            diskName: this.diskName,
            serialNumber: serialNumber,
            spindownTimes: spindownTimes,
            hdparmSetting: hdparmSetting,
            apmLevel: apmLevel
        }));

        this.$('#add-spindown-disk-form :input').tooltip({
            html: true,
            placement: 'right'
        });

        var err_msg = '';
        var spindown_err_msg = function () {
            return err_msg;
        };

        this.$('#enable_apm').click(function () {
            $('#apm_value').prop('disable', !this.checked); // disable apm text
            //$('#slide_lower_half').prop('disable', !this.checked);
            //$('#slide_upper_half').prop('disable', !this.checked);
            //$('#slide_disabled').prop('disable', !this.checked);
            //if (this.checked) {
            //    _this.renderSlider();
            //}
        });

        //if (apmLevel != 'unknown' || apmLevel != null) {
        //    // don't show apm slider if we couldn't read apm value
        //    _this.renderSlider();
        //}

        _this.renderSlider();

        this.$('#add-spindown-disk-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                spindown_time: 'required',
                slider: {
                    required: "#enable_apm:checked" // slider required only if
                    // APM settings tickbox enabled.
                },
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
        // eg by generating dynamicaly lines of the following
        // <option value="240">20 minutes</option>
        // todo awaiting fix for the timeString of the selected item to be passed on form submission
        Handlebars.registerHelper('display_spindown_time', function () {
            var html = '';
            // todo remove this console.log
            console.log('testing availability of current settings ' + this.hdparmSetting);
            for (var timeString in this.spindownTimes) {
                // need to programmatically retrieve current setting for previously set spindownTime ie read from systemd file
                // note it is not possible to use smart or hdparm to read what was set previously hence read from sys file.
                // todo remove this console.log
                console.log('processing timeString = ' + timeString);
                // todo for now hardwire 20 mins as default (pre-selected)
                // todo but this should show the current setting ie hdparmSetting
                // if (timeString == this.hdparmSetting) {
                if (timeString == '20 minutes') {
                    // todo remove this console.log
                    console.log('found our CURRENT SETTING of ' + timeString);
                    // we have found our current setting so mark it selected
                    html += '<option value="' + this.spindownTimes[timeString] + '" selected="selected">';
                    html += timeString + '</option>';
                } else {
                    html += '<option value="' + this.spindownTimes[timeString] + '">' + timeString + '</option>';
                }
            }
            return new Handlebars.SafeString(html);
        });
    },

    renderSlider: function () {
        var value = this.apmLevel;
        // when queried hdparm -B returns off when set to 255 so reverse this
        if (value == 'off') {
            value = 255;
        }
        this.$('#slider').empty();
        this.slider = d3.slider2().min(0).max(255).ticks(10).tickFormat(this.tickFormatter).value(value).callback(this.sliderCallback);
        d3.select('#slider').call(this.slider);
    },

    cancel: function (event) {
        event.preventDefault();
        this.$('#add-spindown-disk-form :input').tooltip('hide');
        app_router.navigate('disks', {trigger: true});
    }

});
