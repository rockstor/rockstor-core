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
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.setup_update_certificate;
    this.certificate = new Certificate();
    this.dependencies.push(this.certificate);
  },

  render: function() {
    this.fetch(this.renderCertificateForm, this);
    return this;
  },

  renderCertificateForm: function() {
    var _this = this;
    $(this.el).html(this.template());
    this.$('#update-certificate-form :input').tooltip({placement: 'right'});
    this.$('#group').chosen();

    this.validator = this.$("#update-certificate-form").validate({
      onfocusout: false,
      onkeyup: false,
      submitHandler: function() {
    	  var button = $('#update-certificate');
          if (buttonDisabled(button)) return false;
          disableButton(button);
    	  var certificateName = $('#certificatename').val();
    	  var certificate = $('#certificate').val();
    	  var privatekey = $('#privatekey').val();
    	  var certData = JSON.stringify({"certificatename": certificateName,
			    "certificate": certificate, "privatekey": privatekey});
    	  console.log("certificate data: "+data);
          var jqxhr = $.ajax({
              url: '/api/certificate',
              type: 'POST',
              dataType: 'json',
	          contentType: 'application/json',
              data: certData
          });
          jqxhr.done(function() {
              enableButton(button);
              _this.$('#update-certificate-form input').tooltip('hide');
           });

           jqxhr.fail(function(xhr, status, error) {
             enableButton(button);
           });
          return false;
      }
    });
    return this;
  }
});
