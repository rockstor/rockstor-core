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

UpdateCertificateView = RockstorLayoutView.extend({
    events: {
        'click #update-certificate': 'renderCertificateForm',
        'click #cancel': 'cancel'
    },

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        this.updatetemplate = window.JST.setup_update_certificate;
        this.template = window.JST.setup_certificate_desc;
        this.certificate = new Certificate();
        this.certificates = new Certificate();
        this.dependencies.push(this.certificates);
        this.initHandlebarHelpers();
    },

    render: function() {
        var _this = this;
        this.fetch(this.renderCertificate, this);
        return this;
    },

    renderCertificate: function() {
        var cert = _.first(this.certificates.get('results'));
        this.certificate.set(cert);
        this.renderCertificateDescription();
    },

    renderCertificateDescription: function() {
        var cname = this.certificate.get('name');
        $(this.el).html(this.template({
            'name': cname
        }));
    },

    cancel: function(event) {
        $(this.el).empty();
        var cname = this.certificate.get('name');
        $(this.el).html(this.template({
            'name': cname
        }));
    },

    renderCertificateForm: function() {
        var _this = this;
        $(this.el).html(this.updatetemplate());
        this.$('#update-certificate-form :input').tooltip({
            placement: 'right'
        });
        this.$('#group').chosen();

        this.validator = this.$('#update-certificate-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                certificatename: 'required',
                certificate: 'required',
                privatekey: 'required'
            },
            submitHandler: function() {
                var button = $('#save-certificate');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var certificateName = $('#certificatename').val();
                var certificate = $('#certificate').val();
                var privatekey = $('#privatekey').val();
                var certData = JSON.stringify({
                    'name': certificateName,
                    'cert': certificate,
                    'key': privatekey
                });
                $.ajax({
                    url: '/api/certificate',
                    type: 'POST',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: certData,
                    success: function() {
                        enableButton(button);
                        _this.$('#update-certificate-form :input').tooltip('hide');
                        _this.certificate.set({
                            'name': certificateName
                        });
                        alert('Certificate update successfully. It will take effect now.');
                        location.reload();
                        _this.renderCertificateDescription();
                    },
                    error: function(xhr, status, error) {
                        enableButton(button);
                        _this.$('#update-certificate-form :input').tooltip('hide');
                        var msg = parseXhrError(xhr.responseText);
                        _this.$('.messages').html(msg);
                    },
                });
            }
        });
        return this;
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_message', function() {
            var html = '';
            if (_.isEmpty(name)) {
                html += 'A self signed Certificate created during installation is in use by default.';
            } else {
                html += 'Admin provided Certificate<strong>(' + name + ')</strong> is currently in use.';
            }
            return new Handlebars.SafeString(html);
        });
    }

});