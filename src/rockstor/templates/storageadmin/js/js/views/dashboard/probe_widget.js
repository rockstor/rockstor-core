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

  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_probe;
    this.top_shares_template = window.JST.dashboard_widgets_top_shares;
    this.displayName = this.options.displayName;
    this.timestamp = 0;
    // periodically check status while polling for data is 
    // going on. this interval controls the frequence
    this.scInterval = 0; 
    //this.nfsData = [[[1,10],[2,10], [3,10], [4,10], [5,10], [6,10],
      //[7,10], [8,10], [9,10], [10,10]]];
    this.nfsData = [0,0,0,0,0,0,0,0,0,0];
		this.graphOptions = {
			lines: { show: true },
			points: { show: true },
			xaxis: {
        min: 0,
        max: 10,
				tickDecimals: 0,
				tickSize: 1
			},
      yaxis: {
        min: 0,
        max: 100
      }
		};
    /*
    this.nfsMetricsAll = [
      { name: 'Reads/sec', min: 20, max: 30 },
      { name: 'Writes/sec', min: 50, max: 60 },
      { name: 'Lookups/sec', min: 20, max: 30 },
      { name: 'Bytes read/sec', min: 500000, max: 600000 },
      { name: 'Bytes written/sec', min: 700000, max: 800000 }
    ]; 
    */
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
    var series = [[]];
    for (i=0; i<10; i++) {
      series[0].push([i, this.nfsData[i]]);
    }

    //$.plot(this.$('#nfsgraph'), this.makeSeries(this.nfsData), this.graphOptions);
    this.initializeProbe('nfs-distrib');
    return this;
  },

  initializeProbe: function(name) {
    var _this = this;
    // check probe status
    this.probes = new ProbeCollection([],{name: name});
    logger.debug('probes url is ' + this.probes.url());
    this.probes.fetch({
      success: function(collection, response, options) {
        if (collection.length > 0) {
          _this.probe = _this.probes.at(0);
          if (_this.probe.get('state') == _this.probeStates.RUNNING) {
            // probe was run before and is running
            _this.setProbeEvents(_this.probe);
            _this.probe.trigger(_this.probeEvents.RUN);
          } else {
            // probe was run before but is not running
            _this.probe = _this.createNewProbe(name);
            _this.probe.trigger(_this.probeEvents.STOP);
          }
        } else {
          // probe was not run before
          _this.probe = _this.createNewProbe(name);
          _this.probe.trigger(_this.probeEvents.STOP);
        }
      },
      error: function(collection, response, options) {
        // probe was not run before
        _this.probe = _this.createNewProbe(name);
        _this.probe.trigger(_this.probeEvents.STOP);
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
    logger.debug('in startProbe');
    this.probe.save(null, {
      success: function(model, response, options) {
        logger.debug('probe create success');
        logger.debug(_this.probe.get('state'));
        if (_this.probe.get('state') == _this.probeStates.CREATED) {
          _this.probe.trigger(_this.probeEvents.START);
        } else {
          _this.probe.trigger(_this.probeEvents.ERROR_START);
        }
      },
      error: function(model, response, options) {
        logger.debug('probe create error');
        logger.debug(_this.probe.get('state'));
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
            logger.debug('in waitTillRunning - probe state is ' + _this.probe.get('state'));
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
          success: function(data, textStatus, jqXHR) {
            if (data.length > 0) {
              window.clearInterval(_this.dataIntervalId);
              _this.startRender();
            }
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
    if (!_.isUndefined(this.dataIntervalId) && !_.isNull(this.dataIntervalId)) {
      window.clearInterval(this.dataIntervalId);
    }
    $.ajax({
      url: this.probe.url() + '/stop/',
      type: 'POST',
      data: {},
      dataType: "json",
      success: function(data, textStatus, jqXHR) {
        _this.probe.trigger(_this.probeEvents.STOP);
      },
      error: function(jqXHR, textStatus, error) {
        logger.debug(error);
        _this.probe.trigger(_this.probeEvents.ERROR);
      }
    });

  },

  makeSeries: function(data) {
    var series = [[]];
    for (i=0; i<10; i++) {
      series[0].push([i,data[i]]);
    }
    return series;
  },

  showNfsIO: function(probeDataUrl) {
    var _this = this;
    // set title
    this.$('#nfs-title').html(this.probe.get('name'));

    // clear rendering area
    this.$('#nfs-graph').empty();

    // create context
    this.cubism_context = cubism.context()
    .step(1e3)
    .size(600);
    
    // create horizon
    this.horizon = this.cubism_context.horizon()
    .colors(['#08519c', '#bae4b3'])
    .height(60);

    // axis
    d3.select(this.el).select("#nfs-graph").selectAll(".axis")
    .data(["top", "bottom"])
    .enter().append("div")
    .attr("class", function(d) { return d + " axis"; })
    .each(function(d) { 
      d3.select(this).call(_this.cubism_context.axis().ticks(12).orient(d)); 
    });

    d3.select(this.el).select("#nfs-graph").append("div")
    .attr("class", "rule")
    .call(_this.cubism_context.rule());
    
    var nfsContext = this.cubism_context.nfs();
    var nfsMetricRead = nfsContext.metric('Reads/sec', 'num_read', probeDataUrl);
    var nfsMetricWrites = nfsContext.metric('Writes/sec', 'num_write', probeDataUrl);
    //var nfsMetricLookups = nfsContext.metric('Lookups/sec', recipe_uri);
    //var nfsMetricReadBytes = nfsContext.metric('Bytes read/sec', recipe_uri);
    //var nfsMetricWriteBytes = nfsContext.metric('Bytes written/sec', recipe_uri);

    d3.select(this.el).select("#nfs-graph").selectAll(".horizon")
    .data([nfsMetricRead, nfsMetricWrites ])
    .enter().insert("div", ".bottom")
    .attr("class", "horizon")
    .call(_this.horizon);

    this.cubism_context.on("focus", function(i) {
      d3.selectAll(".value").style("right", i == null ? null : _this.cubism_context.size() - i + "px");
    });


  },

  start: function() {
    logger.debug('probe created');
    this.disableStartProbe();
    this.enableStopProbe();
    this.$('#probe-status').html('<h3>Probe created - getting status</h3>');
    this.waitTillRunning();
  },
  
  run: function() {
    logger.debug('probe running');
    this.disableStartProbe();
    this.enableStopProbe();
    this.$('#probe-status').html('<h3>Probe running - getting data</h3>');
    // start polling for Data
    this.pollForDataReady();

  },

  stop: function() {
    logger.debug('probe stopped');
    this.enableStartProbe();
    this.disableStopProbe();
    this.$('#probe-status').html('<h3>Probe stopped</h3>');
    if (!_.isUndefined(this.probe.id) && !_.isNull(this.probe.id)) {
      this.stopRender();
    }
  },

  error: function() {
    logger.debug('probe error');
    this.enableStartProbe();
    this.disableStopProbe();
    this.probeState = this.probeStates.ERROR;
    this.$('#probe-status').html('<h3>Error!</h3>');
  },

  startRender: function() {
    this.showNfsIO(this.probe.dataUrl());
  },

  stopRender: function() {
    var _this = this;
    if (!_.isUndefined(this.horizon) && !_.isNull(this.horizon)) {
      d3.select(this.el).select("#nfs-graph").selectAll(".horizon")
      .call(_this.horizon.remove).remove();
    }
    d3.select(this.el).select("#nfs-graph").selectAll(".axis").remove();
    this.cubism_context.stop();
    window.clearInterval(this.topSharesIntervalId);

  },

  clear: function() {

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
  name: 'nfs_distrib_probe', 
  displayName: 'NFS Usage', 
  view: 'ProbeWidget',
  description: 'NFS Usage',
  defaultWidget: false,
  rows: 2,
  cols: 3,
  category: 'Storage'
});

