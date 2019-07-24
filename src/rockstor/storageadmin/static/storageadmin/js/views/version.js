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

VersionView = RockstorLayoutView.extend({
    events: {
        'click #update': 'update',
        'click #donateYes': 'donateYes',
        'click #autoUpdateSwitch': 'autoUpdateSwitch',
        'click #enableAuto': 'enableAutoUpdate',
        'click #disableAuto': 'disableAutoUpdate',
        'click #stable-modal': 'showStableModal',
        'click #testing-modal': 'showTestingModal',
        'click #activateStable': 'activateStable',
        'click #activateTesting': 'activateTesting'
    },

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.update_version_info;
        this.timeLeft = 300;
        this.subscriptions = new UpdateSubscriptionCollection();
        this.dependencies.push(this.subscriptions);
        this.appliances = new ApplianceCollection();
        this.dependencies.push(this.appliances);
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.renderUpdates, this);
        return this;
    },

    renderUpdates: function() {
        var _this = this;
        $('.modal-backdrop').remove();
        $.ajax({
            url: '/api/commands/update-check',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.currentVersion = data[0];
                _this.mostRecentVersion = data[1];
                _this.changeList = data[2];
                _this.checkAutoUpdateStatus();
            },
            error: function(xhr, status, error) {}
        });
        return this;
    },

    checkAutoUpdateStatus: function() {
        var _this = this;
        $.ajax({
            url: '/api/commands/auto-update-status',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.autoUpdateEnabled = data.enabled;
                _this.renderVersionInfo();
            },
            error: function(xhr, status, error) {}
        });
        return this;
    },

    renderVersionInfo: function() {

        var stableSub = null;
        var defaultSub = null;
        this.subscriptions.each(function(s) {
            if (s.get('name') == 'Stable') {
                stableSub = s.toJSON();
            }
            if (s.get('name') == 'Testing') {
                defaultSub = s.toJSON();
            }
        });
        var currentAppliance = this.appliances.find(function(a) {
            return a.get('current_appliance') == true;
        });

        $(this.el).html(this.template({
            currentVersion: this.currentVersion,
            mostRecentVersion: this.mostRecentVersion,
            changeList: this.changeList,
            changeMap: this.changeLog(this.changeList),
            autoUpdateEnabled: this.autoUpdateEnabled,
            stableSub: stableSub,
            defaultSub: defaultSub,
            applianceId: currentAppliance.get('uuid')
        }));
        this.$('#update-modal').modal({
            keyboard: false,
            backdrop: 'static',
            show: false
        });
    },

    donateYes: function() {
        var contrib = 0;
        this.$('input[name="amount"]').val(contrib);
        this.$('#contrib-form').submit();
    },

    update: function() {
        this.$('#update-modal').modal('show');
        this.startForceRefreshTimer();
        $.ajax({
            url: '/api/commands/update',
            type: 'POST',
            dataType: 'json',
            global: false, // dont show global loading indicator
            success: function(data, status, xhr) {
                _this.checkIfUp();
            },
            error: function(xhr, status, error) {
                _this.checkIfUp();
            }
        });
    },

    checkIfUp: function() {
        var _this = this;
        this.isUpTimer = window.setInterval(function() {
            $.ajax({
                url: '/api/sm/sprobes/loadavg?limit=1&format=json',
                type: 'GET',
                dataType: 'json',
                global: false, // dont show global loading indicator
                success: function(data, status, xhr) {
                    _this.reloadWindow();
                },
                error: function(xhr, status, error) {
                    // server is not up, continue checking
                }
            });
        }, 5000);
    },

    // countdown timeLeft seconds and then force a window reload
    startForceRefreshTimer: function() {
        var _this = this;
        this.forceRefreshTimer = window.setInterval(function() {
            _this.timeLeft = _this.timeLeft - 1;
            _this.showTimeRemaining();
            if (_this.timeLeft <= 0) {
                _this.reloadWindow();
            }
        }, 1000);
    },

    showTimeRemaining: function() {
        mins = Math.floor(this.timeLeft / 60);
        sec = this.timeLeft - (mins * 60);
        sec = sec >= 10 ? '' + sec : '0' + sec;
        this.$('#time-left').html(mins + ':' + sec);
        if (mins <= 1 && !this.userMsgDisplayed) {
            this.displayUserMsg();
            this.userMsgDisplayed = true;
        }
    },

    reloadWindow: function() {
        this.clearTimers();
        this.$('#update-modal').modal('hide');
        location.reload(true);
    },

    clearTimers: function() {
        window.clearInterval(this.isUpTimer);
        window.clearInterval(this.forceRefreshTimer);
    },

    displayUserMsg: function() {
        this.$('#user-msg').show('highlight', null, 1000);
    },

    autoUpdateSwitch: function() {
        $('#auto-update-modal').modal({
            keyboard: false,
            show: false,
            backdrop: 'static'
        });
        $('#auto-update-modal').modal('show');
    },

    enableAutoUpdate: function() {
        return this.toggleAutoUpdate('enable-auto-update');
    },

    disableAutoUpdate: function() {
        return this.toggleAutoUpdate('disable-auto-update');
    },

    toggleAutoUpdate: function(updateFlag) {
        var _this = this;
        $.ajax({
            url: '/api/commands/' + updateFlag,
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.reloadWindow();
            },
            error: function(xhr, status, error) {
                // server is not up, continue checking
            }
        });
    },

    changeLog: function(logArray) {
        var changeLogArray = [];
        var issues = [];
        var nextString = [];
        var changeDescription = [];
        var contributors = [];

        for (var i = 0; i < logArray.length; i++) {
            if (logArray[i] == '' || logArray[i].substring(0, 1) == '*') {
                // Preserve empty lines and package version entries 'as is'
                // and Bold for section emphasis.
                changeDescription[i] = logArray[i]
            } else {
                var hashIndex = logArray[i].indexOf('#');
                var atRateIndex = logArray[i].indexOf('@');
                issues[i] = logArray[i].substring(hashIndex + 1, atRateIndex - 1);
                var namesNum = logArray[i].indexOf('@') + 1;
                changeDescription[i] = logArray[i].substring(0, hashIndex - 1);
                nextString[i] = logArray[i].substring(namesNum, logArray[i].length);
                contributors[i] = nextString[i].split(' @');
            }
        }
        for (var k = 0; k < changeDescription.length; k++) {
            var cl = changeDescription[k];
            // Don't process package version lines for issue and contributor
            if (cl == '' || cl.substring(0, 1) == '*') {
                cl = '<strong>' + cl + '</strong>'
            } else {
                cl += '<a href="https://github.com/rockstor/rockstor-core/issues/';
                cl += issues[k];
                cl += '" target="_blank"> #';
                cl += issues[k];
                cl += '</a>';
                if (typeof contributors[k] !== 'undefined') {
                    for (var j = 0; j < contributors[k].length; j++) {
                        cl += '<a href="https://github.com/';
                        cl += contributors[k][j];
                        cl += '" target="_blank"> @';
                        cl += contributors[k][j];
                        cl += '</a>';
                    }
                }
            }
            changeLogArray.push(new Handlebars.SafeString(cl));
        }
        return changeLogArray;
    },

    showStableModal: function() {
        this.$('#activate-stable').modal('show');
    },

    showTestingModal: function() {
        this.$('#activate-testing').modal('show');
    },

    activateStable: function() {
        var button = this.$('activateStable');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var activationCode = this.$('#activation-code').val();
        var _this = this;
        $.ajax({
            url: '/api/update-subscriptions/activate-stable',
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                'activation_code': activationCode
            }),
            success: function(data, status, xhr) {
                _this.reloadWindow();
            },
            error: function(xhr, status, error) {
                enableButton(button);
            }
        });
    },

    activateTesting: function() {
        var _this = this;
        var button = this.$('activateTesting');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        console.log('Inactive testing');
        $.ajax({
            url: '/api/update-subscriptions/activate-testing',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.reloadWindow();
            }
        });
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('is_sub_active', function(sub, options) {
            if (sub && sub.status == 'active') {
                return options.fn(this);
            }
            return options.inverse(this);
        });
        Handlebars.registerHelper('no_sub_active', function(options) {
            if (!this.defaultSub && !this.stableSub) {
                return options.fn(this);
            }
            return options.inverse(this);
        });
        Handlebars.registerHelper('update_available', function(options) {
            if (this.currentVersion != this.mostRecentVersion) {
                return options.fn(this);
            }
            return options.inverse(this);
        });
    }
});