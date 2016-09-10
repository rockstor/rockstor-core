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
    //this.colors = ["#E41A1C", "#377EB8", "#4DAF4A", "#FFFFFF"];
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
	this.AvgCpuChartContainer = $('#cpuusage-avg');
	this.AvgCpuChartCanvas = $('#cpuusage-avg-chart');
    this.AvgCpuChartOptions = {
        showLines: true,
        animation: false,
        legend: {
            display: true,
            position: 'bottom',
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
                }
                ticks: {
                    fontSize: 10,
                    max: 100,
                    min: 0,
                    stepSize: 20,
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }],
            xAxes: [{
                gridLines: {
                    display: true,
                    drawTicks: false
                },
                ticks: {
                    fontSize: 10,
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
	        pointHoverRadius: 5,
	        pointHoverBackgroundColor: "rgba(75,192,192,1)",
	        pointHoverBorderColor: "rgba(220,220,220,1)",
	        pointHoverBorderWidth: 2,
	        pointRadius: 0,
	        pointHitRadius: 10,
	        data: [],
	    }]
	};

    // d3 graph
    this.windowLength = 60000; // window length in msec (1 min)
    this.transDuration = 1000; // transition duration
    this.updateFreq = 1000;


    // cpu data array
    this.cpuData = [];

    this.margin = {top: 20, right: 20, bottom: 20, left: 30};
	
    if (this.maximized) {
      this.width = 500 - this.margin.left - this.margin.right;
      this.height = 200 - this.margin.top - this.margin.bottom;
    } else {
      this.width = 250 - this.margin.left - this.margin.right;
      this.height = 100 - this.margin.top - this.margin.bottom;
    }
    this.padding = {top: 0, right: 0, bottom: 20, left: 0};

    this.cpuColorScale = d3.scale.linear()
    .domain([0, 100])
    .range(["#F7C8A8","#F26F18"]);
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
    var t1Str = moment(_this.t1).toISOString();
    var t2Str = moment(_this.t2).toISOString();
    data = data.results;
    if (data.length > 0) {
      _this.cpuData.push.apply(_this.cpuData, _this.getAvgCpuUsge(data));
    }

    _this.displayIndividualCpuUsage(data);
    if (!_this.graphRendered) {
      _this.renderGraph(data);
      _this.graphRendered = true;
    } else {
      _this.updateGraph(data);
    }

    if (_this.cpuData.length > 0) {
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
    }
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

  displayNoDataMsg: function() {
    this.$('#cpuusage-avg').html('<strong>No data received</strong>');
    this.$('#cpuusage-individual').empty();
  },

  renderGraph: function(data) {
    this.$('#cpuusage-avg').empty();
    var _this = this;
    // Render svg
      this.svg = d3.select(this.el).select('#cpuusage-avg')
	  .append("svg")
	  .attr("class", "cpugraph")
	  .attr("width", this.width + this.margin.left + this.margin.right)
	  .attr("height", this.height + this.margin.top + this.margin.bottom +
		this.padding.top + this.padding.bottom);

      this.svgG = this.svg.append("g")
      	  .attr("transform", "translate(" +
      		(this.margin.left + this.padding.left) + "," +
      		(this.margin.top + this.padding.top) + ")");

    // svg clip path
    this.svgG.append("defs").append("clipPath")
    .attr("id", "clip")
    .append("rect")
    .attr("width", this.width)
    .attr("height", this.height);

    // Scales
    this.x = d3.time.scale().domain([this.t2-this.windowLength, this.t2]).range([0, this.width]);
    this.y = d3.scale.linear().range([this.height, 0]);
    this.y.domain([0, 100]);

    // Line graph
    this.line = d3.svg.line()
    .interpolate('linear')
    .x(function(d) { return _this.x(new Date(d.ts)); })
    .y(function(d) { return _this.y(100 - d.idle); });

    // X Axis
    this.xAxis = this.svgG.append("g")
	  .attr("class", "cpugraph x axis")
	  .attr("transform", "translate(0, 0)")
	  .attr("transform", "translate(0," + this.height + ")")
	  .call(this.x.axis = d3.svg.axis().scale(this.x).orient("bottom").ticks(5));

    // X Grid
    this.x.grid = d3.svg.axis()
    .scale(this.x)
    .orient("bottom")
    .ticks(5)
    .tickSize(-this.height, 0, 0)
    .tickFormat('');

    this.xGrid = this.svgG.append("g")
	  .attr("class", "cpugraph grid")
	  .attr("transform", "translate(0, 0)")
	  .attr("transform", "translate(0," + this.height + ")")
	  .call(this.x.grid) ;

    this.path = this.svgG.append("g")
    .attr("clip-path", "url(#clip)")
    .append("path")
    .data([this.cpuData])
    .attr("class", "cpugraph line");

    // Grpah title
    this.svg.append("text")
    .attr("x", this.margin.left + this.padding.left + this.width/2 )
    .attr("y",  this.margin.top/2)
    .style("text-anchor", "middle")
    .text("Average CPU Usage (%)");

    // X axis label
    this.svg.append("text")
    .attr("x", this.margin.left + this.padding.left + this.width/2 )
    .attr("y",  this.height +
          this.margin.top +
          this.padding.top +
          this.margin.bottom +
          this.padding.bottom/2 )
    .style("text-anchor", "middle")
    .text("Time");

    // Y Axis
    this.yAxis = d3.svg.axis().scale(this.y)
    .orient("left").ticks(3);

    this.yGrid = d3.svg.axis()
    .scale(this.y)
    .orient('left')
    .ticks(4)
    .tickSize(-this.width, 0, 0)
    .tickFormat('');

    this.svgG.append("g")			// Add the Y Axis
    .attr("class", "cpugraph y axis")
    .call(this.yAxis);

    this.svgG.append("g")			// Add the Y Grid
    .attr("class", "cpugraph grid")
    .call(this.yGrid);

    this.svgG.select(".line")
    .attr("d", this.line);

  },

  updateGraph: function(data) {
    var _this = this;

    //var now = new Date(data[data.length-1].ts).getTime();
    //this.x.domain([now-(this.windowLength + this.updateFreq), now - this.updateFreq]);
    this.x.domain([this.t2-(this.windowLength + this.updateFreq), this.t2 - this.updateFreq]);

    //this.cpuData.push.apply(this.cpuData, data);
    this.svgG.select(".line")
    .attr("d", this.line)
    .attr("transform", "translate(0, 0)");

    this.xAxis.transition()
    .duration(this.transDuration)
    .ease("linear")
    .call(this.x.axis);

    this.xGrid.transition()
    .duration(this.transDuration)
    .ease("linear")
    .call(this.x.grid);

    // slide the line left
    this.path.transition()
    .duration(this.transDuration)
    .ease("linear")
    .attr("transform", "translate(" + this.x(this.t2 - (this.windowLength+2*this.updateFreq)) + ")");
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
    } else {
      this.width = 250 - this.margin.left - this.margin.right;
      this.height = 100 - this.margin.top - this.margin.bottom;
      this.$('#cpuusage-individual').css('width', '250');
      this.$('#cpuusage-individual-title').css('width', '250');
    }
    this.$('#cpuusage-avg').empty();
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

