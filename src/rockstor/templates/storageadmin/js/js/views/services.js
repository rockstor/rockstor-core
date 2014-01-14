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
    "click #join-domain": "showJoinDomainPopup",
  },

  initialize: function() {
    this.template = window.JST.services_services;
    this.paginationTemplate = window.JST.common_pagination;
    this.collection = new ServiceCollection();
    this.actionMessages = {
      'start': 'started',
      'stop': 'stopped',
      'restart': 'restarted',
      'reload': 'reloaded'
    }
    this.updateFreq = 5000;
  },

  render: function() {
    var _this = this;
    this.collection.fetch({
      success: function(collection, response, options) {
        _this.renderServices();
      }
    });
    this.updateStatus();
    return this;
  },

  renderServices: function() {
    var _this = this;
    $(this.el).empty();
    var adConfigStr = this.collection.get('winbind').get('config');
    if (!_.isNull(adConfigStr)) {
      this.adServiceConfig = JSON.parse(adConfigStr);
    }
    if (_.isNull(this.adServiceConfig) || _.isUndefined(this.adServiceConfig)) {
      this.adServiceConfig = {};
    }
    $(this.el).append(this.template({
      services: this.collection,
      adServiceConfig: this.adServiceConfig
    }));
    this.$(".ph-pagination").html(this.paginationTemplate({
      collection: this.collection
    }));
    this.$('input.service-status').simpleSlider({
      "theme": "volume",
      allowedValues: [0,1],
      snap: true 
    });
    
    this.$('input.service-status').each(function(i, el) {
      var slider = $(el).data('slider-object');
      // disable track and dragger events to disable slider
      slider.trackEvent = function(e) {};
      slider.dragger.unbind('mousedown');
    });
    this.$('.simple-overlay').overlay({load: false}); 
    
    // join domain modal 
    this.$('#join-domain-modal').modal({
      show: false
    });

    this.$('#join-domain-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        administrator: 'required',
        password: 'required'
      },
      submitHandler: function() {
        var button = _this.$('#join-domain-submit');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var data = JSON.stringify(_this.$('#join-domain-form').getJSON());
        $.ajax({
          url: "/api/commands/join-winbind-domain",
          type: "POST",
          contentType: 'application/json',
          dataType: "json",
          data: data,
          success: function(data, status, xhr) {
            enableButton(button);
            _this.$('#join-domain-status').html('<span class="alert alert-success alert-small">Join Ok</span>');
            _this.$('#join-domain-modal').modal('hide');
          },
          error: function(xhr, status, error) {
            enableButton(button);
            var msg = parseXhrError(xhr)
            _this.$('#join-domain-err').html(msg);
            _this.$('#join-domain-status').html('<span class="alert alert-error alert-small">Not Joined</span>');
          }
        });
        return false;
      }

    });
    var adService = this.collection.get('winbind');
    if (adService.get('status') && 
        (this.adServiceConfig.security == 'ads' || 
         this.adServiceConfig.security == 'domain')) {
      this.showJoinDomainStatus();
    }
  },
  
  startService: function(event) {
    var _this = this;
    var serviceName = $(event.currentTarget).data('service-name'); 
    // if already started, return
    if (this.getSliderVal(serviceName).toString() == "1") return; 
    this.stopPolling();
    this.setStatusLoading(serviceName, true);
    $.ajax({
      url: "/api/sm/services/" + serviceName + "/start",
      type: "POST",
      dataType: "json",
      success: function(data, status, xhr) {
        _this.highlightStartEl(serviceName, true);
        _this.setSliderVal(serviceName, 1); 
        _this.setStatusLoading(serviceName, false);
        _this.updateStatus();
      },
      error: function(xhr, status, error) {
        _this.setStatusError(serviceName, xhr);
        _this.updateStatus();
      }
    });
  },

  stopService: function(event) {
    var _this = this;
    var serviceName = $(event.currentTarget).data('service-name'); 
    // if already stopped, return
    if (this.getSliderVal(serviceName).toString() == "0") return; 
    this.stopPolling();
    this.setStatusLoading(serviceName, true);
    $.ajax({
      url: "/api/sm/services/" + serviceName + "/stop",
      type: "POST",
      dataType: "json",
      success: function(data, status, xhr) {
        _this.highlightStartEl(serviceName, false);
        _this.setSliderVal(serviceName, 0); 
        _this.setStatusLoading(serviceName, false);
        _this.updateStatus();
      },
      error: function(xhr, status, error) {
        _this.setStatusError(serviceName, xhr);
        _this.updateStatus();
      }
    });
  },

  configureService: function(event) {
    event.preventDefault();
    var _this = this;
    var serviceName = $(event.currentTarget).data('service-name'); 
    app_router.navigate('services/' + serviceName + '/edit', {trigger: true});
  },

  setStatusLoading: function(serviceName, show) {
    var statusEl = this.$('div.command-status[data-service-name="' + serviceName + '"]')
    if (show) {
      statusEl.html('<img src="/img/ajax-loader.gif"></img>');
    } else {
      statusEl.empty();
    }
  },

  setStatusError: function(serviceName, xhr) {
    var statusEl = this.$('div.command-status[data-service-name="' + serviceName + '"]')
    var msg = parseXhrError(xhr)
    // remove any existing error popups
    $('body').find('#' + serviceName + 'err-popup').remove();
    // add icon and popup
    statusEl.empty();
    var icon = $('<i>').addClass('icon-exclamation-sign').attr('rel', '#' + serviceName + '-err-popup');
    statusEl.append(icon);
    var errPopup = this.$('#' + serviceName + '-err-popup');
    var errPopupContent = this.$('#' + serviceName + '-err-popup > div');
    errPopupContent.html(msg);
    statusEl.click(function(){ errPopup.overlay().load(); });
  },

  highlightStartEl: function(serviceName, on) {
    var startEl = this.$('div.slider-start[data-service-name="' + serviceName + '"]');
    if (on) {
      startEl.addClass('on');
    } else {
      startEl.removeClass('on');
    }
  },

  setSliderVal: function(serviceName, val) {
    this.$('input[data-service-name="' + serviceName + '"]').simpleSlider('setValue',val);
  },

  getSliderVal: function(serviceName) {
    return this.$('input[data-service-name="' + serviceName + '"]').data('slider-object').value;
  },

  cleanup: function() {
    this.stopPolling();
  },

  updateStatus: function() {
    var _this = this;
    this.startTime = new Date().getTime();
    _this.collection.fetch({
      silent: true,
      success: function(collection, response, options) {
        _this.collection.each(function(service) {
          var serviceName = service.get('name');
          if (service.get('status')) {
            _this.highlightStartEl(serviceName, true);
            _this.setSliderVal(serviceName, 1); 
          } else {
            _this.highlightStartEl(serviceName, false);
            _this.setSliderVal(serviceName, 0); 
          }
        }); 
        var currentTime = new Date().getTime();
        var diff = currentTime - _this.startTime;
        if (diff > _this.updateFreq) {
          _this.updateStatus();
        } else {
          _this.timeoutId = window.setTimeout( function() { 
            _this.updateStatus();
          }, _this.updateFreq - diff);
        }
      } 
    });
  },

  stopPolling: function() {
    var _this = this;
    if (!_.isUndefined(this.timeoutId)) {
      window.clearInterval(this.timeoutId);
    }
  },

  showJoinDomainPopup: function(event) {
    if (!$(event.currentTarget).hasClass('disabled')) {
      this.$('#join-domain-modal').modal('show');
    }
  },

  showJoinDomainStatus: function() {
    var _this = this;
    $.ajax({
      url: "/api/commands/winbind-domain-status",
      type: "POST",
      contentType: 'application/json',
      dataType: "json",
      success: function(data, status, xhr) {
        if (data == 'Yes') {
          _this.$('#join-domain-status').html('<span class="alert alert-success alert-small">Join Ok</span>');
        } else {
          _this.$('#join-domain-status').html('<span class="alert alert-error alert-small"><i class="icon-exclamation-sign"></i>&nbsp;Not Joined</span>');
        }
      },
      error: function(xhr, status, error) {
      }
    });
  }

});

// Add pagination
Cocktail.mixin(ServicesView, PaginationMixin);

