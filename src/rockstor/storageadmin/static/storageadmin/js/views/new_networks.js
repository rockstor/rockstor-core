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

NewNetworksView = Backbone.View.extend({

	initialize: function() {
		this.template = window.JST.network_networks2;
		this.collection = new NetworkConnectionCollection();
		this.collection.on('reset', this.renderNetworks, this);
		this.devices = new NetworkDeviceCollection();
		this.devices.on('reset', this.renderNetworks, this);
		this.initHandlebarHelpers();
	},

	render: function() {
		var _this = this;
		this.collection.fetch();
		this.devices.fetch();
		return this;
	},


	renderNetworks: function() {
		var _this = this;
		$(this.el).empty();
		$(this.el).append(this.template({
			collection: this.collection,
			connections: this.collection.toJSON(),
			devices: this.devices.toJSON()
		}));
		setApplianceName();
	},

	initHandlebarHelpers: function(){
		//Disable the text field when network method is Auto. 
		Handlebars.registerHelper("disableIfAuto", function (condition) {
			return (condition) ? "disabled" : "";
		});
		Handlebars.registerHelper('print_networks_tbody', function() {
			var html = '';
			this.collection.each(function(network, index) {
				var networkName = network.get('name');
				html += '<tr>';
				html += '<td><i class="glyphicon glyphicon-signal"></i> ' +  networkName + '</td>';
				html += '<td>' + network.get("dname") + '</td>';
				html += '<td>' + network.get("mac") + '</td>';
				html += '<td>' + network.get("dspeed") + '</td>';
				html += '<td>' + network.get("method") + '</td>';
				html += '<td>' + network.get("ipaddr") + '</td>';
				html += '<td>' + network.get("netmask") + '</td>';
				html += '<td>' + network.get("gateway") + '</td>';
				html += '<td>' + network.get("dns_servers") + '</td>';
				html += '<td>' + network.get("itype") + '</td>';
				html += '<td><a href="#network/'+ networkName + '/edit" class="edit-network" data-network="' + networkName + '"><i class="glyphicon glyphicon-pencil"></i></a>';
				html += '</td>';
				html += '</tr>';
			});
			return new Handlebars.SafeString(html);
		});
	}

});

//Add pagination
Cocktail.mixin(NewNetworksView, PaginationMixin);

NewNetworkConnectionView = RockstorLayoutView.extend({

	events: {
		'click #cancel': 'cancel',
		'change #method': 'renderOptionalFields',
		'change #ctype': 'renderTeamDropdown',
	},

	initialize: function() {
		this.constructor.__super__.initialize.apply(this, arguments);
		this.template = window.JST.network_new_connection;
		this.devices = new NetworkDeviceCollection();
		this.devices.on('reset', this.renderDevices, this);
	},

	render: function() {
		this.devices.fetch();
		return this;
	},

	renderDevices: function() {
		var _this = this;
		$(this.el).empty();
		$(this.el).append(this.template({
			devices: this.devices.toJSON(),
			ctypes: ['ethernet', 'team', 'bond'],
			teamProfiles: ['broadcast', 'roundrobin', 'activebackup', 'loadbalance', 'lacp']

		}));

		this.validator = this.$("#new-connection-form").validate({
			submitHandler: function() {
				var button = _this.$('#submit');
				if (buttonDisabled(button)) return false;
				disableButton(button);
				var cancelButton = _this.$('#cancel');
				disableButton(cancelButton);
				var conn = new NetworkConnection();
				var data = _this.$('#new-connection-form').getJSON();
				conn.save(data, {
					success: function(model, response, options) {
						app_router.navigate("network2", {trigger: true});
					},
					error: function(model, response, options) {
						enableButton(button);
						enableButton(cancelButton);
					}
				});
			}
		});

		this.$('#devices').chosen();
		
		this.$('#teamprofile').tooltip({
			html: true,
			placement: 'right',
			title: "<strong>broadcast</strong> - Simple runner which directs the team device to transmit packets via all ports.<br>" +
			"<strong>roundrobin</strong> - Simple runner which directs the team device to transmits packets in a round-robin fashion.<br>" + 
			"<strong>activebackup</strong> - Watches for link changes and selects active port to be used for data transfers.<br>" + 
			"<strong>loadbalance</strong> -  To do passive load balancing, runner only sets up BPF hash function which will determine port for packet transmit." + 
			"To do active load balancing, runner moves hashes among available ports trying to reach perfect balance.<br>" + 
			"<strong>lacp</strong> - Implements 802.3ad LACP protocol. Can use same Tx port selection possibilities as loadbalance runner."
		});
	},

	// hide fields when selection is auto
	renderOptionalFields: function(){
		var selection = this.$('#method').val();
		if(selection == 'auto'){
			$('#optionalFields').hide();
		}else{
			$('#optionalFields').show();
		}
	},

	// show dropdown when selection is team
	renderTeamDropdown: function(){
		var selection = this.$('#ctype').val();
		if(selection == 'team'){
			$('#optionalDropdown').show();
		}else{
			$('#optionalDropdown').hide();
		}
	},

	cancel: function(event) {
		event.preventDefault();
		app_router.navigate("network2", {trigger: true});
	}
});
