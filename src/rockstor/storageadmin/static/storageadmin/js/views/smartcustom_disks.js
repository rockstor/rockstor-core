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

SmartcustomDiskView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.disk_smartcustom_disks;
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
        var disk_obj = this.disks.find(function(d) {
            return (d.get('id') == disk_id);
        });
        var serialNumber = disk_obj.get('serial');
        var currentSmartCustom = disk_obj.get('smart_options');
        var disk_name = disk_obj.get('name');

        $(this.el).html(this.template({
            diskName: disk_name,
            serialNumber: serialNumber,
            currentSmartCustom: currentSmartCustom
        }));

        this.$('#add-smartcustom-disk-form :input').tooltip({
            html: true,
            placement: 'right'
        });

        var err_msg = '';
        var smartcustom_err_msg = function() {
            return err_msg;
        };

        $.validator.addMethod('validateSmartCustom', function(value) {
            var smartcustom_options = $('#smartcustom_options').val().trim();
            var devOptions = ['auto', 'test', 'ata', 'scsi', 'sat', 'sat,12', 'sat,16', 'sat,auto', 'usbprolific', 'usbjmicron', 'usbjmicron,0', 'usbjmicron,p', 'usbjmicron,x', 'usbjmicron,x,1', 'usbcypress', 'usbsunplus'];
            var devOptionsRaid = ['3ware', 'areca', 'hpt', 'cciss', 'megaraid', 'aacraid'];
            var toleranceOptions = ['normal', 'conservative', 'permissive', 'verypermissive'];
            // RegExp patters for the following RAID target devices:
            // 3ware /dev/twe, /dev/twa, /dev/twl followed by 0-15
            // Areca sata /dev/sg[2-9] but for hpahcisr and hpsa drivers /dev/sg[0-9]* (lsscsi -g to help)
            // so we still have an issue there.
            // HP Smart array with cciss driver uses /dev/cciss/c[0-9]d0
            // HighPoint RocketRaid SATA RAID controller (hpt), LSI MegaRAID SAS RAID controller Dell PERC 5/i,6/i controller (megaraid)
            // and Adaptec SAS RAID controller (​aacraid) all expect /dev/sd[a-z] type raid device targets.
            var raidTargetRegExp = [/\/dev\/tw[e|a|l][0-9][0-5]{0,1}$/, /\/dev\/sg[0-9]$/, /\/dev\/cciss\/c[0-9]d0$/, /\/dev\/sd[a-z]$/, /autodev$/];
            // Initial cascade of syntactic checks.
            if (smartcustom_options.length == 0) {
                // allow zero length (empty) entry to remove existing options
                return true;
            }
            if (/^[A-Za-z0-9,-/ ]+$/.test(smartcustom_options) == false) {
                err_msg = 'Invalid character found, expecting only letters, numbers, and \'-\',\'/\' and \'space.\'';
                return false;
            }
            if ((!smartcustom_options.includes('-d ')) && (!smartcustom_options.includes('-T '))) {
                err_msg = 'Must contain either -d or -T options or both.';
                return false;
            }
            if (smartcustom_options.length > 64) {
                err_msg = 'S.M.A.R.T options must not exceed 64 characters.';
                return false;
            }
            // By now we have valid characters that include "-d " and or "-T " and
            // less than 64 of them (including spaces) - the max db field length.
            // Move to repeat and semantic checks
            //
            // Check for only one instance of "-d ".
            var first_d_option = smartcustom_options.indexOf('-d ');
            if (first_d_option != -1 && smartcustom_options.lastIndexOf('-d') != first_d_option) {
                err_msg = 'Only one occurrence of the -d switch is permitted.';
                return false;
            }
            // Note that multiple instances of -T are valid.
            // Validate each option.
            // Find elements of given options via split by space.
            var option_array = smartcustom_options.split(' ');
            if ((option_array[0] != '-d') && (option_array[0] != '-T')) {
                err_msg = 'Please begin with either \'-d \' or \'-T \'';
                return false;
            }
            // true if option is Device switch "-d"
            function isDevSwitch(option) {
                return (option == '-d');
            }

            // true if option is Tolerance switch ie "-T"
            function isToleranceSwitch(option) {
                return (option == '-T');
            }

            // true if not recognized as a dev option (non Raid)
            function isNotDevOption(option) {
                return (devOptions.indexOf(option) == -1);
            }

            // true if not recognized as a type option
            function isNotToleranceOption(option) {
                return (toleranceOptions.indexOf(option) == -1);
            }

            // true if not recognized as a RAID option
            // Consider improving to use string.match(regexp) to match whole option.
            // Currently only validates pre ',' in for example 3ware,5
            function isNotRaidOption(option) {
                var without_values = option.substring(0, option.indexOf(','));
                return (devOptionsRaid.indexOf(without_values) == -1);
            }

            // true if not recognized as a RAID target device
            function isNotRaidTarget(option) {
                // assumed not a raid controller target until found otherwise
                target_found = false;
                // for (var pattern of raidTargetRegExp) { // possible js version ?
                for (index = 0; index < raidTargetRegExp.length; index++) {
                    var pattern = raidTargetRegExp[index]; // more compatible.
                    if (pattern.test(option) == true) {
                        target_found = true;
                        // match found so look no further.
                        break;
                    }
                }
                return !target_found;
            }

            // rogue spaces are empty array elements after split so test for them
            function isRogueSpace(option) {
                return (option.toString() == '');
            }

            // test for any rogue spaces
            if (option_array.filter(isRogueSpace).length != 0) {
                err_msg = 'One or more rouge spaces found, please re-check input';
                return false;
            }
            // Categorize all entered options individually, forEach is order safe.
            var dev_options_found = [];
            var tol_options_found = [];
            var unknown_options_found = [];
            var option_type = '';
            var unknown_switches_found = [];
            var dev_switch_found = false;
            var tol_switch_found = false;
            option_array.forEach(function(option) {
                // filter our various options before assessing them as valid.
                if (option.charAt(0) == '-') { // option is a switch
                    if (isDevSwitch(option)) {
                        option_type = 'dev';
                        dev_switch_found = true;
                    } else if (isToleranceSwitch(option)) {
                        option_type = 'tol';
                        tol_switch_found = true;
                    } else { // unknown switch
                        option_type = 'unknown';
                        unknown_switches_found.push(option);
                    }
                } else if (option_type == 'dev') {
                    // collect all options proceeded by a -d option
                    dev_options_found.push(option);
                } else if (option_type == 'tol') {
                    // collect all options proceeded by a -T option
                    tol_options_found.push(option);
                } else {
                    // collect all other options proceeded by an unknown switch.
                    unknown_options_found.push(option);
                }
            });
            // Report any unknown switches.
            if (unknown_switches_found != '') {
                err_msg = 'One or more unknown switches found: \'' + unknown_switches_found.toString() + '\', supported switches are \'-d\' and \'-T\'';
                return false;
            }
            // Report any options of unknown type.
            // Note this should never trigger as the last unknown_switches_found
            // should trigger first. We have a later one to catch unknown options
            // after known triggers.
            if (unknown_options_found != '') {
                err_msg = 'The following options of an unknown type were entered:' +
                    ' \'' + unknown_options_found.toString() + '\', supported ' +
                    'options are ' + devOptions.toString() + '\n' +
                    devOptionsRaid.toString() + toleranceOptions.toString();
                return false;
            }
            // Filter out unknown options on known switches ie "-d notanoption"
            // Filter our dev options first by absolute known / allowed options
            // filter the resulting array by the less strict known raid options
            var unknown_dev_options_found = dev_options_found.filter(isNotDevOption).filter(isNotRaidOption).filter(isNotRaidTarget);
            if (unknown_dev_options_found != '') {
                err_msg = 'The following unknown \'-d\' options were found \'' +
                    unknown_dev_options_found.toString() + '\'';
                return false;
            }
            // Filter out unknown Tolerance options
            var unknown_tol_options_found = tol_options_found.filter(isNotToleranceOption);
            if (unknown_tol_options_found != '') {
                err_msg = 'The following unknown \'-T\' options were found \'' +
                    unknown_tol_options_found.toString() + '\'. Available options' +
                    ' are ' + toleranceOptions.toString();
                return false;
            }
            // Check we have at least one Tolerance option
            if (tol_switch_found && tol_options_found.length < 1) {
                // no Tolerance options found
                err_msg = 'Tolerance switch \'-T\' found without valid options';
                return false;
            }
            // Finally check if more than one -d option is given
            if (dev_options_found.length > 1) {
                // only legitimate -d option with 2 parameters is raid + raid target
                if (dev_options_found.length == 2) {
                    if ((!isNotRaidOption(dev_options_found[0])) && (!isNotRaidTarget(dev_options_found[1]))) {
                        // we have a raid option followed by a raid target dev
                        return true;
                    }
                }
                err_msg = 'Only one \'-d\' option is supported';
                return false;
            }
            // not otherwise found to be invalid or valid so assume valid by now.
            return true;
        }, smartcustom_err_msg);

        this.$('#add-smartcustom-disk-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                smartcustom_options: 'validateSmartCustom',
            },

            submitHandler: function() {
                var button = $('#smartcustom-disk');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var submitmethod = 'POST';
                var posturl = '/api/disks/' + disk_id + '/smartcustom-drive';
                $.ajax({
                    url: posturl,
                    type: submitmethod,
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(_this.$('#add-smartcustom-disk-form').getJSON()),
                    success: function() {
                        enableButton(button);
                        _this.$('#add-smartcustom-disk-form :input').tooltip('hide');
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
        this.$('#add-smartcustom-disk-form :input').tooltip('hide');
        app_router.navigate('disks', {
            trigger: true
        });
    }

});
