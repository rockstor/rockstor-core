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


ServicesView = Backbone.View.extend({

    events: {
    	'click .configure': "configureService",
	'switchChange.bootstrapSwitch': 'switchStatus'
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
    		RockStorSocket.services = io.connect('/services', {'secure': true, 'force new connection': true});
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
    		}   else {
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

	//Initialize bootstrap switch
	this.$("[type='checkbox']").bootstrapSwitch();
	this.$("[type='checkbox']").bootstrapSwitch('onColor','success'); //left side text color
	this.$("[type='checkbox']").bootstrapSwitch('offColor','danger'); //right side text color
    },

    switchStatus: function(event,state){
	var serviceName = $(event.target).attr('data-service-name');
        if (state){
	    this.startService(serviceName);
        }else {
	    this.stopService(serviceName);
        }
    },

    startService: function(serviceName) {
    	var _this = this;
    	$.ajax({
    	    url: "/api/sm/services/" + serviceName + "/start",
    	    type: "POST",
    	    dataType: "json",
    	    success: function(data, status, xhr) {
    		_this.setStatusLoading(serviceName, false);
    	    },
    	    error: function(xhr, status, error) {
    		_this.setStatusError(serviceName, xhr);
    	    }
    	});
    },

    stopService: function(serviceName) {
    	var _this = this;
    	$.ajax({
    	    url: "/api/sm/services/" + serviceName + "/stop",
    	    type: "POST",
    	    dataType: "json",
    	    success: function(data, status, xhr) {
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

    cleanup: function() {
    	RockStorSocket.removeOneListener('services');
    }
});

// Add pagination
Cocktail.mixin(ServicesView, PaginationMixin);
