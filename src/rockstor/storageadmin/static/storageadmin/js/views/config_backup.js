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
	'click .cb-restore': 'restoreBackup',
	'submit': 'uploadConfig'
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
    },
    getCookie: function(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != '') {
	    var cookies = document.cookie.split(';');
	    for (var i = 0; i < cookies.length; i++) {
		var cookie = jQuery.trim(cookies[i]);
		// Does this cookie string begin with the name we want?
		if (cookie.substring(0, name.length + 1) == (name + '=')) {
		    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
		    break;
		}
	    }
	}
	return cookieValue;
    },
    uploadConfig: function(event) {
	event.preventDefault();
	var form = this.$('#file-form')[0];
	var fileSelect = this.$('#file-select')[0];
	var uploadButton = this.$('#upload-button')[0];

	var send = XMLHttpRequest.prototype.send,
	    token = this.getCookie('csrftoken');

	XMLHttpRequest.prototype.send = function(data) {
            this.setRequestHeader('X-CSRFToken', token);
	    return send.apply(this, arguments);
	};

	var file = fileSelect.files;
	var formData = new FormData();
	formData.append('file', file[0]);
	formData.append('file-name', file[0].name);
	var xhr = new XMLHttpRequest();


	xhr.open('POST', '/api/config-backup/file-upload', true);
	console.log(xhr);

	xhr.onload = function() {
	    if (xhr.status < 400) {
		console.log('things went well');
	    } else {
		console.log('problem in file upload');
	    }
	};
	xhr.send(formData);
    }

});

Cocktail.mixin(ConfigBackupView, PaginationMixin);



/*
    var form = document.getElementById('file-form');
    console.log(form);
    var fileSelect = document.getElementById('file-select');
    var uploadButton = document.getElementById('upload-button');

    form.onsubmit = function(event) {
	event.preventDefault();
	console.log('form has been submitted');
	var file = fileSelect.files;
	console.log(file);
	var formData = new FormData();

	formData.append('file', file[0], file[0].name);

	var xhr = new XMLHttpRequest();
	console.log(xhr);
	xhr.open('POST', '/api/file-upload/', true);

	xhr.onload = function () {
	    if (xhr.status < 400) {
		// File(s) uploaded.
		uploadButton.innerHTML = 'Upload';
	    };
	    console.log(xhr);
	    xhr.send(formData);
	};
    };
*/
