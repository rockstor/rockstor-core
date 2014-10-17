/*
 *
 * @licstart  The following is the entire license notice for the 
 * JavaScript code in this page.
 * 
 * Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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


StorageMetricsWidget = RockStorWidgetView.extend({

  initialize: function() {
    var _this = this;
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_storage_metrics;
    // Dependencies 
    this.disks = new DiskCollection();
    this.pools = new PoolCollection();
    this.shares = new ShareCollection();
    this.disks.pageSize = RockStorGlobals.maxPageSize;
    this.shares.pageSize = RockStorGlobals.maxPageSize;
    this.pools.pageSize = RockStorGlobals.maxPageSize;
    this.dependencies.push(this.disks);
    this.dependencies.push(this.pools);
    this.dependencies.push(this.shares);
    // svg 
    this.svgEl = '#ph-metrics-viz';
    // Metrics 
    this.raw = 0; // raw storage capacity in GB
    this.allocated = 0; 
    this.free = 0; 
    this.poolCapacity = 0; 
    this.usage = 0; 
    this.margin = {top: 20, right: 20, bottom: 40, left: 30};
  },

  render: function() {
    var _this = this;
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName,
      maximized: this.maximized
    }));
    this.fetch(function() {
      console.log(_this.disks);
      console.log(_this.pools);
      console.log(_this.shares);
      _this.setData();
      _this.setDimensions();
      _this.setupSvg();
      _this.renderMetrics();
    }, this);
    return this;
  },

  setData: function() {
    var gb = 1024*1024;
    this.raw = this.disks.reduce(function(sum, disk) {
      sum += disk.get('size');
      return sum;
    }, 0)/gb;
    this.allocated = this.disks.reduce(function(sum, disk) {
      sum = disk.get('pool') != null ? sum + disk.get('size') : sum;
      return sum;
    }, 0)/gb;
    this.free = this.raw - this.allocated
    this.poolCapacity = this.pools.reduce(function(sum, pool) {
      sum += pool.get('size');
      return sum;
    }, 0)/gb;
    this.used = this.shares.reduce(function(sum, share) {
      sum += share.get('r_usage');
      return sum;
    }, 0)/gb;
    this.data = [
      {name: 'used', label: 'Usage', value: this.used},
      {name: 'pool', label: 'Pool Capacity', value: this.poolCapacity}, 
      {name: 'raw', label: 'Raw Storage Capacity', value: this.raw}
    ];

  },
  
  setDimensions: function() {
    //this.graphWidth = this.maximized ? 500 : 250;
    //this.graphHeight = this.maximized ? 300 : 150;
    this.barPadding = this.maximized ? 40 : 20;
    this.barWidth = this.maximized ? 400 : 200
    if (this.maximized) {
      this.width = 500 - this.margin.left - this.margin.right;
      this.height = 500 - this.margin.top - this.margin.bottom;
    } else {
      this.width = 250 - this.margin.left - this.margin.right;
      this.height = 250 - this.margin.top - this.margin.bottom;
    }
    this.x = d3.scale.linear().domain([0,this.raw]).range([0, this.width]);
    this.y = d3.scale.linear().domain([0, this.data.length]).range([0, this.height]);
    this.barHeight = (this.height / this.data.length ) - 4;
  },
  
  setupSvg: function() {
    this.$(this.svgEl).empty();
    this.svg = d3.select(this.el).select(this.svgEl)
    .append('svg')
    .attr('class', 'metrics')
    .attr('width', this.width + this.margin.left + this.margin.right)
    .attr('height', this.height + this.margin.top + this.margin.bottom);
    this.svgG = this.svg.append("g")
    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
  },

  renderMetrics: function() {
    var _this = this;
   
    this.xAxis = d3.svg.axis().scale(this.x).orient('bottom').ticks(5);

    this.svgG.append("g")	
    .attr("class", "metrics-axis")
    .attr("transform", "translate(0," + _this.height + ")")
    .call(this.xAxis)

    this.svgG.selectAll('metrics-rect')
    .data(this.data)
    .enter()
    .append('rect')
    .attr('class', function(d) {
      return d.name;
    })
    .attr('x',0)
    .attr('y', function(d,i) {
      //return _this.y(i) + _this.barHeight/2 + _this.barPadding;
      return _this.y(i);
    })
    .attr('width', function(d) { return _this.x(d.value); })
    .attr('height', function() { return _this.barHeight; });
    //.attr('height', this.barHeight)

    //this.svgG.selectAll('g.metrics-raw')
    //.data([this.raw])
    //.enter()
    //.append('g')
    //.attr('transform', function(d,i) {
      //return "translate(0," + 2*_this.barHeight + ")"; 
    //})
    //.append('rect')
    //.attr('class', 'metrics-raw')
    //.attr('x', 0)
    //.attr('y', 0)
    //.attr('width', this.x(this.raw))
    //.attr('height', this.barHeight)

  },

  resize: function(event) {
    this.constructor.__super__.resize.apply(this, arguments);
    this.setGraphDimensions();
  }

});

RockStorWidgets.widgetDefs.push({ 
    name: 'storage_metrics', 
    displayName: 'Storage Metrics', 
    view: 'StorageMetricsWidget',
    description: 'Display capacity and usage',
    defaultWidget: true,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage', 
    position: 6,
});




