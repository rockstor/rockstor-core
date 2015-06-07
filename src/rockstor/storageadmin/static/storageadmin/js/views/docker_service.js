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

DockerServiceView = Backbone.View.extend({
    events: {
	'click .slider-stop': "stopService",
	'click .slider-start': "startService"
    },

    initialize: function() {
	this.dashboardconfig = this.options.dashboardconfig;
	this.template = window.JST.rockons_docker_service;
	this.serviceName = 'docker';
	this.service = new Service({name: this.serviceName});
	this.parentView = this.options.parentView;
	this.updateFreq = 30000;
    },

    render: function() {
	var _this = this;
	this.service.fetch({
	    success: function(collection, response, options) {
		_this.renderPage();
	    }
	});
	this.startPolling();
	return this;
    },

    renderPage: function() {
	$(this.el).html(this.template({
   	    service: this.service
	}));

	this.$('input.service-status').simpleSlider({
	    "theme": "volume",
	    allowedValues: [0,1],
	    snap: true
	});

	this.$('input.service-status').each(function(i, el) {
	    var slider = $(el).data('slider-object');
	    // disable track and dragger events to disable slider
	    slider.trackEvent = function(e) {};
	    slider.dragger.unbind('mousedown');
	});

	return this;
    },

    startService: function(event) {
	var _this = this;
	var serviceName = this.serviceName;
	// if already started, return
	if (this.getSliderVal(serviceName).toString() == "1") return;
	this.stopPolling();
	this.setStatusLoading(serviceName, true);
	$.ajax({
	    url: "/api/sm/services/docker/start",
	    type: "POST",
	    dataType: "json",
	    success: function(data, status, xhr) {
		location.reload(true);
		_this.highlightStartEl(serviceName, true);
		_this.setSliderVal(serviceName, 1);
		_this.setStatusLoading(serviceName, false);
		_this.startPolling();
	    },
	    error: function(xhr, status, error) {
		_this.setStatusError(serviceName, xhr);
		_this.startPolling();
	    }
	});
    },

    stopService: function(event) {
	var _this = this;
	var serviceName = $(event.currentTarget).data('service-name');
	// if already stopped, return
	if (this.getSliderVal(serviceName).toString() == "0") return;
	this.stopPolling();
	this.setStatusLoading(serviceName, true);
	$.ajax({
	    url: "/api/sm/services/docker/stop",
	    type: "POST",
	    dataType: "json",
	    success: function(data, status, xhr) {
		location.reload(true);
		_this.highlightStartEl(serviceName, false);
		_this.setSliderVal(serviceName, 0);
		_this.setStatusLoading(serviceName, false);
		_this.startPolling();
	    },
	    error: function(xhr, status, error) {
		_this.setStatusError(serviceName, xhr);
		_this.startPolling();
	    }
	});
    },

    highlightStartEl: function(serviceName, on) {
	var startEl = this.$('div.slider-start[data-service-name="'+serviceName+'"]');
	if (on) {
	    startEl.addClass('on');
	} else {
	    startEl.removeClass('on');
	}
    },

    setStatusLoading: function(serviceName, show) {
	var statusEl = this.$('div.command-status[data-service-name="'+serviceName+'"]');
	if (show) {
	    statusEl.html('<img src="/static/storageadmin/img/ajax-loader.gif"></img>');
	} else {
	    statusEl.empty();
	}
    },

    startPolling: function() {
	var _this = this;
	// start after updateFreq
	this.timeoutId = window.setTimeout(function() {
	    _this.updateStatus();
	}, this.updateFreq);
    },

    updateStatus: function() {
	var _this = this;
	_this.startTime = new Date().getTime();
	_this.service.fetch({
	    silent: true,
	    success: function(service, response, options) {
		var serviceName = service.get('name');
		if (service.get('status')) {
		    _this.highlightStartEl(serviceName, true);
		    _this.setSliderVal(serviceName, 1);
		} else {
		    _this.highlightStartEl(serviceName, false);
		    _this.setSliderVal(serviceName, 0);
		}
		var currentTime = new Date().getTime();
		var diff = currentTime - _this.startTime;
		// if diff > updateFreq, make next call immediately
		if (diff > _this.updateFreq) {
		    _this.updateStatus();
		} else {
		    // wait till updateFreq msec has elapsed since startTime
		    _this.timeoutId = window.setTimeout( function() {
			_this.updateStatus();
		    }, _this.updateFreq - diff);
		}
	    }
	});
    },

    stopPolling: function() {
	if (!_.isUndefined(this.timeoutId)) {
	    window.clearInterval(this.timeoutId);
	}
    },

    setStatusError: function(serviceName, xhr) {
	var statusEl = this.$('div.command-status[data-service-name="' + serviceName + '"]');
	var msg = parseXhrError(xhr)
	// remove any existing error popups
	$('body').find('#' + serviceName + 'err-popup').remove();
	// add icon and popup
	statusEl.empty();
	var icon = $('<i>').addClass('icon-exclamation-sign').attr('rel', '#' + serviceName + '-err-popup');
	statusEl.append(icon);
	var errPopup = this.$('#' + serviceName + '-err-popup');
	var errPopupContent = this.$('#' + serviceName + '-err-popup > div');
	errPopupContent.html(msg);
	statusEl.click(function(){ errPopup.overlay().load(); });
    },

    setSliderVal: function(serviceName, val) {
	this.$('input[data-service-name='+serviceName+']').simpleSlider('setValue',val);
    },

    getSliderVal: function(serviceName) {
	return this.$('input[data-service-name='+serviceName+']').data('slider-object').value;
    },

    setCheckbox: function(name, checked) {
	var cbox = this.$('input[type="checkbox"][value="' + name + '"]');
	if (checked) {
	    cbox.attr("checked", "true");
	} else {
	    cbox.removeAttr("checked");
	}
    },

    cleanup: function() {
	this.stopPolling();
    }

});
