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

    initialize: function() {
        var _this = this;
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.disk_spindown_disks;
        this.disks = new DiskCollection();
        this.diskId = this.options.diskId;
        this.dependencies.push(this.disks);
        this.tickFormatter = function(d) {
            var formatter = d3.format(',.0f');
            if (d > 254.4) {
                return formatter(d) + ' off';
            }
            if (d < 0.5) {
                return 'none';
            }
            return formatter(d);
        };
        this.tickFormatterText = function(d) {
            var formatter = d3.format(',.0f');
            return formatter(d);
        };
        this.slider = null;
        // update the text box apm_value when ever the slider is moved.
        this.sliderCallback = function(slider) {
            var value = slider.value();
            _this.$('#apm_value').val(_this.tickFormatterText(value));
        };
        this.initHandlebarHelpers();
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
            'No spin down': 0,
            'Remove config': -1
        };
        _this.spindownTimes = spindownTimes;
        var diskObj = this.disks.find(function(d) {
            return (d.get('id') == disk_id);
        });
        var serialNumber = diskObj.get('serial');
        var hdparmSetting = diskObj.get('hdparm_setting');
        var apmLevel = diskObj.get('apm_level');
        var disk_name = diskObj.get('name');

        $(this.el).html(this.template({
            diskName: disk_name,
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
        var spindown_err_msg = function() {
            return err_msg;
        };

        $.validator.addMethod('validateApmValue', function(value) {
            var apm_value = $('#apm_value').val();
            if (apm_value == '') {
                err_msg = 'Please enter an APM value (1-255), or 0 to not apply an APM settings.';
                return false;
            }
            if (/^[0-9\b]+$/.test(apm_value) == false) {
                err_msg = 'Invalid APM value: please enter a number in the range 0-255.';
                return false;
            }
            if (apm_value < 0 || apm_value > 255) {
                err_msg = 'The APM setting must be between 0 (no setting) and 255 (disabled).';
                return false;
            }
            return true;
        }, spindown_err_msg);

        this.$('#enable_apm').click(function() {
            // $('#apm_value').prop('disable', !this.checked); // disable apm text
            //$('#slide_lower_half').prop('disable', !this.checked);
            //$('#slide_upper_half').prop('disable', !this.checked);
            //$('#slide_disabled').prop('disable', !this.checked);
            if (this.checked) {
                $('#slider-entry').show();
                $('#slider-key').show();
                $('#apm_value').val(apmLevel);
            } else {
                $('#slider-entry').hide();
                $('#slider-key').hide();
            }
        });

        // apmLevel = the current sensed level from the drive
        if (apmLevel == 0) {
            // we have a device that doesn't support APM or there was an error
            // reading it's current level so disable / hide our APM settings.
            //this.$('#enable_apm').attr('checked', 'true');
            this.$('#enable_apm').removeAttr('checked');
            this.$('#enable_apm').attr('disabled', 'true');
            //this.$('#slider').hide();
            this.$('#slider-entry').hide();
            this.$('#slider-key').hide();
        } else {
            // we can't disable the slider this way:
            // this.$('#slider').attr('disabled', 'true');
            // the apm_value text box is greyed but the slider still updates it's
            // contents.
            // disable on the text box works a treat given the above
            // this.$('#apm_value').attr('disabled', 'true');

            _this.renderSlider();
            // apmLevel = the current sensed level from the drive
            // apm_value = the text box and it's entered value
            // update the slider when the apm_value text box is changed
            //_this.$('#apm_value').focusout(function () {
            _this.$('#apm_value').change(function() {
                var our_value = this.value;
                // avoid passing NaN value to slider, leaving them to be
                // validated by our forms validateApmValue
                if (!isNaN(our_value)) {
                    _this.slider.setValue((our_value));
                }
            });
            // set the text box to show the current sensed APM level
            _this.$('#apm_value').val(apmLevel);
            // now call the change event on text box apm_value to update the slider
            _this.$('#apm_value').change();
            //_this.$('#enable_apm').click();
        }

        this.$('#add-spindown-disk-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                spindown_time: 'required',
                apm_value: 'validateApmValue'
                //slider: {
                //    required: "#enable_apm:checked" // slider required only if
                //    // APM settings tickbox enabled.
                //},
            },

            submitHandler: function() {
                var button = $('#spindown-disk');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var submitmethod = 'POST';
                var posturl = '/api/disks/' + disk_id + '/spindown-drive';
                var data = _this.$('#add-spindown-disk-form').getJSON();
                var selected_time = data.spindown_time;
                var spindown_text = 'no message';
                // look through spindownTimes to find the selected value
                for (var time_string in _this.spindownTimes) {
                    if (_this.spindownTimes[time_string] == selected_time) {
                        // value found so set our text to it's key.
                        spindown_text = time_string;
                        break;
                    }
                }
                // safeguard against setting -B (APM) option if enable_apm is
                // unticked.
                if (data.enable_apm != true) {
                    data.apm_value = 0;
                }
                data.spindown_message = spindown_text;
                $.ajax({
                    url: posturl,
                    type: submitmethod,
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    success: function() {
                        enableButton(button);
                        _this.$('#add-spindown-disk-form :input').tooltip('hide');
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

    initHandlebarHelpers: function() {
        // helper to fill dropdown with drive spindown values
        // eg by generating dynamicaly lines of the following
        // <option value="240">20 minutes</option>
        Handlebars.registerHelper('display_spindown_time', function() {
            var html = '';
            if (this.hdparmSetting == null) {
                // if there is no previous setting then default to 20 minutes
                this.hdparmSetting = '20 minutes';
            }
            for (var timeString in this.spindownTimes) {
                // Get the last setting by reading it from systemd file's
                // comment line as neither smart or hdparm can retrieve it.
                if (timeString == this.hdparmSetting) {
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

    renderSlider: function() {
        // Callback used to broadcast our changing value.
        this.$('#slider').empty();
        this.slider = d3.slider2().min(0).max(255).ticks(10).tickFormat(this.tickFormatter).value(0).reclaimable(127).used(0.5).callback(this.sliderCallback);
        d3.select('#slider').call(this.slider);
    },

    cancel: function(event) {
        event.preventDefault();
        this.$('#add-spindown-disk-form :input').tooltip('hide');
        app_router.navigate('disks', {
            trigger: true
        });
    }

});
