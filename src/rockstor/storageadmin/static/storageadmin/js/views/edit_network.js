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

EditNetworkView = RockstorLayoutView.extend({
  events: {
    'click #cancel': 'cancel',
    'change #boot_proto': 'changeBootProtocol'
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.network_edit_network;
    this.name = this.options.name;
    this.network = new NetworkInterface({name: this.name});
  },
  
  render: function() {
    var _this = this;
    this.network.fetch({
      success: function(collection, response, options) {
        _this.renderNetwork();
      }
    });
    return this;
  },

  renderNetwork: function() {
    var _this = this;
    $(this.el).html(this.template({network: this.network}));
    
    this.$('#edit-network-form :input').tooltip({placement: 'right'});
    
    this.validator = this.$("#edit-network-form").validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
      },
      messages: {
      },
      
      submitHandler: function() {
        var button = _this.$('#submit');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var network = new NetworkInterface({name: _this.name});
        var data = _this.$('#edit-network-form').getJSON();
        if (_this.$("#itype").prop("checked")) {
          data.itype = 'management';
        } else {
          data.itype = '';
        }
        data.boot_protocol = data.boot_proto;
        network.save(data, {
          success: function(model, response, options) {
            app_router.navigate("network", {trigger: true});
          },
          error: function(model, xhr, options) {
            enableButton(button);
          }
        });
        return false;  
      }
    });
  },
  
  changeBootProtocol: function(event) {
    if (this.$('#boot_proto').val() == 'static') {
      this.$('#ipaddr').removeAttr('disabled');
      this.$('#netmask').removeAttr('disabled');
      this.$('#gateway').removeAttr('disabled');
      this.$('#domain').removeAttr('disabled');
      this.$('#dns_servers').removeAttr('disabled');
      this.$('#edit-network-form :input').tooltip({placement: 'right'});
    } else {
      this.$('#ipaddr').attr('disabled', 'disabled');
      this.$('#netmask').attr('disabled', 'disabled');
      this.$('#gateway').attr('disabled', 'disabled');
      this.$('#domain').attr('disabled', 'disabled');
      this.$('#dns_servers').attr('disabled', 'disabled');
      this.$('#edit-network-form :input').tooltip('hide');
    }

  },
  
  cancel: function() {
    app_router.navigate("network", {trigger: true});
  }

});



