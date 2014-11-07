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


MemoryUtilizationWidget = RockStorWidgetView.extend({

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_memory_utilization;
    this.updateFreq = 1000;
    this.dataBuffer = [];
    this.dataLength = 10;
    this.windowLength = 10000;
    this.currentTs = null;
    this.colors = ["#04BA44", "#C95351"];
    //this.emptyData = {"id": 0, "total": 0, "free": 0, "buffers": 0, "cached": 0, "swap_total": 0, "swap_free": 0, "active": 0, "inactive": 0, "dirty": 0, "ts": "2013-07-17T00:00:16.109Z"};
    this.t2 = RockStorGlobals.currentTimeOnServer.getTime()-30000;
    //this.t2 = new Date('2013-12-03T17:18:06.312Z').getTime();
    this.t1 = this.t2 - this.windowLength;
  },
  
  render: function() {
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName,
    }));
    this.displayMemoryUtilization('#mem-util-chart');

    /*
    var _this = this;
    var t1Str = moment(_this.t1).toISOString();
    var t2Str = moment(_this.t2).toISOString();
    var pageSizeStr = '&page_size=' + RockStorGlobals.maxPageSize;
    $.ajax({
      url: '/api/sm/sprobes/meminfo/?format=json' + pageSizeStr + '&t1=' +
        t1Str + '&t2=' + t2Str, 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        _.each(data.results, function(d) {
          _this.dataBuffer.push(d);
        });

        if (_this.dataBuffer.length > 0) { 
          while (new Date(_this.dataBuffer[0].ts).getTime() < _this.t2-(_this.windowLength )) {
            _this.dataBuffer.shift();
          }
        } 
        _this.getData(_this); 
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }

    });
    */
    return this;
  },

  displayMemoryUtilization: function(svgEl) {
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
    this.margin = {top: 20, right: 40, bottom: 20, left: 50};
    if (this.maximized) {
      this.width = 500 - this.margin.left - this.margin.right;
      this.height = 500 - this.margin.top - this.margin.bottom;
    } else {
      this.width = 250 - this.margin.left - this.margin.right;
      this.height = 190 - this.margin.top - this.margin.bottom;
    }
  },
  
  setupSvg: function(svgEl) {
    var _this = this;
    this.$(svgEl).empty();
    this.svg = d3.select(this.el).select(svgEl)
    .append('svg')
    .attr('class', 'metrics')
    .attr('width', this.width + this.margin.left + this.margin.right)
    .attr('height', this.height + this.margin.top + this.margin.bottom)
    .append("g")
    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");

    this.parseDate = d3.time.format("%y-%b-%d").parse; 
    this.formatPercent = d3.format(".0%");

    this.x = d3.time.scale().range([0, this.width]);

    this.y = d3.scale.linear().range([this.height, 0]);

    this.color = d3.scale.category20();
    this.color.domain(['used','cached','buffers','free'])

    this.xAxis = d3.svg.axis()
    .scale(this.x)
    .orient("bottom");

    this.yAxis = d3.svg.axis()
    .scale(this.y)
    .orient("left")
    .tickFormat(this.formatPercent);

    this.area = d3.svg.area()
    .x(function(d) { return _this.x(d.date); })
    .y0(function(d) { return _this.y(d.y0); })
    .y1(function(d) { return _this.y(d.y0 + d.y); });

    this.stack = d3.layout.stack()
    .values(function(d) { return d.values; });

  },

  update: function() {
    var _this = this;
    var pageSizeStr = '&page_size=1';
    if (this.initial) {
      pageSizeStr = '&page_size=' + this.dataLength;
      this.initial = false;
    }
    $.ajax({
      url: '/api/sm/sprobes/meminfo/?format=json' + pageSizeStr, 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        data.results.reverse();
        _.each(data.results, function(d) {
          d.date = new Date(d.ts);
          d.used = d.total - d.cached - d.buffers - d.free;
          _this.dataBuffer.push(d);
          _this.used.values.push({date: d.date, y: d.used/d.total});
          _this.cached.values.push({date: d.date, y: d.cached/d.total});
          _this.buffers.values.push({date: d.date, y: d.buffers/d.total});
          _this.free.values.push({date: d.date, y: d.free/d.total});
        });
        // remove data outside window
        var max_ts = new Date(_this.dataBuffer[_this.dataBuffer.length-1].ts).getTime();
        var min_ts = max_ts - this.windowLength;
        if (_this.dataBuffer.length > 0) { 
          while (new Date(_this.dataBuffer[0].ts).getTime() < min_ts) {
            _this.dataBuffer.shift();
            _this.used.values.shift();
            _this.cached.values.shift();
            _this.buffers.values.shift();
            _this.free.values.shift();
          }
        } 
        console.log(_this.dataBuffer);
        console.log(_this.used);
        console.log(_this.cached);

        _this.x.domain(d3.extent(_this.used.values, function(d) { return d.date; }));
        var utilTypes = _this.stack(_this.layers);
        var utilType = _this.svg.selectAll('.utilType')
        .data(utilTypes)
        .enter()
        .append('g')
        .attr('class', '.utilType')

        utilType.append('path')
        .attr("class", "area")
        .attr("d", function(d) { return _this.area(d.values); })
        .style("fill", function(d) { return _this.color(d.name); });
       
        _this.svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + _this.height + ")")
        .call(_this.xAxis);

        _this.svg.append("g")
        .attr("class", "y axis")
        .call(_this.yAxis); 

      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }
    });
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
    // TODO implement
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

