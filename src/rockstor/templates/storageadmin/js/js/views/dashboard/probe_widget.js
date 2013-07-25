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

ProbeWidget = RockStorWidgetView.extend({

  events: {
    'click .start-probe' : 'startProbe',
    'click .stop-probe' : 'stopProbe',
    'click .resize-widget': 'resize',
    'click .close-widget': 'close',
    'click .probe-select': 'selectProbe',
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_probe;
    this.probe_list_template = window.JST.dashboard_widgets_probe_list;
    this.displayName = this.options.displayName;
    this.timestamp = 0;
    // periodically check status while polling for data is 
    // going on. this interval controls the frequence
    this.scInterval = 0; 
    this.probeStates = {
      STOPPED: 'stopped',
      CREATED: 'created',
      RUNNING: 'running',
      ERROR: 'error',
    };
    this.probeEvents = {
      START: 'start',
      RUN: 'run',
      STOP: 'stop',
      ERROR: 'error',
      ERROR_START: 'error_start',
      ERROR_RUN: 'error_run',
    };
    // time between successive ajax calls for state changes 
    this.statePollInterval = 5000;
    // time between successive ajax calls for probe data
    this.dataPollInterval = 2000;
    this.renderTimers = [];
  },

  render: function() {
    this.constructor.__super__.render.apply(this, arguments);
    var _this = this;
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName
    }));
    this.disableStartProbe();
    this.disableStopProbe();
    this.displayProbeList();
    this.initializeProbe('nfs-distrib');
    return this;
  },

  selectProbe: function(event) {
    event.preventDefault(); 
    if ($(event.currentTarget).hasClass('disabled')) {
      return false;
    }
    probeName = $(event.currentTarget).attr('data-probe-name');
    this.$('#selected-probe-name').html(probeName);
    logger.debug(probeName + ' selected');
    this.probe = this.createNewProbe(probeName);
    this.probe.trigger(this.probeEvents.STOP);
  },

  initializeProbe: function(name) {
    //checks if probe is running and if so, loads it and displays
    var _this = this;
    // check probe status
    this.probes = new ProbeCollection([],{name: name});
    this.probes.fetch({
      success: function(collection, response, options) {
        if (collection.length > 0) {
          _this.probe = _this.probes.at(0);
          if (_this.probe.get('state') == _this.probeStates.RUNNING) {
            // probe was run before and is running
            _this.disableProbeSelect();
            this.$('#selected-probe-name').html(_this.probe.get('name'));
            _this.setProbeEvents(_this.probe);
            _this.probe.trigger(_this.probeEvents.RUN);
          } else {
            // probe was run before but is not running
            //_this.probe = _this.createNewProbe(name);
            //_this.probe.trigger(_this.probeEvents.STOP);
          }
        } else {
          // probe was not run before
          //_this.probe = _this.createNewProbe(name);
          //_this.probe.trigger(_this.probeEvents.STOP);
        }
      },
      error: function(collection, response, options) {
        // probe was not run before
        //_this.probe = _this.createNewProbe(name);
        //_this.probe.trigger(_this.probeEvents.STOP);
      }

    });
  },
  
  startProbe: function(event) {
    var _this = this;
    if (!_.isUndefined(event)) {
      event.preventDefault();
    }
    if (buttonDisabled(this.$('.start-probe'))) {
      return false;
    }
    // set the id to new probe if it was run before
    if (!_.isNull(this.probe.id)) {
      this.probe = this.createNewProbe(this.probe.get('name'));
    }
    this.disableProbeSelect();
    this.probe.save(null, {
      success: function(model, response, options) {
        if (_this.probe.get('state') == _this.probeStates.CREATED) {
          _this.probe.trigger(_this.probeEvents.START);
        } else {
          _this.probe.trigger(_this.probeEvents.ERROR_START);
        }
      },
      error: function(model, response, options) {
        _this.probe.trigger(_this.probeEvents.ERROR_START);
      }
    });
  },

  waitTillRunning: function() {
    var _this = this;
    logger.debug('polling till running');
    this.statusIntervalId = window.setInterval(function() {
      return function() { 
        _this.probe.fetch({
          success: function(model, response, options) {
            if (_this.probe.get('state') == _this.probeStates.RUNNING) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to running state
              _this.probe.trigger(_this.probeEvents.RUN);
            } else if (_this.probe.get('state') == _this.probeStates.ERROR) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to error state
              _this.probe.trigger(_this.probeEvents.ERROR);
            }

          },
          error: function(model, response, options) {
            // stop polling for status
            window.clearInterval(_this.statusIntervalId);
            // go to error state
            _this.probe.trigger(_this.probeEvents.ERROR);
          }

        });
      }
    }(), this.statePollInterval)

  },

  // poll till data is available
  pollForDataReady: function(recipe_uri) {
    var _this = this;
    logger.debug('starting polling for data');
    this.dataIntervalId = window.setInterval(function() {
      return function() { 
        $.ajax({
          url: _this.probe.dataUrl(),
          type: 'GET',
          dataType: "json",
          global: false, // dont show global loading indicator
          success: function(data, textStatus, jqXHR) {
            window.clearInterval(_this.dataIntervalId);
            _this.$('#probe-status').html(': Probe Running - receiving data');
            _this.startRender();
          },
          error: function(jqXHR, textStatus, error) {
            logger.debug(error);
            window.clearInterval(_this.dataIntervalId);
            _this.probe.trigger(_this.probeEvents.ERROR);
          }
        });

        //_this.probe.fetch({
          //success: function(model, response, options) {
            //window.clearInterval(_this.dataIntervalId);
            //_this.startRender();
          //},
          //error: function(model, response, options) {
            //window.clearInterval(_this.dataIntervalId);
            //_this.probe.trigger(_this.probeEvents.ERROR);
          //},
        //});
      }
    }(), this.dataPollInterval);

  },

  stopProbe: function(event) {
    var _this = this;
    if (!_.isUndefined(event)) {
      event.preventDefault();
    }
    if (buttonDisabled(this.$('.stop-probe'))) {
      return false;
    }
    if (!_.isUndefined(this.statusIntervalId) && !_.isNull(this.statusIntervalId)) {
      window.clearInterval(this.dataIntervalId);
    }
    if (!_.isUndefined(this.dataIntervalId) && !_.isNull(this.dataIntervalId)) {
      window.clearInterval(this.dataIntervalId);
    }
    $.ajax({
      url: this.probe.url() + '/stop/',
      type: 'POST',
      data: {},
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, textStatus, jqXHR) {
        _this.probe.trigger(_this.probeEvents.STOP);
      },
      error: function(jqXHR, textStatus, error) {
        logger.debug(error);
        _this.probe.trigger(_this.probeEvents.ERROR);
      }
    });
    this.enableProbeSelect();

  },

  makeSeries: function(data) {
    var series = [[]];
    for (i=0; i<10; i++) {
      series[0].push([i,data[i]]);
    }
    return series;
  },

  start: function() {
    logger.debug('probe created');
    this.disableStartProbe();
    this.enableStopProbe();
    this.$('#probe-status').html(': Probe created - waiting for status');
    this.waitTillRunning();
  },
  
  run: function() {
    logger.debug('probe running');
    this.disableStartProbe();
    this.enableStopProbe();
    this.$('#probe-status').html(': Probe running - waiting for data');
    // start polling for Data
    this.pollForDataReady();

  },

  stop: function() {
    logger.debug('probe stopped');
    this.enableStartProbe();
    this.disableStopProbe();
    this.$('#probe-status').html(': Probe stopped');
    if (!_.isUndefined(this.probe.id) && !_.isNull(this.probe.id)) {
      this.stopRender();
    }
  },

  error: function() {
    logger.debug('probe error');
    this.enableStartProbe();
    this.disableStopProbe();
    this.probeState = this.probeStates.ERROR;
    this.$('#probe-status').html(': Error!');
  },

  startRender: function() {
    var _this = this;
    var tmp = _.find(RockStorProbeMap, function(p) {
      return p.name == _this.probe.get('name');
    });
    logger.debug(tmp);
    var viewName = tmp.view;
    logger.debug('found probe view ' + viewName);
    var probeClass = window[viewName];
    if (!_.isUndefined(probeClass) && !_.isNull(probeClass)) {
      this.currentProbeView = new window[viewName]({probe: this.probe});
      this.$('#probe-content').empty();
      this.$('#probe-content').append(this.currentProbeView.render().el);
    }
  },

  stopRender: function() {
    var _this = this;
    if (!_.isUndefined(this.currentProbeView) && !_.isNull(this.currentProbeView)) {
      this.currentProbeView.cleanup();
    }
    //this.$('#probe-content').empty();
  },

  setProbeEvents: function(probe) {
    probe.on(this.probeEvents.START, this.start, this);
    probe.on(this.probeEvents.RUN, this.run, this);
    probe.on(this.probeEvents.STOP, this.stop, this);
    probe.on(this.probeEvents.ERROR, this.error, this);
    probe.on(this.probeEvents.ERROR_START, this.error, this);
    probe.on(this.probeEvents.ERROR_RUN, this.error, this);
  },

  createNewProbe: function(name) {
    probe = new Probe({
      name: name,
      state: this.probeStates.STOPPED
    })
    this.setProbeEvents(probe);
    return probe;
  },

  disableStartProbe: function() {
    disableButton(this.$('.start-probe'));
  },
  enableStartProbe: function() {
    enableButton(this.$('.start-probe'));
  },
  disableStopProbe: function() {
    disableButton(this.$('.stop-probe'));
  },
  enableStopProbe: function() {
    enableButton(this.$('.stop-probe'));
  },
  disableProbeSelect: function() {
    logger.debug('disabling probe select');
    this.$('.probe-select').addClass('disabled');
  },
  enableProbeSelect: function() {
    logger.debug('enabling probe select');
    this.$('.probe-select').removeClass('disabled');
  },
  displayProbeList: function() {
    var _this = this;
    $.ajax({
      //url: '/api/recipes/nfs/123?t=' + this.timestamp,
      url: '/api/sm/sprobes/',
      type: 'GET',
      global: false, // dont show global loading indicator
      success: function(data, textStatus, jqXHR) {
        _this.$('#probe-list-container').append(_this.probe_list_template({probes: data}));
      },
      error: function(jqXHR, textStatus, error) {
        logger.debug(error);
      }
    });

  },

});


cubism.context.prototype.nfs = function() {
  var source = {},
      context = this;

  source.metric = function(nfsMetric, attrName, probeDataUrl) {
    return context.metric(function(start, stop, step, callback) {
      $.ajax({
        //url: '/api/recipes/nfs/123?t=' + this.timestamp,
        url: probeDataUrl,
        type: 'GET',
        global: false, // dont show global loading indicator
        success: function(data, textStatus, jqXHR) {
          tmp = data.map(function(d) { return d[attrName]; });
          callback(null, tmp);
        },
        error: function(jqXHR, textStatus, error) {
          window.clearInterval(_this.dataIntervalId);
          logger.debug(error);
          // TODO show error message on widget
        }
      });
    }, nfsMetric);
  };

  source.toString = function() {
    return nfsMetric;
  };

  return source;
};


RockStorWidgets.available_widgets.push({ 
  name: 'smart_probe', 
  displayName: 'Smart Probes', 
  view: 'ProbeWidget',
  description: 'Smart Probes that display nfs call distribution',
  defaultWidget: true,
  rows: 2,
  cols: 3,
  category: 'Storage',
  position: 3
});

