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

ConfigureServiceView = RockstoreLayoutView.extend({
  events: {
    "click #cancel": "cancel"
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.serviceName = this.options.serviceName;
    // set template
    this.template = window.JST['services_configure_' + this.serviceName];
    this.rules = {
      ntpd: { server: 'required' },
      nis: { domain: 'required', server: 'required' },
    }
    this.formName = this.serviceName + '-form';
    this.service = new Service({name: this.serviceName});
    this.dependencies.push(this.service);
  },

  render: function() {
    this.fetch(this.renderServiceConfig, this);
    return this;
  },

  renderServiceConfig: function() {
    var _this = this;
    var config = this.service.get('config');
    var configObj = {};
    if (config != null) {
      configObj = JSON.parse(this.service.get('config'));
    }
    $(this.el).html(this.template({service: this.service, config: configObj}));

    this.validator = this.$('#' + this.formName).validate({
      onfocusout: false,
      onkeyup: false,
      rules: this.rules[this.serviceName],
      //messages: {
        //password_confirmation: {
          //equalTo: "The passwords do not match"
        //}
      //},
      submitHandler: function() {
        var button = _this.$('#submit');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var data = JSON.stringify({config: _this.$('#' + _this.formName).getJSON()});
        $.ajax({
          url: "/api/sm/services/" + _this.serviceName + "/config",
          type: "POST",
          contentType: 'application/json',
          dataType: "json",
          data: data,
          success: function(data, status, xhr) {
            enableButton(button);
            app_router.navigate("services", {trigger: true});
          },
          error: function(xhr, status, error) {
            enableButton(button);
            var msg = parseXhrError(xhr)
            if (_.isObject(msg)) {
              _this.validator.showErrors(msg);
            } else {
              _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
            }
          }
        });
        return false;
      }
    });
    return this;
  },

  cancel: function() {
    app_router.navigate("services", {trigger: true});
  }

});


