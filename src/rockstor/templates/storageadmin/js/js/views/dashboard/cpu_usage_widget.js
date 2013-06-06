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


CpuUsageWidget = RockStorWidgetView.extend({
  
  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_cpuusage;
    this.numSamples = 60;
    this.cpu_data = [];
    this.modes = ['umode', 'smode', 'umode_nice', 'idle'];
    this.colors = ["#CCC1F5", "#A39BC2", "#BAB8C2", "#E1E1E3"];
    for (var i=0; i < this.numSamples; i++) {
      this.cpu_data.push({umode: 0, umode_nice: 0, smode: 0, idle: 0});
    }
    this.updateInterval = 5000;
    this.graphOptions = { 
      grid : { hoverable : true },
			series: {
        stack: true,
        stackpercent : false,
        bars: { show: true, barWidth: 0.4, fillColor: {colors:[{opacity: 1},{opacity: 1}]}, align: "center" },
        lines: { show: false, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
			yaxis: { min: 0, max: 110 },
      xaxis: {  
        tickFormatter: this.cpuTickFormatter,
        tickSize: 12,
        min: 0, 
        max: 60 
        },
      legend : { container : "#legends", noColumns : 3 },
      tooltip: true,
      tooltipOpts: { content: "<b>%s</b> (%p.2%)" }
    };
    this.prev_cpu_data = null;
  },
  
  cpuTickFormatter: function(val, axis) {
    return (5 - (parseInt(val)/12)).toString() + ' m';
  },

  render: function() {
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    var _this = this;
    $(this.el).html(this.template({
      modes: this.modes,
      colors: this.colors,
      height: this.defaultHeight,
      width: this.defaultWidth,
      displayName: this.displayName
    }));
    
    
    this.intervalId = window.setInterval(function() {
      return function() { _this.getData(_this); }
    }(), this.updateInterval)
    
    return this;
  },
  
  updateGraph: function(data) {
    var new_data = this.modifyData(data);
    $.plot("#cpuusage", new_data, this.graphOptions);
  },

  getData: function(context) {
    var _this = context;
    // showLoadingIndicator('service-loading-indicator', _this);
    $.ajax({
      url: "/api/sm/cpumetric/", 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        _this.updateGraph(data);
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }

    });
  },

  /* Calculate utilization as difference in data for two consecutive times */
  modifyData: function(data) {
    var tmp = [];
    var res = [];
    var new_data = [];
    var totals = [];
    if (data.length > this.numSamples) {
      data = data.slice(data.length - this.numSamples);
    }
    // calculate diffs from previous for each mode.
    for (var m = 0; m < this.modes.length; m++) {
      var mode = this.modes[m];
      tmp[m] = [];
      res[m] = [];
      for (var i=0; i< data.length; i++) {
        if (!_.isNull(this.prev_cpu_data) && this.prev_cpu_data.length == data.length) {
          var diff = data[i][mode] - this.prev_cpu_data[i][mode];
          tmp[m].push(diff);
        } else {
          tmp[m].push(0);
        }
      }
    }
    // calculate totals for each sample
    for (var i=0; i< data.length; i++) {
      totals[i] = 0;
      for (var m = 0; m < this.modes.length; m++) {
        totals[i] = totals[i] + tmp[m][i];
      }
      for (var m = 0; m < this.modes.length; m++) {
        if (totals[i] != 0) {
          tmp[m][i] = (tmp[m][i] / totals[i]) * 100;
        } else {
          tmp[m][i] = 0;
        }
        
      }
    }
    // create series with x as index and y as util percent
    for (var m = 0; m < this.modes.length; m++) {
      res[m] = [];
      for (var i=0; i < this.numSamples; i++) {
        res[m].push([i, tmp[m][i]]);
      }
      new_data.push({ "label": this.modes[m], "data": res[m], "color": this.colors[m] });
    }

    this.prev_cpu_data = data;
    return new_data;
  },

  cleanup: function() {
    logger.debug('clearing setInterval in cpu_usage_widget'); 
    if (!_.isUndefined(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  }

});

// Default configuration for cpu widget
RockStorWidgets.available_widgets.push({ 
  name: 'cpuusage', 
  displayName: 'CPU Utilization', 
  view: 'CpuUsageWidget',
  description: 'CPU Utilization',
  defaultWidget: true,
  rows: 1,
  cols: 1,
  category: 'Compute',
  position: 2
});

