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


MemoryUtilizationWidget = RockStorWidgetView.extend({

  initialize: function() {
    RockStorSocket.memoryWidget = io.connect('/memory-widget', {'secure': true, 'force new connection': true});
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_memory_utilization;
    this.updateFreq = 1000;
    this.dataLength = 60;
    this.windowLength = 60000;
    this.currentTs = null;
  },

  render: function() {
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    $(this.el).html(this.template({
      module_name: this.module_name,
      displayName: this.displayName
    }));
    this.displayMemoryUtilization('#mem-util-chart');

    return this;
  },

  displayMemoryUtilization: function(svgEl) {
    this.dataBuffer = [];
    this.used = { name: 'used', values: [] };
    this.cached = { name: 'cached', values: [] };
    this.buffers = { name: 'buffers', values: [] };
    this.free = { name: 'free', values: [] };
    this.layers = [this.used, this.cached, this.buffers, this.free];
    this.setDimensions();
    this.setupSvg(svgEl);
    this.initial = true;
    this.update();
  },

  setDimensions: function() {
    this.margin = {top: 5, right: 20, bottom: 20, left: 30};
    if (this.maximized) {
      this.width = 500 - this.margin.left - this.margin.right;
      this.height = 240 - this.margin.top - this.margin.bottom;
      this.swapWidth = 500 - this.margin.left - this.margin.right;
      this.swapHeight = 100 - this.margin.top - this.margin.bottom;
    } else {
      this.width = 250 - this.margin.left - this.margin.right;
      this.height = 120 - this.margin.top - this.margin.bottom;
      this.swapWidth = 250 - this.margin.left - this.margin.right;
      this.swapHeight = 50 - this.margin.top - this.margin.bottom;
    }
  },

  setupSvg: function(svgEl) {
    var _this = this;
    this.$(svgEl).empty();
    this.svg = d3.select(this.el).select(svgEl)
    .append('svg')
    .attr('width', this.width + this.margin.left + this.margin.right)
    .attr('height', this.height + this.margin.top + this.margin.bottom)
    .append("g")
    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");

    this.svg.append("defs").append("clipPath")
    .attr("id", "clip")
    .append("rect")
    .attr("width", this.width)
    .attr("height", this.height);

    this.parseDate = d3.time.format("%y-%b-%d").parse;
    //this.formatPercent = d3.format(".0%");
    this.formatPercent = function(d) { return (d*100) + ''; };
    this.x = d3.time.scale().range([0, this.width]);

    this.y = d3.scale.linear().range([this.height, 0]);
    this.y.domain = [0, 100];

    this.color = { used: '#fb6a4a', cached: '#fcbba1', buffers: '#7bccc4', free: '#ccebc5' };
    this.xAxis = d3.svg.axis()
    .scale(this.x)
    .orient("bottom")
    .ticks(5);

    this.yAxis = d3.svg.axis()
    .scale(this.y)
    .orient("left")
    .ticks(3)
    .tickFormat(this.formatPercent);

    this.area = d3.svg.area()
    .x(function(d) { return _this.x(d.date); })
    .y0(function(d) { return _this.y(d.y0); })
    .y1(function(d) { return _this.y(d.y0 + d.y); });

    this.stack = d3.layout.stack()
    .values(function(d) { return d.values; });

    this.swapSvg = d3.select(this.el).select('#swap-util-chart')
    .append('svg')
    .attr('width', this.swapWidth + this.margin.left + this.margin.right)
    .attr('height', this.swapHeight + this.margin.top + this.margin.bottom)
    .append("g")
    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
  },

  createValues: function(seed) {
    return {
      'total': 1,
      'free': 0,
      'buffers': 0,
      'cached': 0,
      'swap_total': 1,
      'swap_free': 0,
      'active': 0,
      'inactive': 0,
      'dirty': 0,
      'ts': new Date(new Date().getTime() - ((60 - seed) * 1000))
    };

  },

  update: function() {
    var _this = this;
    var data = {'results': []};
    for (var i = 0; i < 60; i++) {
      data.results.push(this.createValues(i));
    }
    // Pass in zero values for the data to kick the process off
    // However, we care about the timestamp. That needs to be current
    _this.modifyData(data);
    _this.truncateData();
    _this.x.domain(d3.extent(_this.used.values, function(d) { return new Date(d.date).getTime(); }));
    var utilTypes = _this.stack(_this.layers);
    var utilType = _this.svg.selectAll('.utilType')
          .data(utilTypes)
          .enter()
          .append('g')
          .attr("clip-path", "url(#clip)")
          .attr('class', '.utilType');

    _this.path = utilType.append('path')
      .attr("class", "area")
      .attr("d", function(d) { return _this.area(d.values); })
      .style("fill", function(d) { return _this.color[d.name]; });

    var textData = _this.layers.map(function(d) { return {name: d.name, value: d.values[d.values.length -1]}; }).reverse();

    _this.utilValues = _this.svg.selectAll(".utilValue")
      .data(textData)
      .enter()
      .append('g')
      .attr('class', 'utilValue')
      .attr("transform", function(d, i) { return "translate(" + _this.width + "," + (20*(i+1)) + ")";});

    _this.utilValues.append('rect')
      .attr('class', 'utilValueColor')
      .attr('x', -20)
      .attr('y', -10)
      .attr('width', 10)
      .attr('height', 10)
      .attr('fill', function(d) { return _this.color[d.name];})
      .attr('stroke', '#000');

    _this.utilValues.append("text")
      .attr("class", "utilValueText")
      .attr("x", -26)
      .text(function(d) { return d.name + " " + d3.format(".0%")(d.value.y); });

    _this.xAxisG = _this.svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + _this.height + ")")
      .call(_this.xAxis);

    _this.svg.append("g")
      .attr("class", "y axis")
      .call(_this.yAxis);

    // Swap Usage
    _this.swapX = d3.scale.linear().range([0,_this.swapWidth]).domain([0,_this.swapTotal]);
    _this.swapXAxis = d3.svg.axis()
      .scale(_this.swapX)
      .orient("bottom")
      .ticks(3)
      .tickFormat(function(d) { return humanize.filesize(d*1024); });

    _this.swapXAxisG = _this.swapSvg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + _this.swapHeight + ")")
      .call(_this.swapXAxis);

    _this.swapSvg.append('rect')
      .attr('class', 'swapRect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', _this.swapX(_this.swapUsage))
      .attr('height', _this.swapHeight-2)
      .attr('fill', function(d) { return '#D0D8DB';})
      .attr('stroke', '#aaa');

    _this.swapSvg.append('text')
      .attr('class', 'swapText')
      .attr('x', 2)
      .attr('y', _this.swapHeight/2 - 2)
      .text(humanize.filesize(_this.swapUsage*1024) + ' (' + d3.format(".0%")(_this.swapUsagePc/100) + ')');
    RockStorSocket.addListener(this.tick, this, 'memoryWidget:memory');
  },

  tick: function(data) {
    var _this = this;
    _this.modifyData(data);
    _this.stack(_this.layers);
    var min_ts = new Date(_this.dataBuffer[0].ts).getTime();
    var max_ts = new Date(_this.dataBuffer[_this.dataBuffer.length-1].ts).getTime()-_this.updateFreq;
    _this.x.domain([min_ts, max_ts]);

    _this.svg.selectAll('.area')
      .attr("d", function(d) { return _this.area(d.values); })
      .attr('transform', "translate(0,0)");

    _this.xAxisG.transition()
      .duration(_this.updateFreq)
      .ease('linear')
      .call(_this.xAxis);

    // slide the area left
    var new_pos = _this.x(min_ts-_this.updateFreq);

    _this.path.transition()
      .duration(_this.updateFreq)
      .ease("linear")
      .attr("transform", "translate(" + new_pos + ")");

    // remove data outside window
    _this.truncateData(data);

    //update value text label
    var textData = _this.layers.map(function(d) { return {name: d.name, value: d.values[d.values.length -1]}; }).reverse();

    _this.svg.selectAll(".utilValueText")
      .data(textData)
      .text(function(d) { return d.name + " " + d3.format(".0%")(d.value.y); });

      // Swap Usage
      _this.swapSvg.select('svg').remove();
      _this.swapSvg.select('g').remove();
      _this.swapSvg.select('rect').remove();
      _this.swapSvg.select('text').remove();
      _this.swapSvg
	  .append('svg')
	  .attr('width', this.swapWidth + this.margin.left + this.margin.right)
	  .attr('height', this.swapHeight + this.margin.top + this.margin.bottom)
	  .append("g")
	  .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
      _this.swapX = d3.scale.linear().range([0,_this.swapWidth]).domain([0,_this.swapTotal]);
      _this.swapXAxis = d3.svg.axis()
	  .scale(_this.swapX)
	  .orient("bottom")
	  .ticks(3)
	  .tickFormat(function(d) { return humanize.filesize(d*1024); });

      _this.swapXAxisG = _this.swapSvg.append("g")
	  .attr("class", "x axis")
	  .attr("transform", "translate(0," + _this.swapHeight + ")")
	  .call(_this.swapXAxis);

    _this.swapSvg.append('rect')
      .attr('class', 'swapRect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', _this.swapX(_this.swapUsage))
      .attr('height', _this.swapHeight-2)
      .attr('fill', function(d) { return '#D0D8DB';})
      .attr('stroke', '#aaa');

    _this.swapSvg.append('text')
      .attr('class', 'swapText')
      .attr('x', 2)
      .attr('y', _this.swapHeight/2 - 2)
      .text(humanize.filesize(_this.swapUsage*1024) + ' (' + d3.format(".0%")(_this.swapUsagePc/100) + ')');

    _this.swapSvg.selectAll('.swapRect')
      .attr('width', _this.swapX(_this.swapUsage));

    _this.swapSvg.selectAll('.swapText')
      .text(humanize.filesize(_this.swapUsage*1024) + ' (' + d3.format(".0%")(_this.swapUsagePc/100) + ')');

  },

  modifyData: function(data) {
    var _this = this;
    data.results.reverse();
    _.each(data.results, function(d) {
      d.date = new Date(d.ts);
      d.used = d.total - d.cached - d.buffers - d.free;
      if ( _.isUndefined(_this.dataBuffer) ) {
        _this.dataBuffer = [];
      } else if (_this.dataBuffer.length == 0 || (d.ts != _this.dataBuffer[_this.dataBuffer.length - 1].ts)) {
        _this.dataBuffer.push(d);
        _this.used.values.push({date: d.date, y: d.used/d.total});
        _this.cached.values.push({date: d.date, y: d.cached/d.total});
        _this.buffers.values.push({date: d.date, y: d.buffers/d.total});
        _this.free.values.push({date: d.date, y: d.free/d.total});
      }
    });
    _this.swapFree = data.results[data.results.length - 1].swap_free;
    _this.swapTotal = data.results[data.results.length - 1].swap_total;
    _this.swapUsagePc = ((_this.swapTotal - _this.swapFree)/_this.swapTotal) * 100;
    _this.swapUsage = _this.swapTotal - _this.swapFree;
  },

  truncateData: function() {
    // remove data outside window
    var max_ts = new Date(this.dataBuffer[this.dataBuffer.length-1].ts).getTime();
    var min_ts = max_ts - this.windowLength;
    if (this.dataBuffer.length > 0) {
      while (new Date(this.dataBuffer[0].ts).getTime() < new Date(min_ts)) {
        this.dataBuffer.shift();
        this.used.values.shift();
        this.cached.values.shift();
        this.buffers.values.shift();
        this.free.values.shift();
      }
    }
  },

  download: function(event) {
    if (!_.isUndefined(event) && !_.isNull(event)) {
      event.preventDefault();
    }
    // calculate date 24hrs ago
    var t2Date = new Date(this.currentTs);
    var t1Date =  new Date(t2Date - 1000 * 60 * 60 * 24); // one day ago
    var t2 = t2Date.toISOString();
    var t1 = t1Date.toISOString();
    document.location.href = "/api/sm/sprobes/meminfo/?t1="+t1+"&t2="+t2+"&download=true";
  },

  cleanup: function() {
    RockStorSocket.removeOneListener('memoryWidget');
  },

  resize: function() {
    this.constructor.__super__.resize.apply(this, arguments);
    if (this.maximized) {
      this.width = 500 - this.margin.left - this.margin.right;
      this.height = 240 - this.margin.top - this.margin.bottom;
      this.swapWidth = 500 - this.margin.left - this.margin.right;
      this.swapHeight = 100 - this.margin.top - this.margin.bottom;
    } else {
      this.width = 250 - this.margin.left - this.margin.right;
      this.height = 120 - this.margin.top - this.margin.bottom;
      this.swapWidth = 250 - this.margin.left - this.margin.right;
      this.swapHeight = 50 - this.margin.top - this.margin.bottom;
    }
    this.$('#mem-util-chart').empty();
    this.$('#swap-util-chart').empty();
    this.dataBuffer = [];
    this.displayMemoryUtilization('#mem-util-chart');

  }

});

RockStorWidgets.widgetDefs.push({
    name: 'memory_utilization',
    displayName: 'Memory',
    view: 'MemoryUtilizationWidget',
    description: 'Display memory utilization',
    defaultWidget: true,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Compute',
    position: 4
});
