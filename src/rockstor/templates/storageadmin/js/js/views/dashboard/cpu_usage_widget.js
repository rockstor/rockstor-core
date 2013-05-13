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
    this.numSamples = 120;
    this.cpu_data = [];
    this.modes = ['umode', 'umode_nice', 'smode', 'idle'];
    for (var i=0; i < this.numSamples; i++) {
      this.cpu_data.push({umode: 0, umode_nice: 0, smode: 0, idle: 0});
    }
    this.cleanupArray = this.options.cleanupArray;
  },

  render: function() {
    var _this = this;
    $(this.el).html(this.template());
   
    // display cpu graph 
    var w = 200; // width
    var h = 100; // height
    var padding = 30;
    var id = "#cpuusage";
    /*
    var graph = d3.select(this.el).select(id).append("svg:svg")
    .attr("width", w)
    .attr("height", h);
    */
    var elem = this.$(id)[0];
    var max_y = 100;
    var padding = 30;
    var xscale = d3.scale.linear().domain([0, 120]).range([padding, w]); 
    var yscale = d3.scale.linear().domain([0, 100]).range([0, h-padding]);
    var xdiff = xscale(1) - xscale(0);

    var initial = true; 
    var cpu_data = null; 
    this.displayGraph(elem, w, h, padding, cpu_data, xscale, yscale, 1000, 1000);

    return this;
  },

  displayGraph: function(elem, width, height, padding, data, x, y) {
    var tv = 5000;
    this.graph = new Rickshaw.Graph( {
      element: elem,
      width: width,
      height: height,
      renderer: 'bar',
      series: new Rickshaw.Series.FixedDuration([{ color: 'steelblue', name: 'one' }], undefined, {
        timeInterval: tv,
        maxDataPoints: this.numSamples,
        timeBase: new Date().getTime() / 1000
      }) 
    } );
    this.graph.render();
    var _this = this;
    this.intervalId = window.setInterval(function() {
      return function() { _this.getData(_this); }
    }(), 5000)
  },
  
  updateGraph: function(data) {
    var new_data = this.modifyData(data);
    this.graph.series.addData(new_data[new_data.length-1]);
    this.graph.render();
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

  modifyData: function(data) {
    this.prev_cpu_data = this.cpu_data;
    var tmp = [];
    if (data.length < this.numSamples) {
      for (var i=0; i < this.numSamples-data.length; i++) {
        tmp.push({umode: 0, umode_nice: 0, smode: 0, idle: 0});
      }
      data = tmp.concat(data);
    }
    this.cpu_data = data;
    var cpu_util = [];
    for (var i=0; i < this.numSamples; i++) {
      cpu_util.push({
        umode: this.cpu_data[i].umode - this.prev_cpu_data[i].umode,
        umode_nice: this.cpu_data[i].umode_nice - this.prev_cpu_data[i].umode_nice,
        smode: this.cpu_data[i].smode - this.prev_cpu_data[i].smode,
        idle: this.cpu_data[i].idle - this.prev_cpu_data[i].idle,
      })
    }
    var data_umode = null; 
    data_umode = _.map(cpu_util, function(d,i) {
      var sum = _.reduce(this.modes, function(memo, mode) { return memo + d[mode];}, 0, this);
      if (sum == 0) {
        return {one: 0}; 
      } else {
        return {one: Math.round((d['umode']/sum) * 100)};
      }

    }, this);
    return data_umode;
  },
  
  cleanup: function() {
    logger.debug('clearing setInterval in cpu_usage_widget'); 
    if (!_.isUndefined(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  }

});

