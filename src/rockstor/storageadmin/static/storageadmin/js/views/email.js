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

EmailView = RockstorLayoutView.extend({
    events: {
	"click #Add-email-address" : "renderEmailForm",
	"click #cancel": "cancel",
	"click .email-delete": "deleteEmail",
	"click .send-test-message": "sendTestEmail"
    },

    initialize: function() {
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.email_email_setup;
	this.updatetemplate = window.JST.email_email;
	this.emails = new EmailAccountCollection();
	this.dependencies.push(this.emails);
	this.emails.on("reset", this.renderEmail, this);
    },

    render: function() {
	this.emails.fetch();
	var _this = this;
	this.fetch(_this.renderEmail, _this);
	return this;
    },

    renderEmail: function() {
	var email = null;
	if (this.emails.length > 0) {
	    email = this.emails.at(0);
	}
	$(this.el).html(this.template({
	    email: email
	}));
    },

    renderEmailForm: function() {
	var _this = this;
	var email = null;
	if (this.emails.length > 0) {
	    email = this.emails.at(0);
	}
	$(this.el).html(this.updatetemplate({
	    email: email
	}));

	this.$('#email-form input').tooltip({placement: 'right'});

	this.validator = this.$('#email-form').validate({
    	    onfocusout: false,
            onkeyup: false,
            rules: {
		name: 'required',
		sender: 'required',
		password: 'required',
		smtp_server: 'required',
		receiver: 'required'
            },

            submitHandler: function() {
		var button = $('#add-email');
		disableButton(button);
		var submitmethod = 'POST';
		var posturl = '/api/email';
		var data = _this.$('#email-form').getJSON();
		$.ajax({
		    url: posturl,
		    type: submitmethod,
		    dataType: 'json',
		    contentType: 'application/json',
		    data: JSON.stringify(data),
		    success: function() {
			enableButton(button);
			_this.emails.fetch({reset: true});
		    },
		    error: function(xhr, status, error) {
			enableButton(button);
		    }
		});

		return false;
	    }
	});
    },

    deleteEmail: function(event) {
	event.preventDefault();
	var _this = this;
	if(confirm("Are you sure about deleting this Email Account?")){
	    $.ajax({
		url: "/api/email",
		type: "DELETE",
		dataType: "json",
		success: function() {
		    _this.emails.fetch({reset: true});
		},
		error: function(xhr, status, error) {
		}
	    });
	} else {
	    return false;
	}
    },

    sendTestEmail: function(event) {
	event.preventDefault();
	$.ajax({
	    url: "/api/email/send-test-email",
	    type: "POST",
	    dataType: "json",
	    success: function() {
		$('#test-message-confirm').modal({
		    keyboard: false,
		    show: false,
		    backdrop: 'static'
		});
		$('#test-message-confirm').modal('show');
	    },
	});
    },

    cancel: function(event) {
	this.renderEmail();
    }


});
