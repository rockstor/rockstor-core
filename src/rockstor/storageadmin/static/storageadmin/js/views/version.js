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
	'click #enableAuto': 'enableAutoUpdate',
	'click #disableAuto': 'disableAutoUpdate'
    },

    initialize: function() {
	// call initialize of base
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.update_version_info;

	this.paginationTemplate = window.JST.common_pagination;
	this.timeLeft = 300;
    },

    render: function() {
	var _this = this;
	$.ajax({
	    url: "/api/commands/update-check",
	    type: "POST",
	    dataType: "json",
	    success: function(data, status, xhr) {
		_this.currentVersion = data[0];
		_this.mostRecentVersion = data[1];
		_this.changeList = data[2];
		//_this.renderVersionInfo();
		_this.checkAutoUpdateStatus();
	    },
	    error: function(xhr, status, error) {
	    }
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
	    error: function(xhr, status, error) {
	    }
	});
	return this;
    },

    renderVersionInfo: function() {

	var _this = this;
	$(this.el).html(this.template({
	    currentVersion: this.currentVersion,
	    mostRecentVersion: this.mostRecentVersion,
	    changeList: this.changeList,
	    autoUpdateEnabled: this.autoUpdateEnabled
	}));
	this.$('#update-modal').modal({
	    keyboard: false,
	    backdrop: 'static',
	    show: false
	});
	// Show or hide custom contrib textfield
	this.$('#contrib-custom').click(function(e) {
	    _this.$('#custom-amount').css('display', 'inline');
	});
	this.$('#contrib20').click(function(e) {
	    _this.$('#custom-amount').css('display', 'none');
	});
	this.$('#contrib30').click(function(e) {
	    _this.$('#custom-amount').css('display', 'none');
	});
    },

    donateYes: function() {
	var contrib = 0;
	this.$('input[name="amount"]').val(contrib);
	this.$('#contrib-form').submit();
	this.update();
    },

    update: function() {
	this.$('#update-modal').modal('show');
	this.startForceRefreshTimer();
	$.ajax({
	    url: "/api/commands/update",
	    type: "POST",
	    dataType: "json",
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
		url: "/api/sm/sprobes/loadavg?limit=1&format=json",
		type: "GET",
		dataType: "json",
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
	mins = Math.floor(this.timeLeft/60);
	sec = this.timeLeft - (mins*60);
	sec = sec >=10 ? '' + sec : '0' + sec
	this.$('#time-left').html(mins + ':' + sec)
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

    enableAutoUpdate: function() {
	return this.toggleAutoUpdate('enable-auto-update');
    },

    disableAutoUpdate: function() {
	return this.toggleAutoUpdate('disable-auto-update');
    },

    toggleAutoUpdate: function(updateFlag) {
	var _this = this;
	$.ajax({
            url: "/api/commands/" + updateFlag,
            type: "POST",
            dataType: "json",
	    success: function(data, status, xhr) {
		_this.reloadWindow();
            },
            error: function(xhr, status, error) {
		// server is not up, continue checking
            }
	});
    },


});
