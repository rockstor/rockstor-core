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
    this.maxCpus = 16;
    this.modes = ['smode', 'umode', 'umode_nice'];
    this.colors = ["#E41A1C", "#377EB8", "#4DAF4A", "#FFFFFF"];
    this.numCpus = null; 
    this.cpuData = {};
    this.avg = this.genEmptyCpuData(this.numSamples);
    this.cpuNames = [];
    this.allCpuGraphData = null;
    this.updateInterval = 2000;
    this.allCpuGraphOptions = { 
      grid : { 
        clickable: true,
        show : true,
        borderWidth: {
          top: 1,
          right: 0,
          bottom: 1,
          left: 1
        },
        aboveData: true,
        borderColor: "#ddd",
        color: "#aaa"
      },
			series: {
        stack: true,
        stackpercent : false,
        bars: { show: true, barWidth: 0.9, fillColor: {colors:[{opacity: 1},{opacity: 1}]}, align: "center" },
        lines: { show: false, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
			yaxis: { 
        min: 0, 
        max: 100,
        ticks: 4,
        tickFormatter: this.pctTickFormatter,
      },
      xaxis: { 
        tickLength: 2,
        tickFormatter: this.allCpuTickFormatter(this.cpuNames, this),
      },
      legend: { show: false },
      
    }

    this.graphOptions = { 
      grid : { 
        borderWidth: {
          top: 1,
          right: 1,
          bottom: 1,
          left: 1
        },
        aboveData: true,
        borderColor: "#ddd",
        color: "#aaa"
      },
			series: {
        stack: true,
        stackpercent : false,
        lines: { show: true, fill: 0.5, lineWidth: 1 },
        shadowSize: 0	
			},
			yaxis: { 
        min: 0, 
        max: 100,
        ticks: 4,
        tickFormatter: this.pctTickFormatter,
      },
      xaxis: {  
        tickFormatter: this.cpuTickFormatter,
        tickSize: 12,
        min: 0, 
        max: 60,
      },
      legend : { container : "#cpuusage-legend", noColumns : 4 },
      //tooltip: true,
      //tooltipOpts: { content: "<b>%s</b> (%p.2%)" }
    };
  },
 
  allCpuTickFormatter: function(cpuNames, context) {
    return function(val, axis) {
      if (!_.isUndefined(context.cpuNames[val-1])) {
        return context.cpuNames[val-1];
      } else {
        return "";
      }
    }
  },
  
  cpuTickFormatter: function(val, axis) {
    return (5 - (parseInt(val)/12)).toString() + ' m';
  },

  pctTickFormatter: function(val, axis) {
    return val + "%";
  },

  render: function() {
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
  

  getData: function(context) {
    var _this = context;
    
    $.ajax({
      url: "/api/sm/sprobes/cpumetric/?format=json&group=name&limit=1", 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        if (_.isNull(_this.numCpus)) {
          _this.numCpus = data.length;
        }
        _this.parseData(data); 
        _this.updateGraph();
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }
    });
  },

  cleanup: function() {
    if (!_.isUndefined(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  },

  parseData: function(data) {
    var _this = this;
    var tmpSum = {};
    _.each(data, function(d) {
      var cpu = _this.cpuData[d.name];
      if (_.isUndefined(cpu)) {
        cpu = _this.genEmptyCpuData(_this.numSamples );
        _this.cpuData[d.name] = cpu;
      }
      _.each(_this.modes, function(mode) {
        cpu[mode].push(d[mode]);
        cpu[mode].splice(0,1);
        if (!_.isUndefined(tmpSum[mode])) {
          tmpSum[mode] = tmpSum[mode] + d[mode];
        } else {
          tmpSum[mode] = d[mode];
        }
      });
    });
    this.cpuNames = _.keys(this.cpuData);
    _.each(_this.modes, function(mode) {
      tmpSum[mode] = tmpSum[mode]/_this.cpuNames.length;  
      _this.avg[mode].push(tmpSum[mode]);
      _this.avg[mode].splice(0,1);
    })

    _this.allCpuGraphData = [];
    _.each(_this.modes, function(mode, i) {
      var tmp = [];
      _.each(_this.cpuNames, function(name, j) {
        var dm = _this.cpuData[name][mode];
        tmp.push([j+1, dm[dm.length-1]]);
      });
      // Add empty data so that bar width is acc to maxCpus .
      for (var k=_this.numCpus; k<_this.maxCpus; k++) {
        tmp.push([k+1, null]);
      }
      _this.allCpuGraphData.push({
        "label": mode, 
        "data": tmp, 
        "color": _this.colors[i]
      });

    });
    _this.avgGraphData = [];
    _.each(_this.modes, function(mode, i) {
      var tmp = [];
      _.each(_this.avg[mode], function(d,j) {
        tmp.push([j+1, d]);
      });
      _this.avgGraphData.push({
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

    var rawData = [];
    for (i=0; i<this.numCpus; i++) {
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
    //this.allCpuGraphOptions.xaxis.ticks = this.cpuNames.length;
    this.allCpuGraphOptions.xaxis.ticks = this.maxCpus;
    $.plot($("#cpuusage-all"), this.allCpuGraphData, this.allCpuGraphOptions);
    //$("#cpuusage-all").bind("plotclick", function(event, pos, item) {
    //});
    $.plot($("#cpuusage"), this.avgGraphData, this.graphOptions);
  },

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

