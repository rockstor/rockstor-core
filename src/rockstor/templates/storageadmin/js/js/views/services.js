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

/* Services */

ServicesView = RockstoreLayoutView.extend({
  
  events: {
    'click .service-command': 'doCommand',
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.services_services;
    this.snames = ['nfs', 'samba', 'sftp', 'ldap', 'ad', 'iscsi'];
    this.services = {};
    _.each(this.snames, function(name) {
      console.log('creating service model for ' + name);
      this.services[name] = new Service({name: name});
    }, this);
    _.each(_.keys(this.services), function(name) {
      console.log('adding dependency for ' + name);
      this.dependencies.push(this.services[name]);
    }, this);
    this.actionMessages = {
      'start': 'started',
      'stop': 'stopped',
      'restart': 'restarted',
      'reload': 'reloaded'
    }
  },

  render: function() {
    console.log('in services render');
    this.fetch(this.renderStatus, this);
    return this;
  },

  renderStatus: function() {
    $(this.el).empty();
    console.log('rendering template');
    
    $(this.el).append(this.template({
      services: this.services
    }));
    
    var _this = this;
    this.intervalId = window.setInterval(function() {
      return function() { _this.updateStatus(_this); }
    }(), 5000)
  },
  
  doCommand: function(event) {
    event.preventDefault();
    var _this = this;
    var tgt = $(event.currentTarget);
    var inputType = tgt.attr('type');
    var command = null;
    if (inputType == 'checkbox') {
      command = _.isUndefined(tgt.attr('checked')) ? 'stop' : 'start';
    } else {
      command = tgt.attr('data-command');
    }
    var name = tgt.attr('data-service-name');
    var service = this.services[name];
    
    $.ajax({
      url: "/api/sm/services/" + name + "/",
      type: "PUT",
      dataType: "json",
      data: {command: command}, 
      success: function(data, status, xhr) {
        console.log('service saved successfully');
        var action = _this.actionMessages[command];
        showSuccessMessage(name + ' ' + action + ' successfully');
      },
      error: function(xhr, status, error) {
        showError(xhr.responseText);	
      }
    });

  },

  updateStatus: function(context) {
    var _this = context;
    showLoadingIndicator('service-loading-indicator', _this);
    $.ajax({
      url: "/api/sm/services/", 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        hideLoadingIndicator('service-loading-indicator', _this);
        _.each(data, function(service) {
          var name = service.name;
          status_elem = _this.$('#'+name+'-status');
          update_elem = _this.$('#'+name+'-update');
          if (!_.isNull(status_elem) && !_.isUndefined(status_elem)) {
            if (service.status) {
              status_elem.html('<div class="service-status running"></div>');
              update_elem.html('<span href="#" id="'+name+'-start" class="service-command" data-service-name="'+name+'" data-command="start">Start</span>&nbsp;&nbsp;&nbsp;&nbsp;<a href="#" id="'+name+'-stop" class="service-command" data-service-name="'+name+'" data-command="stop">Stop</a>&nbsp;&nbsp;&nbsp;&nbsp;<a href="#" id="'+name+'-restart" class="service-command" data-service-name="'+name+'" data-command="restart">Restart</a>&nbsp;&nbsp;&nbsp;&nbsp;<a href="#" id="'+name+'-reload" class="service-command" data-service-name="'+name+'" data-command="reload">Reload</a>');
            } else {
              status_elem.html('<div class="service-status stopped"></div>');
              update_elem.html('<a href="#" id="'+name+'-start" class="service-command" data-service-name="'+name+'" data-command="start">Start</a>&nbsp;&nbsp;&nbsp;&nbsp;<span href="#" id="'+name+'-stop" class="service-command" data-service-name="'+name+'" data-command="stop">Stop</span>&nbsp;&nbsp;&nbsp;&nbsp;<span href="#" id="'+name+'-restart" class="service-command" data-service-name="'+name+'" data-command="restart">Restart</span>&nbsp;&nbsp;&nbsp;&nbsp;<span href="#" id="'+name+'-reload" class="service-command" data-service-name="'+name+'" data-command="reload">Reload</span>');
            }
          }
        });
      },
      error: function(xhr, status, error) {
        hideLoadingIndicator('service-loading-indicator', _this);
      }

    });
  },

  cleanup: function() {
    console.log('clearing setInterval'); 
    if (!_.isUndefined(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  }

});

