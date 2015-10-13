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

/* Services */


ServicesView = Backbone.View.extend({

    events: {
	'click .slider-stop': "stopService",
	'click .slider-start': "startService",
	'click .configure': "configureService"
    },

    initialize: function() {
	this.template = window.JST.services_services;
	this.paginationTemplate = window.JST.common_pagination;
	this.collection = new ServiceCollection();
	this.actionMessages = {
	    'start': 'started',
	    'stop': 'stopped',
	    'restart': 'restarted',
	    'reload': 'reloaded'
	};
	this.smTs = null; // current timestamp of sm service
	this.configurable_services = ['nis', 'ntpd', 'active-directory', 'ldap', 'snmpd', 'docker', 'smartd', 'smb', 'nut', ];
    },

    render: function() {
	var _this = this;
	this.collection.fetch({
	    success: function(collection, response, options) {
		_this.renderServices();
		// Register function for socket endpoint
		RockStorSocket.services = io.connect('/services', {'secure': true});
		RockStorSocket.addListener(_this.servicesStatuses, _this, 'services:get_services');

	    }
	});

	return this;
    },

    servicesStatuses: function(data) {
	var _this = this;
	_.each(data, function(value, key, list) {
	    // Returns array of one object
	    var collectionArr = _this.collection.where({ 'name': key });
	    var collectionModel = collectionArr[0];
	    if ( collectionArr.length > 0) {
		if ( value.running > 0) {
		    collectionModel.set('status', false);
		} else {
		    collectionModel.set('status', true);
		}
	    }
	});
	this.renderServices();

    },

    renderServices: function() {
	var _this = this;
	$(this.el).empty();

	// find service-monitor service
	$(this.el).append(this.template({
	    services: this.collection,
	    configurable_services: this.configurable_services
	}));
	this.$(".ph-pagination").html(this.paginationTemplate({
	    collection: this.collection
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

    },

    startService: function(event) {
	var _this = this;
	var serviceName = $(event.currentTarget).data('service-name');
	// if already started, return
	if (this.getSliderVal(serviceName).toString() == "1") return;
	this.setStatusLoading(serviceName, true);
	$.ajax({
	    url: "/api/sm/services/" + serviceName + "/start",
	    type: "POST",
	    dataType: "json",
	    success: function(data, status, xhr) {
		_this.highlightStartEl(serviceName, true);
		_this.setSliderVal(serviceName, 1);
		_this.setStatusLoading(serviceName, false);
	    },
	    error: function(xhr, status, error) {
		_this.setStatusError(serviceName, xhr);
	    }
	});
    },

    stopService: function(event) {
	var _this = this;
	var serviceName = $(event.currentTarget).data('service-name');
	if (serviceName == 'service-monitor') return;
	// if already stopped, return
	if (this.getSliderVal(serviceName).toString() == "0") return;
	this.setStatusLoading(serviceName, true);
	$.ajax({
	    url: "/api/sm/services/" + serviceName + "/stop",
	    type: "POST",
	    dataType: "json",
	    success: function(data, status, xhr) {
		_this.highlightStartEl(serviceName, false);
		_this.setSliderVal(serviceName, 0);
		_this.setStatusLoading(serviceName, false);
	    },
	    error: function(xhr, status, error) {
		_this.setStatusError(serviceName, xhr);
	    }
	});
    },

    configureService: function(event) {
	event.preventDefault();
	var _this = this;
	var serviceName = $(event.currentTarget).data('service-name');
	app_router.navigate('services/' + serviceName + '/edit', {trigger: true});
    },

    setStatusLoading: function(serviceName, show) {
	var statusEl = this.$('div.command-status[data-service-name="' + serviceName + '"]');
	if (show) {
	    statusEl.html('<img src="/static/storageadmin/img/ajax-loader.gif"></img>');
	} else {
	    statusEl.empty();
	}
    },

    setStatusError: function(serviceName, xhr) {
	var statusEl = this.$('div.command-status[data-service-name="' + serviceName + '"]');
	var msg = parseXhrError(xhr);
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

    highlightStartEl: function(serviceName, on) {
	var startEl = this.$('div.slider-start[data-service-name="' + serviceName + '"]');
	if (on) {
	    startEl.addClass('on');
	} else {
	    startEl.removeClass('on');
	}
    },

    setSliderVal: function(serviceName, val) {
	this.$('input[data-service-name="' + serviceName + '"]').simpleSlider('setValue',val);
    },

    getSliderVal: function(serviceName) {
	return this.$('input[data-service-name="' + serviceName + '"]').data('slider-object').value;
    },

    cleanup: function() {
	RockStorSocket.removeOneListener('services');

    },

    showJoinDomainPopup: function(event) {
	if (!$(event.currentTarget).hasClass('disabled')) {
	    this.$('#join-domain-modal').modal('show');
	}
    },

    showJoinDomainStatus: function() {
	if (!_.isUndefined(RockStorGlobals.adJoinStatus) &&
            !_.isNull(RockStorGlobals.adJoinStatus)) {
	    if (RockStorGlobals.adJoinStatus) {
		this.$('#join-domain-status').html('<span class="alert alert-success alert-small">Join Ok</span>');
	    } else {
		this.$('#join-domain-status').html('<span class="alert alert-success alert-small">Not Joined</span>');
	    }
	}
    }

});

// Add pagination
Cocktail.mixin(ServicesView, PaginationMixin);
