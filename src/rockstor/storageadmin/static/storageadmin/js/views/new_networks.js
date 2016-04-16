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
		'change #method': 'renderOptionalFields'
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
			teamTypes: ['type1', 'type2', 'type3']
		
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
	},
	
	renderOptionalFields: function(){
		var selection = this.$('#method').val();
		  if(selection == 'auto'){
			  $('#optionalFields').hide();
		  }else{
			  $('#optionalFields').show();
		  }
	},
	
	cancel: function(event) {
		event.preventDefault();
		app_router.navigate("network2", {trigger: true});
	}
});
