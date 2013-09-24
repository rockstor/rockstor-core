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

ServicesView = Backbone.View.extend({
  
  events: {
    'click .slider-stop': "stopService",
    'click .slider-start': "startService",
    'click .configure': "configureService",

  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.services_services;
    this.collection = new ServiceCollection();
    this.collection.on("reset", this.renderServices, this);
    this.actionMessages = {
      'start': 'started',
      'stop': 'stopped',
      'restart': 'restarted',
      'reload': 'reloaded'
    }
  },

  render: function() {
    //this.fetch(this.renderStatus, this);
    this.collection.fetch();
    return this;
  },

  renderServices: function() {
    var _this = this;
    $(this.el).empty();
    
    $(this.el).append(this.template({
      services: this.collection
    }));
    this.$('input.service-status').simpleSlider({
      "theme": "volume",
      allowedValues: [0,1],
      snap: true 
    });

    this.$('input.service-status').bind('slider:changed', function(event, data) {
      var val = data.value.toString();
      var serviceName = $(event.currentTarget).data('service-name'); 
      startSpan = _this.$('span.slider-start[data-service-name="' + serviceName + '"]');
      if (val == "0") {
        startSpan.removeClass('on');
      } else {
        startSpan.addClass('on');
      }
    });
    
    /*
    this.intervalId = window.setInterval(function() {
      return function() { _this.updateStatus(_this); }
    }(), 5000);
   */
  },
  
  doCommand: function(name, command) {
    
    $.ajax({
      url: "/api/sm/services/" + name + "/" + command,
      type: "POST",
      dataType: "json",
      success: function(data, status, xhr) {
        var action = _this.actionMessages[command];
        showSuccessMessage(name + ' ' + action + ' successfully');
      },
      error: function(xhr, status, error) {
        var msg = parseXhrError(xhr)
        _this.$(".share-messages").html("<label class=\"error\">" + msg + "</label>");
      }
    });

  },

  startService: function(event) {
    var _this = this;
    var span = $(event.currentTarget);
    var serviceName = span.data('service-name');
    var commandStatus = this.$('span.command-status[data-service-name="' + serviceName + '"]')
    commandStatus.html('<img src="/img/ajax-loader.gif"></img>');
    $.ajax({
      url: "/api/sm/services/" + serviceName + "/start",
      type: "POST",
      dataType: "json",
      success: function(data, status, xhr) {
        // add highlight class
        span.addClass('on');
        _this.$('input[data-service-name="' + serviceName + '"]').simpleSlider('setValue',1);
        commandStatus.html('&nbsp;');
      },
      error: function(xhr, status, error) {
        var msg = parseXhrError(xhr)
        commandStatus.html('<i class="icon-exclamation-sign"></i>');
      }
    });
    
  },

  stopService: function(event) {
    var _this = this;
    var span = $(event.currentTarget);
    var serviceName = $(event.currentTarget).data('service-name');
    var commandStatus = this.$('span.command-status[data-service-name="' + serviceName + '"]')
    commandStatus.html('<img src="/img/ajax-loader.gif"></img>');
    $.ajax({
      url: "/api/sm/services/" + serviceName + "/stop",
      type: "POST",
      dataType: "json",
      success: function(data, status, xhr) {
        startSpan = _this.$('span.slider-start[data-service-name="' + serviceName + '"]');
        startSpan.removeClass('on');
        _this.$('input[data-service-name="' + serviceName + '"]').simpleSlider('setValue',0);
        commandStatus.html('&nbsp;');
      },
      error: function(xhr, status, error) {
        var msg = parseXhrError(xhr)
        commandStatus.html('<i class="icon-exclamation-sign"></i>');
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
        data = data.results;
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

  configureService: function(event) {
    event.preventDefault();
  },

  cleanup: function() {
    if (!_.isUndefined(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  }

});

