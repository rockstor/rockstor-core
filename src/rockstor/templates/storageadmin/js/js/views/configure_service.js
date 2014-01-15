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
    "click #cancel": "cancel",
    "click #security": "toggleFormFields",
    "click #enabletls": "toggleCertUrl",
  },

  initialize: function() {
    // call initialize of base
    var _this = this;
    this.constructor.__super__.initialize.apply(this, arguments);
    this.serviceName = this.options.serviceName;
    // set template
    this.template = window.JST['services_configure_' + this.serviceName];
    this.rules = {
      ntpd: { server: 'required' },
      nis: { domain: 'required', server: 'required' },
      winbind: {domain: 'required', controllers: 'required', 
        security: 'required', 
        realm: {
          required: {
            depends: function(element) {
              return (_this.$('#security').val() == 'ads');
            }
          }
        },
        templateshell: {
          required: {
            depends: function(element) {
              return ((_this.$('#security').val() == 'ads') ||
                      (_this.$('#security').val() == 'domain'));
            }
          }
        }
      },
      ldap: {
        server: 'required',
        basedn: 'required',
        cert: {
          required: {
            depends: function(element) {
              return _this.$('#enabletls').prop('checked'); 
            }
          }
        }
      }
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

    this.$('#nis-form :input').tooltip();
    this.$('#ldap-form :input').tooltip();
    this.$('#ntpd-form :input').tooltip();
    this.$('#winbind-form #domain').tooltip({
      html: true,
      placement: 'right',
      title: 'Specifies the Windows Active Directory or domain controller to connect to.'
    });
    this.$('#winbind-form #security').tooltip({
      html: true,
      placement: 'right',
      title: "<strong>Security Model</strong> — Allows you to select a security model, which configures how clients should respond to Samba. The drop-down list allows you select any of the following:<br> \
      <ul>\
      <li><strong>ads</strong> — This mode instructs Samba to act as a domain member in an Active Directory Server (ADS) realm. To operate in this mode, the krb5-server package must be installed, and Kerberos must be configured properly.</li> \
      <li><strong>domain</strong> — In this mode, Samba will attempt to validate the username/password by authenticating it through a Windows NT Primary or Backup Domain Controller, similar to how a Windows NT Server would.</li> \
      <li><strong>server</strong> — In this mode, Samba will attempt to validate the username/password by authenticating it through another SMB server (for example, a Windows NT Server). If the attempt fails, the user mode will take effect instead.</li> \
      <li><strong>user</strong> — This is the default mode. With this level of security, a client must first log in with a valid username and password. Encrypted passwords can also be used in this security mode.</li> \
      </ul>"
    });
    this.$('#winbind-form #realm').tooltip({
      html: true,
      placement: 'right',
      title: 'When the ads Security Model is selected, this allows you to specify the ADS Realm the Samba server should act as a domain member of.'
    });
    this.$('#winbind-form #controllers').tooltip({
      html: true,
      placement: 'right',
      title: 'Use this option to specify which domain controller winbind should use.'
    });
    this.$('#winbind-form #templateshell').tooltip({
      html: true,
      placement: 'right',
      title: 'When filling out the user information for a Windows NT user, the winbindd daemon uses the value chosen here to to specify the login shell for that user.'
    });
    
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
  },

  toggleFormFields: function() {
    if (this.$('#security').val() == 'ads') {
      this.$('#realm').removeAttr('disabled');
    } else {
      this.$('#realm').attr('disabled', 'true');    	
    }
    if (this.$('#security').val() == 'ads' 
        || this.$('#security').val() == 'domain') {
      this.$('#templateshell').removeAttr('disabled');
    } else {
      this.$('#templateshell').attr('disabled', 'true');
    }
  },

  toggleCertUrl: function() {
    var cbox = this.$('#enabletls');
    if (cbox.prop('checked')) {
      this.$('#cert-ph').css('visibility','visible');
    } else {
      this.$('#cert-ph').css('visibility','hidden');
    }
  },


});


