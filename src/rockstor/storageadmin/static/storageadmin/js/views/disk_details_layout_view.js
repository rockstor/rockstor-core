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

DiskDetailsLayoutView = RockstorLayoutView.extend({

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        this.diskId = this.options.diskId;
        this.template = window.JST.disk_disk_details_layout;
        this.disk = new Disk({
            diskId: this.diskId
        });
        this.smartinfo = new SmartInfo({
            diskId: this.diskId
        });
        this.dependencies.push(this.disk);
        this.dependencies.push(this.smartinfo);
        this.active_tab = 0;
        this.initHandlebarHelpers();
    },

    events: {
        'click #smartinfo': 'refreshInfo',
        'click #test-start': 'startTest'
    },

    render: function() {
        this.fetch(this.renderSubViews, this);
        return this;
    },

    renderSubViews: function() {
        var capabilities = this.smartinfo.get('capabilities') || [];
        var test_capabilities = {};
        var running_test = null;
        capabilities.forEach(function(c) {
            if ((c.name == 'Short self-test routine recommended polling time') ||
                (c.name == 'Extended self-test routine recommended polling time') ||
                (c.name == 'Conveyance self-test routine recommended polling time')) {
                var p = c.name.indexOf('routine');
                var short_name = c.name.substring(0, p);
                test_capabilities[short_name] = c.capabilities;
            } else if (c.name == 'Self-test execution status' &&
                c.flag > 240 && c.flag < 250) {
                running_test = c.capabilities;
            }
        });
        var attributes = this.smartinfo.get('attributes') || [];
        var errorlogsummary = this.smartinfo.get('errorlogsummary') || [];
        var errorlog = this.smartinfo.get('errorlog') || [];
        var errorlogZero, errorlogOne = null;
        if (errorlog.length != 0) {
            errorlogZero = errorlog[0].line;
            errorlogOne = errorlog[1].line;
        }
        var testlog = this.smartinfo.get('testlog') || [];
        var testlogLength = testlog.length;
        var testlogdetail = this.smartinfo.get('testlogdetail') || [];
        var identity = this.smartinfo.get('identity') || [];
        var diskSmartNotAvailable = !this.disk.get('smart_available');
        var diskSmartNotEnabled = !this.disk.get('smart_enabled');
        var diskName = this.disk.get('name');
        var errorLogSummaryNull,
            testLogNull,
            notRunningTest,
            smartNotAvailableEnabled = false;
        if (errorlogsummary.length == 0) {
            errorLogSummaryNull = true;
        }
        if (testlogLength == 0) {
            testLogNull = true;
        }
        if (diskSmartNotAvailable || diskSmartNotEnabled) {
            smartNotAvailableEnabled = true;
        }
        if (!running_test) {
            notRunningTest = true;
        }

        $(this.el).html(this.template({
            disk: this.disk,
            diskSmartNotAvailable: diskSmartNotAvailable,
            diskSmartNotEnabled: diskSmartNotEnabled,
            smartNotAvailableEnabled: smartNotAvailableEnabled,
            diskName: diskName,
            attributes: attributes,
            capabilities: capabilities,
            errorlogsummary: errorlogsummary,
            errorLogSummaryNull: errorLogSummaryNull,
            errorlog: errorlog,
            errorlogZero: errorlogZero,
            errorlogOne: errorlogOne,
            testlog: testlog,
            testLogNull: testLogNull,
            testlogdetail: testlogdetail,
            smartinfo: this.smartinfo,
            tests: test_capabilities,
            running_test: running_test,
            notRunningTest: notRunningTest,
            identity: identity
        }));
        this.$('input.smart-status').simpleSlider({
            'theme': 'volume',
            allowedValues: [0, 1],
            snap: true
        });
        this.$('ul.nav.nav-tabs').tabs('div.css-panes > div');
        this.$('ul.nav.nav-tabs').data('tabs').click(this.active_tab);
        this.active_tab = 0;
    },

    refreshInfo: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        $.ajax({
            url: '/api/disks/smart/info/' + _this.diskId,
            type: 'POST',
            success: function(data, status, xhr) {
                _this.render();
            },
            error: function(xhr, status, error) {
                enableButton(button);
            }
        });
    },

    startTest: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var test_type = $('#test_name').val();
        $.ajax({
            url: '/api/disks/smart/test/' + _this.diskId,
            type: 'POST',
            dataType: 'json',
            data: {
                'test_type': test_type
            },
            success: function(data, status, xhr) {
                _this.render();
                _this.active_tab = 5;
            },
            error: function(xhr, status, error) {
                enableButton(button);
            }
        });
    },

    initHandlebarHelpers: function() {

        Handlebars.registerHelper('isAboveMinLength', function(minValue, target, options) {
            // check we have all the arguments we expect
            if (arguments.length != 3) {
                throw new Error('Handlerbars Helper ' +
                    '\'isAboveMinLength\' expects exactly 2 parameter.');
            }
            // do our logic and return options functions appropriately.
            if (target.length > minValue) {
                return options.fn(this);
            } else {
                return options.inverse(this);
            }
        });

        Handlebars.registerHelper('lastScannedOn', function () {
            var html = '';
            if (this.identity.scanned_on != null){
                html += 'Information presented was manually scanned on: ' +
                    this.identity.scanned_on + ' ';
            } else {
                html += 'No prior manual scan initiated: ';
            }
            return new Handlebars.SafeString(html);
        });
    }
});
