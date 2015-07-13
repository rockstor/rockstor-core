/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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

ConfigBackupView = RockstorLayoutView.extend({
    events: {
	'click #new_backup': 'newBackup',
	'click .cb-delete': 'deleteBackup',
	'click .cb-restore': 'restoreBackup'
    },

    initialize: function() {
	// call initialize of base
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.cb_cb;
	this.cb_table_template = window.JST.cb_cb_table;
	this.pagination_template = window.JST.common_pagination;
	this.collection = new ConfigBackupCollection();
	this.dependencies.push(this.collection);
	this.collection.on("reset", this.renderConfigBackups, this);
    },

    render: function() {
	this.collection.fetch();
	return this;
    },

    renderConfigBackups: function() {
	$(this.el).html(this.template({ collection: this.collection }));
	this.$("#cb-table-ph").html(this.cb_table_template({ collection: this.collection }));
    },

    newBackup: function() {
	console.log('in newBackup');
	var _this = this;
	var button = _this.$('#new-backup');
	if (buttonDisabled(button)) return false;
	disableButton(button);
	$.ajax({
	    url: "/api/config-backup",
	    type: "POST",
	    dataType: "json",
	    contentType: "application/json",
	    success: function() {
		enableButton(button);
		console.log('backup successful');
		_this.collection.fetch({reset: true});
	    },
	    error: function(xhr, status, error) {
		console.log("error in config backup");
		enableButton(button);
	    }
	});
	return this;
    },

    deleteBackup: function(event) {
	event.preventDefault();
	var _this = this;
	var cbid = $(event.currentTarget).attr('data-id');
	var button = $(event.currentTarget);
	if (buttonDisabled(button)) return false;
	if (confirm("Are you sure?")) {
	    disableButton(button);
	    $.ajax({
		url: "/api/config-backup/" + cbid,
		type: "DELETE",
		success: function() {
		    enableButton(button);
		    _this.collection.fetch({reset: true});
		},
		error: function(xhr, status, error) {
		    console.log('error while deleting config backup');
		    enableButton(button);
		}
	    });
	}
	return this;
    },

    restoreBackup: function(event) {
	event.preventDefault();
	var _this = this;
	var cbid = $(event.currentTarget).attr('data-id');
	var button = $(event.currentTarget);
	if (buttonDisabled(button)) return false;
	if (confirm("Are you sure?")) {
	    disableButton(button);
	    $.ajax({
		url: "/api/config-backup/" + cbid,
		type: "POST",
		dataType: "json",
		contentType: "application/json",
		data: JSON.stringify({"command": "restore"}),
		success: function() {
		    enableButton(button);
		    _this.collection.fetch({reset: true});
		},
		error: function() {
		    console.log('error while restoring this config backup');
		    enableButton(button);
		}
	    });
	}
	return this;
    }

});

Cocktail.mixin(ConfigBackupView, PaginationMixin);
