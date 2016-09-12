/*
 *
 * @licstart  The following is the entire license notice for the 
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
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
    RockStorSocket.cpuWidget = io.connect('/cpu-widget', {'secure': true, 'force new connection': true});
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_cpuusage;
    // maximized size for shapeshift
    this.maxCols = 10;
    this.maxRows = 2;
    this.numSamples = 60;
    this.maxCpus = 8;
    this.modes = ['smode', 'umode', 'umode_nice', 'idle'];
    this.colors = ['#FF8C00', '#98abc5', '#8a89a6', '#ffffff'];
    this.numCpus = null;
    this.avg = this.genEmptyCpuData(this.numSamples);
    this.cpuNames = [];
    this.allCpuGraphData = null;
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
        borderColor: "#ddd",
        color: "#aaa"
      },
			series: {
        stack: true,
        stackpercent : false,
        bars: { show: true, barWidth: 0.8, fillColor: {colors:[{opacity: 1},{opacity: 1}]}, align: "center" },
        lines: { show: false, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
			yaxis: {
        min: 0,
        max: 100,
        ticks: 2,
        tickFormatter: this.pctTickFormatter,
        font: { color: "#333" }
      },
      xaxis: {
        ticks: this.maxCpus,
        tickLength: 1,
        tickFormatter: this.allCpuTickFormatter(this),
        font: { color: "#333" }
      },
      legend : {
        container : "#cpuusage-legend",
        noColumns : 4,
        labelBoxBorderColor: '#ffffff'

      }

    };
	
	this.AvgCpuChart = null;
	this.AvgCpuChartCanvas = this.$('#cpuusage-avg-chart');
    this.AvgCpuChartOptions = {
        showLines: true,
        animation: false,
		responsive: true,
        legend: {
            display: false,
            position: 'top',
            labels: {
                boxWidth: 10,
                padding: 2
            }
        },
        tooltips: {
            enabled: false
        },
        scales: {
            yAxes: [{
                gridLines: {
                    drawTicks: false
                },
                ticks: {
                    fontSize: 9,
                    max: 100,
                    min: 0,
                    stepSize: 20,
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }],
            xAxes: [{
				scaleLabel: {
					display: true,
					fontSize: 10,
					labelString: 'Time'
				},
                gridLines: {
                    display: true,
                    drawTicks: false
                },
                ticks: {
                    fontSize: 9,
                    maxRotation: 0,
                    autoSkip: false,
                    callback: function(value) {
                        return (value.toString().length > 0 ? value : null);
                    }
                }
            }]
        }
    };
	this.AvgCpuChartData = {
	    labels: [],
	    datasets: [{
	        label: "Cpu Average Usage",
	        fill: false,
	        lineTension: 0.2,
	        backgroundColor: "rgba(75,192,192,0.4)",
	        borderColor: "rgba(75,192,192,1)",
	        borderCapStyle: 'butt',
	        borderDash: [],
	        borderDashOffset: 0.0,
	        borderWidth: 1,
	        borderJoinStyle: 'miter',
	        pointBorderColor: "rgba(75,192,192,1)",
	        pointBackgroundColor: "#fff",
	        pointBorderWidth: 1,
	        pointHoverRadius: 0,
	        pointHoverBackgroundColor: "rgba(75,192,192,1)",
	        pointHoverBorderColor: "rgba(220,220,220,1)",
	        pointHoverBorderWidth: 0,
	        pointRadius: 0,
	        pointHitRadius: 10,
	        data: [],
	    }]
	};

    // cpu data array
    this.cpuData = [];

    this.margin = {top: 20, right: 20, bottom: 20, left: 30};
	this.padding = {top: 0, right: 0, bottom: 20, left: 0};
	
    if (this.maximized) {
      this.width = 500 - this.margin.left - this.margin.right;
      this.height = 200 - this.margin.top - this.margin.bottom;
    } else {
      this.width = 250 - this.margin.left - this.margin.right;
      this.height = 100 - this.margin.top - this.margin.bottom;
    }
    

    this.cpuColorScale = d3.scale.linear()
    .domain([0, 100])
    .range(["#F7C8A8","#F26F18"]);

	//Generate empty data and labels on avg cpu chart
	this.genAvgCputInitData(this.numSamples);
	
  },
  
  genAvgCputInitData: function(numSamples){
	var _this = this;
	for (var i=0; i<numSamples; i++) {
    _this.AvgCpuChartData.labels.push('');
    _this.AvgCpuChartData.datasets[0].data.push(null);
    }
  },

  allCpuTickFormatter: function(context) {
    return function(val, axis) {
      if (!_.isUndefined(context.cpuNames[val-1])) {
        return context.cpuNames[val-1];
      } else {
        return "";
      }
    };
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
      displayName: this.displayName,
      maximized: this.maximized
    }));

    RockStorSocket.addListener(this.getData, this, 'cpuWidget:cpudata');
    return this;
  },

  getData: function(data) {
    this.t2 = new Date(data.results[0].ts);
    var _this = this;
    _this.startTime = new Date().getTime();
    data = data.results;
    if (data.length > 0) {
      _this.cpuData.push.apply(_this.cpuData, _this.getAvgCpuUsge(data));
    }

    //_this.displayIndividualCpuUsage(data);
    if (!_this.graphRendered) {
		_this.AvgCpuChart = Chart.Line(this.$('#cpuusage-avg-chart'), {
		data: _this.AvgCpuChartData, 
		options: _this.AvgCpuChartOptions
		});
      _this.graphRendered = true;
    } else {
      _this.updateGraph(data);
    }

    /*if (_this.cpuData.length > 0) {
      while (new Date(_this.cpuData[0].ts).getTime() < _this.t2-(_this.windowLength + _this.updateFreq)) {
        _this.cpuData.shift();
      }
    }

    var currentTime = new Date().getTime();
    var diff = currentTime - _this.startTime;
    if (diff > _this.updateFreq) {
      if (_this.cpuData.length > 0) {
        _this.t1 = new Date(_this.cpuData[_this.cpuData.length-1].ts).getTime();
      } else {
        _this.t1 = _this.t1 + diff;
      }
      _this.t2 = _this.t2 + diff;
    } else {
      if (_this.cpuData.length > 0) {
        _this.t1 = new Date(_this.cpuData[_this.cpuData.length-1].ts).getTime();
      } else {
        _this.t1 = _this.t1 + _this.updateFreq;
      }
      _this.t2 = _this.t2 + _this.updateFreq;
    }*/
  },

  cleanup: function() {
    if (!_.isUndefined(this.timeoutId)) {
      window.clearTimeout(this.timeoutId);
    }
    RockStorSocket.removeOneListener('cpuWidget');
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

  renderGraph: function(data) {
    //this.$('#cpuusage-avg').empty();
    var _this = this;
  },

  updateGraph: function(data) {
    var _this = this;
	var avgcpu = _this.getAvgCpuUsge(data);
	  _this.AvgCpuChart.data.datasets[0].data.shift();
  _this.AvgCpuChart.data.labels.shift();
  _this.AvgCpuChart.data.datasets[0].data.push(100-avgcpu[0].idle);
  var csecs = moment(avgcpu[0].ts).format("s");
  if (csecs % 15 === 0) {
    var label = csecs == '0' ? moment(avgcpu[0].ts).format("HH:mm") : moment(avgcpu[0].ts).format(":ss");
    _this.AvgCpuChart.data.labels.push(label);
  } else {
    _this.AvgCpuChart.data.labels.push('');
  }

  _this.AvgCpuChart.update();
  },

  displayIndividualCpuUsage: function(data) {
    var _this = this;
    // get latest value for each cpu
    var tmp = _.groupBy(data, function(d) { return d.name; });
    this.cpuNames = _.keys(tmp);
    this.numCpus = this.cpuNames.length;
    data = _.map(_.keys(tmp), function(d) {
      var a = tmp[d];
      return a[a.length-1];
    });
    _this.allCpuGraphData = [];
    _.each(_this.modes, function(mode, i) {
      var tmp2 = [];
      _.each(_this.cpuNames, function(name, j) {
        var dm = data[j][mode];
        tmp2.push([j+1, dm]);
      });
      // Add empty data so that bar width is acc to maxCpus .
      for (var k=_this.numCpus; k<_this.maxCpus; k++) {
        tmp2.push([k+1, null]);
      }
      if (mode != 'idle') {
        _this.allCpuGraphData.push({
          "label": mode,
          "data": tmp2,
          "color": _this.colors[i]
        });
      }

    });
    $.plot($("#cpuusage-individual"), this.allCpuGraphData, this.allCpuGraphOptions);

  },

  getAvgCpuUsge: function(data) {
    var _this = this;
    var tmp = _.groupBy(data, function(d) {
      return d.ts;
    });
    return _.map(_.keys(tmp), function(key) {
      var ds = tmp[key];
      if (ds.length > 0) {
        var s = _.reduce(ds, function(sum, d) {
          return d.idle + sum;
        }, 0);
        var avg = s / ds.length;
        return {idle: avg, ts: key};
      } else {
        return {idle: 0, ts: key};
      }
    });
  },

  resize: function(event) {
    this.constructor.__super__.resize.apply(this, arguments);
    if (this.maximized) {
      this.width = 500 - this.margin.left - this.margin.right;
      this.height = 200 - this.margin.top - this.margin.bottom;
      this.$('#cpuusage-individual').css('width', '500px');
      this.$('#cpuusage-individual-title').css('width', '500px');
	  //this.$('#cpuusage-avg').css('width', '500px');
    } else {
      this.width = 250 - this.margin.left - this.margin.right;
      this.height = 100 - this.margin.top - this.margin.bottom;
      this.$('#cpuusage-individual').css('width', '250px');
      this.$('#cpuusage-individual-title').css('width', '250px');
	  //this.$('#cpuusage-avg').css('width', '250px');
    }
    //this.$('#cpuusage-avg').empty();
	this.AvgCpuChart.resize();
    this.renderGraph(this.cpuData);
  }

});

// Default configuration for cpu widget
RockStorWidgets.widgetDefs.push({
  name: 'cpuusage',
  displayName: 'CPU',
  view: 'CpuUsageWidget',
  description: 'CPU Utilization',
  defaultWidget: true,
  rows: 1,
  cols: 5,
  maxRows: 2,
  maxCols: 10,
  category: 'Compute',
  position: 3
});

