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
    this.svgLegendEl = '#ph-metrics-legend';
    // Metrics 
    this.raw = 0; // raw storage capacity in GB
    this.allocated = 0; 
    this.free = 0; 
    this.poolCapacity = 0; 
    this.usage = 0; 
    this.margin = {top: 0, right: 40, bottom: 20, left: 30};
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
    }, 0);
    this.provisioned = this.disks.reduce(function(sum, disk) {
      sum = disk.get('pool') != null ? sum + disk.get('size') : sum;
      return sum;
    }, 0);
    this.free = this.raw - this.provisioned

    this.pool = this.pools.reduce(function(sum, pool) {
      sum += pool.get('size');
      return sum;
    }, 0);
    this.raidOverhead = this.provisioned - this.pool; 
    this.share = this.shares.reduce(function(sum, share) {
      sum += share.get('size');
      return sum;
    }, 0);
    this.usage = this.shares.reduce(function(sum, share) {
      sum += share.get('r_usage');
      return sum;
    }, 0);
    this.pctUsed = parseFloat(((this.usage/this.raw).toFixed(0)) * 100);
    
    this.data = [
      {name: 'used', label: 'Usage', value: this.usage},
      {name: 'pool', label: 'Pool Capacity', value: this.poolCapacity}, 
      {name: 'raw', label: 'Raw Capacity', value: this.raw}
    ];

    this.data1 = [
      { name: 'share', label: 'Share Capacity', value: this.share},
      { name: 'pool-provisioned', label: 'Provisioned', value: this.provisioned },
      { name: 'raw', label: 'Raw Capacity', value: this.raw },
    ]
    this.data2 = [
      { name: 'usage', label: 'Usage', value: this.usage},
      { name: 'pool', label: 'Pool Capacity', value: this.pool },
      { name: 'provisioned', label: 'Provisioned', value: this.provisioned },
    ]

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
      this.height = 160 - this.margin.top - this.margin.bottom;
    }
    this.x = d3.scale.linear().domain([0,this.raw]).range([0, this.width]);
    this.y = d3.scale.linear().domain([0, this.data.length]).range([0, this.height]);
    this.barHeight = (this.height / this.data.length );
  },
  
  setupSvg: function() {
    // svg for viz
    this.$(this.svgEl).empty();
    this.svg = d3.select(this.el).select(this.svgEl)
    .append('svg')
    .attr('class', 'metrics')
    .attr('width', this.width + this.margin.left + this.margin.right)
    .attr('height', this.height + this.margin.top + this.margin.bottom);
    this.svgG = this.svg.append("g")
    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
    
    // svg for legend
    this.$(this.svgLegendEl).empty();
    this.svgLegend = d3.select(this.el).select(this.svgLegendEl)
    .append('svg')
    .attr('class', 'metrics-legend')
    .attr('width', this.width + this.margin.left + this.margin.right)
    .attr('height', 80);
  },

  renderMetrics: function() {
    var _this = this;
    
    // tickValues(this.x.domain()) sets tick values at beginning and end of the scale
    this.xAxis = d3.svg.axis().scale(this.x).orient('bottom').tickValues(_this.x.domain()).tickFormat(function(d) {
      return humanize.filesize(d*1024);
    });
    this.yAxis = d3.svg.axis().scale(this.y).orient('left').tickValues([0,1,2]).tickFormat(function(d) {
      if (d==0) {
        return 'Shares';
      } else if (d==1) {
        return 'Pools';
      } else if (d==2) {
        return 'Disks'
      }
    });

    this.svgG.append("g")	
    .attr("class", "metrics-axis")
    .attr("transform", "translate(0," + _this.height + ")")
    .call(this.xAxis)
    
    // render data1
    this.svgG.selectAll('metrics-rect1')
    .data(this.data1)
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
    .attr('height', function() { return _this.barHeight-4; });

    // render data2
    this.svgG.selectAll('metrics-rect2')
    .data(this.data2)
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
    .attr('height', function() { return _this.barHeight-4; });
    
    // allocated 
    //this.svgG
    //.append('rect')
    //.attr('class', function(d) {
      //return 'allocated';
    //})
    //.attr('x',0)
    //.attr('y', _this.y(2))
    //.attr('width', function(d) { return _this.x(_this.allocated); })
    //.attr('height', function() { return _this.barHeight-4; });
   
    // text labels 
    this.svgG.selectAll('metrics-text-data1')
    .data(this.data1)
    .enter()
    .append('text')
    .attr("class", "metrics-text-data1")
    .attr('x', function(d){ 
      var xOff = _this.x(d.value) - 4;
      return (xOff > 0 ? xOff : 0);
    })
    .attr('y', function(d,i) {
      return _this.y(i) + 12;
    })
    .style('text-anchor', function(d) {
      var xOff = _this.x(d.value) - 4;
      return (xOff > 30 ?  'end' : 'start');
    })
    .text(function(d,i) {
      return humanize.filesize(d.value*1024);
    });

    // text labels 
    this.svgG.selectAll('metrics-text-data2')
    .data(this.data2)
    .enter()
    .append('text')
    .attr("class", "metrics-text-data1")
    .attr('x', function(d){ 
      var xOff = _this.x(d.value) - 4;
      return (xOff > 0 ? xOff : 0);
    })
    .attr('y', function(d,i) {
      return _this.y(i) + _this.barHeight - 12;
    })
    .style('text-anchor', function(d) {
      var xOff = _this.x(d.value) - 4;
      return (xOff > 30 ?  'end' : 'start');
    })
    .text(function(d,i) {
      return humanize.filesize(d.value*1024);
    });
    
    // legend 
    //this.svgGLegend
    //.append('text')
    //.attr("class", "metrics-small-text")
    //.attr('x', 5)
    //.attr('y', this.y(2) + _this.barHeight/4 + 16) // y of raw + 16px for large label above it
    //.style("text-anchor", "left")
    //.text(function(d,i) {
      //return _this.disks.length + ' x ' + humanize.filesize(_this.disks.at(0).get('size')*1024) + ' disks';
    //});

    this.gDisk = this.svgLegend.append('g')
    .attr('class', 'metrics-disk-legend')
    .attr("transform", function(d,i) {
      return "translate(" + _this.margin.left + ",0)"
    });

    var diskLabelData = [
      {label: 'Disks - provisioned (' + humanize.filesize(this.provisioned*1024) + ')', fill: '#91BFF2'},
      {label: 'Disks - free (' + humanize.filesize(this.free*1024) + ')', fill: '#E4EDF7'},
      {label: 'Pool Capacity (' + humanize.filesize(this.pool*1024) + ')', fill: '#0BD6E3'},
      {label: 'Pool Raid overhead  (' + humanize.filesize(this.raidOverhead*1024) + ')', fill: '#B0F1F5'},
      {label: 'Share Capacity (' + humanize.filesize(this.shares*1024) + ')', fill: '#FAE8CA'},
      {label: 'Usage (' + humanize.filesize(this.raidOverhead*1024) + ')', fill: '#FAC670'},
    ]
   
    var diskLabels = this.gDisk.selectAll('legend-disk')
    .data(diskLabelData)
    .enter();

    var diskLabelG = diskLabels.append('g')
    .attr("transform", function(d,i) {
      return "translate(0, " + (i*12) + ")"
    });

    diskLabelG.append("rect")
    .attr("width", 13)
    .attr("height", 13)
    .attr("fill", function(d) { return d.fill;})

    diskLabelG.append("text")
    .attr("text-anchor", "left")
    .attr("class", "metrics-legend-text")
    .attr("transform", function(d,i) {
      return "translate(16,13)"
    })
    .text(function(d) { return d.label;}); 
   
    /* 
    labels.append("rect")
    .attr("width", 13)
    .attr("height", 13)
    .attr("transform", "translate(80,0)")
    .attr("fill", colors[1].fill)
    .attr("stroke", colors[1].stroke);

    labels.append("text")
    .attr("text-anchor", "left")
    .attr("class", "metrics-small-text")
    .attr("transform", "translate(96,13)")
    .text(labelText[1]); 
    */

    // draw y axis last so that it is above all rects
    this.svgG.append("g")	
    .attr("class", "metrics-axis")
    .call(this.yAxis)
    .selectAll("text")	
    .style("text-anchor", "end")
    .attr("transform", function(d) {
      return "rotate(-90)";
    })
    .attr("dx", "-.4em")
    .attr("dy", "-.30em");

  },

  resize: function(event) {
    this.constructor.__super__.resize.apply(this, arguments);
    this.setGraphDimensions();
  }

});

RockStorWidgets.widgetDefs.push({ 
    name: 'storage_metrics', 
    displayName: 'Total Capacity, Allocation and Usage', 
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




