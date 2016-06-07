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

UsersView = RockstorLayoutView.extend({
	events: {
		"click .delete-user": "deleteUser",
		"click .edit-user": "editUser"
	},

	initialize: function() {
		// call initialize of base
		this.constructor.__super__.initialize.apply(this, arguments);
		this.template = window.JST.users_users;
		this.collection = new UserCollection();
		this.dependencies.push(this.collection);
		this.collection.on("reset", this.renderUsers, this);
		this.initHandlebarHelpers();
	},

	render: function() {
		this.collection.fetch();
		return this;
	},

	renderUsers: function() {
		if (this.$('[rel=tooltip]')) {
			this.$('[rel=tooltip]').tooltip('hide');
		}

		this.rockstorUsers = this.collection.filter(function(grp) {
			return (grp.get('admin'))
		});
		this.otherSystemUsers = this.collection.filter(function(grp) {
			return (!grp.get('admin'))
		});

		$(this.el).html(this.template({
			collection: this.collection,
			rockstorUsers: this.rockstorUsers,
			otherSystemUsers: this.otherSystemUsers,
		}));

		this.$('[rel=tooltip]').tooltip({
			placement: 'bottom'
		});
	},

	deleteUser: function(event) {
		event.preventDefault();
		var _this = this;
		var username = $(event.currentTarget).attr('data-username');
		if (confirm("Delete user:  " + username + ". Are you sure?")) {
			$.ajax({
				url: "/api/users/" + username,
				type: "DELETE",
				dataType: "json",
				success: function() {
					_this.collection.fetch();
				},
				error: function(xhr, status, error) {}
			});
		} else {
			return false;
		}
	},

	editUser: function(event) {
		if (event) event.preventDefault();
		if (this.$('[rel=tooltip]')) {
			this.$('[rel=tooltip]').tooltip('hide');
		}
		var username = $(event.currentTarget).attr('data-username');
		app_router.navigate('users/' + username + '/edit', {
			trigger: true
		});
	},

	initHandlebarHelpers: function() {
		Handlebars.registerHelper('display_users_table', function(adminBool) {
			var html = '';
			var filteredCollection = null;
			if (adminBool) {
				filteredCollection = this.rockstorUsers;
			} else {
				filteredCollection = this.otherSystemUsers;
			}
			if (filteredCollection == null) {
				html += "No groups exist";
			} else {
				for (var i = 0; i < filteredCollection.length; i++) {
					var has_pincard = filteredCollection[i].get('has_pincard');
					var pincard_allowed = filteredCollection[i].get('pincard_allowed');
					if (has_pincard) {
						pincard_allowed = 'yes';
					}
					html += '<tr>';
					html += '<td><i class="glyphicon glyphicon-user"></i> ' + filteredCollection[i].get('username') + '</td>';
					html += '<td>' + filteredCollection[i].get('uid') + '</td>';
					html += '<td>' + filteredCollection[i].get('groupname') + '</td>';
					html += '<td>' + filteredCollection[i].get('gid') + '</td>';
					html += '<td>';
					if (filteredCollection[i].get('shell') != null) {
						html += filteredCollection[i].get('shell');
					}
					html += '</td>';
					html += '<td>';
					if (filteredCollection[i].get('managed_user')) {
						html += '<a href="#" class="edit-user" data-username="' + filteredCollection[i].get('username') + '" rel="tooltip" title="Edit user"><i class="glyphicon glyphicon-pencil"></i></a>&nbsp;';
						html += '<a href="#" class="delete-user" data-username="' + filteredCollection[i].get('username') + '" rel="tooltip" title="Delete user"><i class="glyphicon glyphicon-trash"></i></a>';
					}
					if (has_pincard) {
						html += '&nbsp;<i class="fa fa-credit-card text-success" aria-hidden="true" rel="tooltip" title="Pincard already present - Click to generate a new Pincard"></i>';
					} else {
						switch (pincard_allowed) {
							case 'yes':
								html += '&nbsp;<i class="fa fa-credit-card text-success" style="color: green;" aria-hidden="true" rel="tooltip" title="Click to generate a new Pincard"></i>';
								break;
							case 'otp':
								html += '&nbsp;<a href="#email" rel="tooltip" title="Pincard+OTP (One Time Password) via mail required, Email Alerts not enabled, click to procede"><i class="fa fa-credit-card text-warning" aria-hidden="true"></i></a>';
								break;
						}
					}
					html += '</td>';
					html += '</tr>';
				}
			}
			return new Handlebars.SafeString(html);
		});
	}

});

//Add pagination
Cocktail.mixin(UsersView, PaginationMixin);