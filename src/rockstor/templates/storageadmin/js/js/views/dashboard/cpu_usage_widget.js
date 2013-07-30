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
    this.numSamples = 5;
    this.cpu_data = [];
    this.modes = ['smode', 'umode', 'umode_nice', 'idle'];
    this.colors = ["#CCC1F5", "#A39BC2", "#BAB8C2", "#FFFFFF"];
    this.cpuData = {};
    this.cpuNames = [];
    this.allCpuGraphData = null;
    for (var i=0; i < this.numSamples; i++) {
      this.cpu_data.push({umode: 0, umode_nice: 0, smode: 0, idle: 0});
    }
    this.updateInterval = 2000;
    this.allCpuGraphOptions = { 
      grid : { 
        show : true,
        borderWidth: {
          top: 0,
          right: 1,
          bottom: 0,
          left: 0
        },
        borderColor: "#aaa"
      },
			series: {
        stack: true,
        stackpercent : false,
        bars: { show: true, barWidth: 10*this.numSamples/300, fillColor: {colors:[{opacity: 1},{opacity: 1}]}, align: "center" },
        lines: { show: false, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
			yaxis: { min: 0, max: 100 },
      xaxis: { 
        tickFormatter: this.allCpuTickFormatter(this.cpuNames, this)
      },
      legend: { show: false },
      
    }


    this.graphOptions = { 
      //grid : { hoverable : true },
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
 
  allCpuTickFormatter: function(cpuNames, context) {
    return function(val, axis) {
      return context.cpuNames[val-1];
    }
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
    
    
    this.intervalId = window.setTimeout(function() {
      return function() { _this.getData(_this); }
    }(), this.updateInterval)
    
    return this;
  },
  

  getData: function(context) {
    var _this = context;
    // showLoadingIndicator('service-loading-indicator', _this);
    /*
    $.ajax({
      url: "/api/sm/sprobes/cpumetric/", 
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
    */
    var rawData = _this.genRawData(); 
    _this.parseData(rawData); 
    console.log(_this.allCpuGraphData);
    _this.updateGraph();
    
    
  },


  cleanup: function() {
    logger.debug('clearing setInterval in cpu_usage_widget'); 
    if (!_.isUndefined(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  },

  parseData: function(data) {
    var _this = this;
    _.each(data, function(d) {
      var cpu = _this.cpuData[d.name];
      if (_.isUndefined(cpu)) {
        cpu = _this.genEmptyCpuData(_this.numSamples );
        _this.cpuData[d.name] = cpu;
      }
      _.each(_this.modes, function(mode) {
        cpu[mode].push(d[mode]);
        cpu[mode].splice(0,1);
      });
    });
    this.cpuNames = _.keys(this.cpuData);
    console.log(this.cpuNames);
    _this.allCpuGraphData = [];
    _.each(_this.modes, function(mode, i) {
      var tmp = [];
      _.each(_this.cpuNames, function(name, j) {
        var dm = _this.cpuData[name][mode];
        tmp.push([j+1, dm[dm.length-1]]);
      });
      _this.allCpuGraphData.push({
        "label": mode, 
        "data": tmp, 
        "color": _this.colors[i]
      });

    });
    
  },

  genEmptyCpuData: function(numSamples) {
    var cpu = {};
    _.each(this.modes, function(mode) {
      cpu[mode] = [];
      for (var i=0; i<numSamples; i++) {
        cpu[mode].push(0); 
      }
    });
    return cpu;
  },

  genRawData: function(n) {
    //{"id": 96262, "name": "cpu1", "umode": 188641, "umode_nice": 0, "smode": 269451, "idle": 17115082, "ts": "2013-07-29T00:44:09.250Z"}, 

    var n = 4; // no of cpus
    var rawData = [];
    for (i=0; i<n; i++) {
      var cpu = {name: "cpu" + i};
      cpu.smode = 10 + parseInt(Math.random()*10);
      cpu.umode = 40 + parseInt(Math.random()*10);
      cpu.umode_nice = parseInt(Math.random()*5);
      cpu.idle = 100 - (cpu.smode + cpu.umode + cpu.umode_nice);
      rawData.push(cpu);
    }
    return rawData;
  },


  updateGraph: function(data) {
    this.allCpuGraphOptions.xaxis.ticks = this.cpuNames.length;
    $.plot("#cpuusage_all", this.allCpuGraphData, this.allCpuGraphOptions);
  },

  /* Calculate utilization as difference in data for two consecutive times */
  /*
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
  */

});

// Default configuration for cpu widget
RockStorWidgets.available_widgets.push({ 
  name: 'cpuusage', 
  displayName: 'CPU Utilization', 
  view: 'CpuUsageWidget',
  description: 'CPU Utilization',
  defaultWidget: true,
  rows: 1,
  cols: 2,
  category: 'Compute',
  position: 1
});

