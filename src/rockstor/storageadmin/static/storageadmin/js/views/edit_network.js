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

EditNetworkView = RockstorLayoutView.extend({
    events: {
	'click #cancel': 'cancel',
	'change #method': 'changeBootProtocol'
    },

    initialize: function() {
	// call initialize of base
	this.constructor.__super__.initialize.apply(this, arguments);
	// set template
	this.template = window.JST.network_edit_network;
	this.name = this.options.name;
	this.network = new NetworkInterface({name: this.name});
	this.initHandlebarHelpers();
    },

    render: function() {
	var _this = this;
	this.network.fetch({
	    success: function(collection, response, options) {
		_this.renderNetwork();
	    }
	});
	return this;
    },

    renderNetwork: function() {
	var _this = this;
	var methodManual, methodAuto, managementInterface = false;
	if (this.network.get('method') == 'manual'){
		methodManual = true;
	}else{
		methodAuto = true;
	}
	if(this.network.get('itype') == 'management'){
		managementInterface = true;
	}
	$(this.el).html(this.template({
		network: this.network,
		networkName: this.network.get('name'),
		ipAddr: this.network.get('ipaddr'),
		netMask: this.network.get('netmask'),
		gateWay: this.network.get('gateway'),
		dnsServers: this.network.get('dns_servers'),
		interfaceType: this.network.get('itype'),
		methodManual: methodManual,
		methodAuto: methodAuto,
		managementInterface: managementInterface,
		}));

	this.$('#edit-network-form input').tooltip({placement: 'right'});

	this.$('#itype').tooltip({
	    html: true,
	    placement: 'right',
	    title: "You can assign a role for this interface. <strong>Unassigned</strong>: No special role will be assigned. <strong>Management</strong>: All Web-UI management will be restricted to this interface. <strong>Replication</strong>: Replication service will use this interface. Without a designated interface, Replication service will use the management interface by default"
	});

	this.validator = this.$("#edit-network-form").validate({
	    onfocusout: false,
	    onkeyup: false,
	    rules: {
		ipaddr: {
		    required: {
			depends: function(element) {
			    return (_this.$('#method').val() == 'manual')
			}
		    }
		},
		netmask: {
		    required: {
			depends: function(element) {
			    return (_this.$('#method').val() == 'manual')
			}
		    }
		}
	    },

	    submitHandler: function() {
		var button = _this.$('#submit');
		if (buttonDisabled(button)) return false;
		disableButton(button);
		var cancelButton = _this.$('#cancel');
		disableButton(cancelButton);
		var network = new NetworkInterface({name: _this.name});
		var data = _this.$('#edit-network-form').getJSON();
		network.save(data, {
		    success: function(model, response, options) {
			app_router.navigate("network", {trigger: true});
		    },
		    error: function(model, xhr, options) {
			enableButton(button);
			enableButton(cancelButton);
		    }
		});
		return false;
	    }
	});
    },

    changeBootProtocol: function(event) {
	if (this.$('#method').val() == 'manual') {
	    this.$('#ipaddr').removeAttr('disabled');
	    this.$('#netmask').removeAttr('disabled');
	    this.$('#gateway').removeAttr('disabled');
	    this.$('#domain').removeAttr('disabled');
	    this.$('#dns_servers').removeAttr('disabled');
	    this.$('#edit-network-form :input').tooltip({placement: 'right'});
	} else {
	    this.$('#ipaddr').attr('disabled', 'disabled');
	    this.$('#netmask').attr('disabled', 'disabled');
	    this.$('#gateway').attr('disabled', 'disabled');
	    this.$('#domain').attr('disabled', 'disabled');
	    this.$('#dns_servers').attr('disabled', 'disabled');
	    this.$('#edit-network-form :input').tooltip('hide');
	}

    },

    cancel: function(event) {
	event.preventDefault();
	app_router.navigate("network", {trigger: true});
    },
    
    initHandlebarHelpers: function(){
    	//Disable the text field when network method is Auto. 
    	Handlebars.registerHelper("disableIfAuto", function (condition) {
    	    return (condition) ? "disabled" : "";
    	});
    }

});
