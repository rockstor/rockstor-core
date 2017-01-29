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

ShutdownView = RockstorLayoutView.extend({

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.common_navbar;
        this.paginationTemplate = window.JST.common_pagination;
        this.timeLeft = 180;
    },

    render: function() {
        var _this = this;
        $('#shutdown-modal').modal({
            keyboard: false,
            backdrop: 'static',
            show: false
        });
        if (confirm('Are you sure you want to Shutdown the system? All network access will be lost. Click OK to continue or Cancel to go back.')) {
            $('#shutdown-modal').modal('show');
            this.startForceRefreshTimer();

            $.ajax({
                url: '/api/commands/shutdown',
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
        } else {
            location.reload(history.go(-1));
        }
        return this;
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
                    // _this.reloadWindow();
                },
                error: function(xhr, status, error) {
                    _this.displayUserMsg2();
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
        $('#time-left').html(mins + ':' + sec);
        if (mins <= 1 && !this.userMsgDisplayed) {
            this.displayUserMsg();
            this.userMsgDisplayed = true;
        }
    },

    reloadWindow: function() {
        this.clearTimers();

    },

    clearTimers: function() {
        window.clearInterval(this.isUpTimer);
        window.clearInterval(this.forceRefreshTimer);
    },

    displayUserMsg: function() {
        $('#time-left').remove();
        $('#user-msg').show('highlight', null, 1000);
    },

    displayUserMsg2: function() {
        $('#message').remove();
        $('#timer').removeAttr('src');
        $('#time-left').remove();
        $('#user-msg').remove();
        $('#user-msg2').show('highlight', null, 1000);
    }

});