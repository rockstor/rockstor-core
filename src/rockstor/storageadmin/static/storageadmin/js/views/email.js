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
        'click #Add-email-address': 'renderEmailForm',
        'click #cancel': 'cancel',
        'click .email-delete': 'deleteEmail',
        'click .send-test-message': 'sendTestEmail',
        'click #test-smtp': 'checkSmtpAuth'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.email_email_setup;
        this.updatetemplate = window.JST.email_email;
        this.emails = new EmailAccountCollection();
        this.dependencies.push(this.emails);
        this.emails.on('reset', this.renderEmail, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        this.emails.fetch();
        var _this = this;
        this.fetch(_this.renderEmail, _this);
        return this;
    },

    renderEmail: function() {
        var email = {};
        if (this.emails.length > 0) {
            email = this.emails.at(0).toJSON();
        }
        var isEmailNull = true;
        if (Object.keys(email).length > 0) {
            isEmailNull = false;
        }

        $(this.el).html(this.template({
            email: email,
            isEmailNull: isEmailNull
        }));
    },

    renderEmailForm: function() {
        var _this = this;
        var email = {};
        if (this.emails.length > 0) {
            email = this.emails.at(0).toJSON();
        }
        $(this.el).html(this.updatetemplate({
            email: email
        }));

        this.$('#enable_username').closest('.form-group').next().toggle(); //on load hide username div elem
        this.$('#enable_username').click(function() { //on checkbox change switch username hide/show enable/disabled
            $('#username').prop('disabled', !this.checked);
            if (!this.checked) {
                $('#username').val('');
            } // clear username field for erroneous check-uncheck
            $('#enable_username').closest('.form-group').next().toggle(1000);
        });

        this.$('#email-form input').tooltip({
            placement: 'right'
        });

        this.validator = this.$('#email-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                name: 'required',
                sender: 'required',
                password: 'required',
                smtp_server: {
                    required: true,
                    pattern: /^(([a-z\d]|[a-z\d][a-z\d\-]*[a-z\d])\.)*([a-z\d]|[a-z\d][a-z\d\-]*[a-z\d])$/
                },
                receiver: 'required',
                username: {
                    required: '#enable_username:checked' //username field required only if username checkbox checked else empty
                },
                port: {
                    number: true
                }
            },
            messages: {
                smtp_server: {
                    pattern: 'Please provide a correct hostname with only lowercase letters, digits and -'
                }
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
                        _this.emails.fetch({
                            reset: true
                        });
                    },
                    error: function(xhr, status, error) {
                        enableButton(button);
                    }
                });

                return false;
            }
        });
    },

    checkSmtpAuth: function(event) {
        var _this = this;
        var check_auth = true;
        $('.auth-results').hide();
        $('.check-smtp-auth').each(function() {
            if ($(this).is(':visible')) {
                check_auth = check_auth && ($.trim(this.value).length > 0);
            }
        });
        if (check_auth) {
            var data = _this.$('#email-form').getJSON();
            $.ajax({
                url: '/api/email/check-smtp-auth',
                type: 'POST',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(data),
                success: function(response) {
                    var auth_result = JSON.parse(response).smtp_auth ? '#auth_success' : '#auth_failed';
                    $(auth_result).fadeIn(500);
                },
            });
        } else {
            $('#auth_failed').fadeIn(500);
        }
    },

    deleteEmail: function(event) {
        event.preventDefault();
        var _this = this;
        if (confirm('Are you sure about deleting this Email Account?')) {
            $.ajax({
                url: '/api/email',
                type: 'DELETE',
                dataType: 'json',
                success: function() {
                    _this.emails.fetch({
                        reset: true
                    });
                },
                error: function(xhr, status, error) {}
            });
        } else {
            return false;
        }
    },

    sendTestEmail: function(event) {
        event.preventDefault();
        $.ajax({
            url: '/api/email/send-test-email',
            type: 'POST',
            dataType: 'json',
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
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('add_email', function(inputName) {
            var html = '';
            if (inputName == 'name') {
                if ('name' in this.email) {
                    html += 'value="' + this.email.name + '"';
                }
                html += 'title="Name associated with the email, eg: firstname lastname."';
            }
            if (inputName == 'email') {
                if ('sender' in this.email) {
                    html += 'value="' + this.email.sender + '"';
                }
                html += 'title="Rockstor will send email notifications from this address / account. For better security we highly recommend using a separate dedicated email account for this purpose."';
            }
            if (inputName == 'username') { //username value to use for smtp auth
                if ('username' in this.email) {
                    html += 'value="' + this.email.username + '"';
                }
                html += 'title="Enter username required for smtp authentication"';
            }
            if (inputName == 'smtp') {
                if ('smtp_server' in this.email) {
                    html += 'value="' + this.email.smtp_server + '"';
                }
                html += 'title="smtp server url of your email provider. eg: smtp.gmail.com, smtp.zoho.com etc..';
                html += 'If using a Google account please Allow less secure apps to access accounts"';
            }
            if (inputName == 'port') {
                if ('port' in this.email) {
                    html += 'value="' + this.email.port + '"';
                }
                html += 'value=587 title="port number for the smtp server. Defaults to 587"';
            }
            if (inputName == 'recipient') {
                if ('receiver' in this.email) {
                    html += 'value="' + this.email.receiver + '"';
                }
                html += 'title="Rockstor will send email notifications to this address. eg: your personal email."';
            }
            return new Handlebars.SafeString(html);
        });

    }
});