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
    // Metrics 
    this.raw = 0; // raw storage capacity in GB
    this.usable = 0; // usable storage capacity in GB
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
    this.fetch(this.renderViz, this);
    return this;
  },

  renderTitle: function() {
    this.svgTitle = d3.select(this.el).select('#ph-metrics-title')
    .append('svg')
    .attr('width', this.graphWidth)
    .attr('height', 20);
    
    this.svgTitle.append('text')
    .attr('x', this.diskColOffset)
    .attr('y', 10)
    .style("text-anchor", "start")
    .text('Disks')
    
    this.svgTitle.append('text')
    .attr('x', this.diskColOffset + this.diskWidth + this.poolColOffset + this.poolRectOffset - 1)
    .attr('y', 10)
    .style("text-anchor", "start")
    .text('Pools')

  },

   
  renderViz: function() {
    // sort disks and shares by pool
    this.disks = this.disks.sortBy(function(disk) { return -disk.get('pool'); }, this);
    this.pools = this.pools.sortBy(function(pool) { return -pool.id }, this);
    this.shares = this.shares.sortBy(function(share) { return -share.get('pool').id }, this);
    var sum = this.disks.reduce(function(sum, disk) {
      sum += disk.get('size');
      return sum;
    }, 0);
    this.raw = Math.round(sum / (1024*1024));
    sum = this.pools.reduce(function(sum, pool) {
      sum += pool.get('size');
      return sum;
    }, 0);
    this.usable = Math.round(sum/(1024*1024));
    
    var diskProvisioned = this.disks.reduce(function(sum, disk) {
      sum = disk.get('pool') != null ? sum + disk.get('size') : sum;
      return sum;
    }, 0);
    this.diskProvisioned = diskProvisioned/(1024*1024);
    var diskFree = this.disks.reduce(function(sum, disk) {
      sum = disk.get('pool') == null ? sum + disk.get('size') : sum;
      return sum;
    }, 0);
    this.diskFree = diskFree/(1024*1024);
    this.setGraphDimensions();
    console.log(this.graphHeight);
    this.y = d3.scale.linear().domain([0,this.raw]).range([0, this.graphHeight]);
    console.log(this.disks);
    console.log(this.pools);
    console.log(this.shares);
    this.poolsColYOffset = this.y((this.raw - this.usable)/2);

    //this.setData();
    this.$('#ph-metrics-viz').empty();
    this.svg = d3.select(this.el).select('#ph-metrics-viz')
    .append('svg')
    .attr('class', 'metrics')
    .attr('width', this.graphWidth)
    .attr('height', this.graphHeight);
    
    this.renderTitle(); 
    this.renderMetrics();
    this.renderLegend();
  },


  setGraphDimensions: function() {
    this.graphWidth = this.maximized ? 500 : 250;
    this.graphHeight = this.maximized ? 300 : 150;
    this.diskWidth = this.maximized ? 40 : 20;
    this.diskTextOffset = 2;
    this.diskColOffset = 35;
    this.poolWidth = this.maximized ? 40 : 20;
    this.poolTextOffset = 2;
    this.poolColOffset = 30;
    this.poolRectOffset = 35;

  },


  renderMetrics: function() {
    var _this = this;
    var links = [];
   
    // Disks 
    var disksColumn = this.svg.append('g').attr('class', 'disks-column');
    
    var diskRects = disksColumn.selectAll('g.disk-rect')
    .data(_this.disks)
    .enter()
    .append('rect')
    .attr('class', function(d,i) {
      return (d.get('pool') == null ? 'disk-rect disk-rect-free' : 'disk-rect disk-rect-used')
    })
    .attr('x', _this.diskColOffset)
    .attr('y', function(d, i) { 
      return (_this.graphHeight/_this.disks.length)*i; 
    })
    .attr('width', _this.diskWidth)
    .attr('height', (_this.graphHeight/_this.disks.length)-2);

    var disksText = disksColumn.selectAll('g.disk-text')
    .data(_this.disks)
    .enter();
    
    disksText.append('text')
    .attr('x', 2)
    .attr('y', function(d, i) { 
      var unit = _this.graphHeight / _this.disks.length;
      return (unit*i) + unit/2;
    })
    .style("text-anchor", "start")
    .text(function(d,i) {
      return d.get('name');
    });
    disksText.append('text')
    .attr('x', _this.diskTextOffset)
    .attr('y', function(d, i) { 
      var unit = _this.graphHeight / _this.disks.length;
      return (unit*i) + unit/2 + 12;
    })
    .style("text-anchor", "start")
    .text(function(d,i) {
      return d.get('size')/(1024*1024) + ' GB';
    });

    diskRects.each(function(d,i) {
      var pool = d.get('pool');
      console.log('pool');
      if (pool != null) {
        if (links[pool] == null) {
          links[pool] = [];
        }
        links[pool].push({'source': {
          x: _this.diskColOffset + _this.diskWidth,
          y: ((_this.graphHeight/_this.disks.length)*i) +
            (_this.graphHeight/_this.disks.length)/2 
        }});
      }
    });
    console.log(links);

    // Pools
    var poolsColumn = this.svg.append('g').attr('class', 'pools-column')
    .attr("transform", function(d, i) { 
      var x = _this.diskColOffset + _this.diskWidth + _this.poolColOffset;
      var y = _this.poolsColYOffset;
      return "translate(" + x + "," + y + ")";
    });
  
    var poolRects = poolsColumn.selectAll('g.pool-rect')
    .data(_this.pools)
    .enter()
    .append('rect')
    .attr('class', function(d,i) {
      return 'pool-rect pool-rect-used';
    })
    .attr('x', _this.poolRectOffset)
    .attr('y', function(d, i) { 
      // sum heights of all pools before this one
      return _.reduce(_this.pools, function(sum, pool, j) {
        return j < i ?  sum +=  _this.y(pool.sizeGB()) : sum;
      }, 0, _this);
    })
    .attr('width', _this.poolWidth)
    .attr('height', function(d, i) { 
      //return _this.y(d.sizeGB()) - 2;
      return _this.y(d.sizeGB())-2;
    });

    // Used space for pool 
    //poolRects.append('rect')
    //.attr('class', function(d,i) {
      //return 'pool-rect pool-rect-used';
    //})
    //.attr('x', _this.poolRectOffset)
    //.attr('y', function(d, i) { 
      //// sum heights of all pools before this one
      //var tmp = _.reduce(_this.pools, function(sum, pool, j) {
        //return j < i ?  sum +=  _this.y(pool.sizeGB()) : sum;
      //}, 0, _this);
      //// y is height of previous pools + height of used for current pool
      //tmp = tmp + _this.y(d.freeGB());
      //return tmp;
    //})
    //.attr('width', _this.poolWidth)
    //.attr('height', function(d, i) { 
      ////return _this.y(d.sizeGB()) - 2;
      //return _this.y(d.usedGB());
    //})

     
    var poolsText = poolsColumn.selectAll('g.pool-text')
    .data(_this.pools)
    .enter();
    
    poolsText.append('text')
    .attr('x', _this.poolRectOffset-1)
    .attr('y', function(d, i) { 
      // sum heights of all pools before this one
      var ht = _.reduce(_this.pools, function(sum, pool, j) {
        return j < i ?  sum +=  _this.y(pool.sizeGB()) : sum;
      }, 0, _this);
      // move text to middle of current pool rect
      ht += _this.y(d.sizeGB())/2;
      console.log(ht);
      return ht;
    })
    .style("text-anchor", "end")
    .text(function(d,i) {
      return d.get('name');
    });

    poolsText.append('text')
    .attr('x', _this.poolRectOffset-1)
    .attr('y', function(d, i) { 
      var ht = _.reduce(_this.pools, function(sum, pool, j) {
        return j < i ?  sum +=  _this.y(pool.sizeGB()) : sum;
      }, 0, _this);
      // move text to middle of current pool rect
      ht += _this.y(d.sizeGB())/2;
      ht += 12; // offset for pool name
      return ht;
    })
    .style("text-anchor", "end")
    .text(function(d,i) {
      return d.sizeGB() + ' GB';
    });
    
    console.log(poolRects); 
    poolRects.each(function(d,i) {
      var tmp = _.reduce(_this.pools, function(sum, pool, j) {
        return j < i ?  sum +=  _this.y(pool.sizeGB()) : sum;
      }, 0, _this);
      console.log(d.get('id'));
      _.each(links[d.get('id')], function(d1) {
        d1['target'] = {
          x: _this.diskColOffset + _this.diskWidth + _this.poolColOffset + _this.poolRectOffset,
          y: tmp + _this.y(d.sizeGB()/2) + _this.poolsColYOffset
        }
      });
    });
    console.log(links);
  
    // Disk - pool connectors
    //var diagonal = d3.svg.diagonal()
    var diagonal = d3.svg.diagonal()
    .source(function(d) { return {"x":d.source.y, "y":d.source.x}; })            
    .target(function(d) { return {"x":d.target.y, "y":d.target.x}; })
    .projection(function(d) { return [d.y, d.x]; });

    links = _.flatten(_.values(links));
    console.log(links);
    var link = this.svg.selectAll(".metric-link")
    .data(links)
    .enter().append("path")
    .attr("class", "metric-link")
    .attr("d", diagonal); 
  },

  renderLegend: function() {
    this.$('#ph-metrics-legend').empty();
    var html = 'Raw Storage capacity: ' + this.raw + ' GB';
    html += '<br>';
    html += '<div style="float: left; width: 10px; height: 10px;" class="legend-disk-used"></div>' +
      '&nbsp;'+
      '<div style="float: left">' +  
      'Provisioned: ' + this.diskProvisioned + ' GB' + 
      '</div>' + 
      '&nbsp;'+
      '<div style="float: left; width: 10px; height: 10px;" class="legend-disk-free"></div>' +
      '<div style="float: left">' +  
      'Free: ' + this.diskFree + ' GB'; 
      '</div>';
    var dataset = [this.raw, this.diskProvisioned, this.diskFree]
    var dataLabels = ['Raw Storage Capacity', 'Provisioned', 'Unprovisioned']
     
    this.legendSvg = d3.select(this.el).select('#ph-metrics-legend')
    .append('svg')
    .attr('width', this.graphWidth)
    .attr('height', 100);

    var labels = this.legendSvg.selectAll("g.labels")
    .data(dataLabels)
    .enter()
    .append("g")
    .attr("transform", function(d,i) {
      return "translate(0," + (5 + i*20)+ ")";
    });

    labels.append("rect")
    .attr("width", function(d,i){
      return i == 0 ? 0 : 13;
    })
    .attr("height", function(d,i) {
      return i == 0 ? 0 : 13;
    })
    .attr("class", function(d,i) {
      if (i==1) {
        return 'disk-rect-used';
      } else {
        return 'disk-rect-free';
      }
         
    });
    
    labels.append("text")
    .attr("text-anchor", "left")
    .attr("transform", function(d,i) {
      if (i==0) {
        return "translate(0,13)";
      } else {
        return "translate(16,13)";
      }
    })
    .text(function(d,i) {
      return d + ' ' + dataset[i] + ' GB';
    });

    //this.$('#ph-metrics-legend').html(html);

  },

  
  resize: function(event) {
    this.constructor.__super__.resize.apply(this, arguments);
    this.setGraphDimensions();
    //this.renderTopShares();
  }

});

RockStorWidgets.widgetDefs.push({ 
    name: 'storage_metrics', 
    displayName: 'Storage Metrics', 
    view: 'StorageMetricsWidget',
    description: 'Display top shares by usage',
    defaultWidget: true,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage', 
    position: 6,
});




