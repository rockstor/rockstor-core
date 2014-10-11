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
    this.rawStorageCapacity = 0; // raw storage capacity in GB
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
 
   
  renderViz: function() {
    // sort disks and shares by pool
    this.disks = this.disks.sortBy(function(disk) { return -disk.get('pool'); }, this);
    this.pools = this.pools.sortBy(function(pool) { return -pool.id }, this);
    this.shares = this.shares.sortBy(function(share) { return -share.get('pool').id }, this);
    var sum = this.disks.reduce(function(sum, disk) {
      sum += disk.get('size');
      return sum;
    }, 0);
    this.rawStorageCapacity = Math.round(sum / (1024*1024));
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
    this.y = d3.scale.linear().domain([0,this.rawStorageCapacity]).range([0, this.graphHeight]);
    console.log(this.disks);
    console.log(this.pools);
    console.log(this.shares);

    //this.setData();
    this.$('#ph-metrics-viz').empty();
    this.svg = d3.select(this.el).select('#ph-metrics-viz')
    .append('svg')
    .attr('class', 'metrics')
    .attr('width', this.graphWidth)
    .attr('height', this.graphHeight);
    
    this.renderMetrics();
    this.renderLegend();
    //this.renderTopShares();
  },

  //setData: function() {
    //this.data = this.shares.sortBy(function(s) {
      //return ((s.get('r_usage')/s.get('size'))*100);
    //}).reverse().slice(0,this.numTop);
    //this.data.map(function(d) { 
      //d.set({'pUsed': ((d.get('r_usage')/d.get('size'))*100)});
    //});
  //},

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

  //renderTopShares: function() {
    //var _this = this;

    //// Get top shares by % used
    //var tip = d3.tip()
    //.attr('class', 'd3-tip')
    //.offset([-10, 0])
    //.html(function(d) {
      //return '<strong>' + d.get('name') + '</strong><br>' + 
        //'   <strong>Used:</strong> ' +
        //humanize.filesize(d.get('r_usage')*1024) + '<br>' + 
        //' <strong>Free:</strong> ' + 
        //humanize.filesize((d.get('size')-d.get('r_usage'))*1024); 
    //})

    //this.svg = d3.select(this.el).select('#ph-top-shares-graph')
    //.append('svg')
    //.attr('class', 'top-shares')
    //.attr('width', this.graphWidth)
    //.attr('height', this.graphHeight);
    
    //this.svg.call(tip);

    //// Header 
    //var titleRow = this.svg.append('g')
    //.attr('class','.title-row');
    
    //titleRow.append("text")  
    //.attr('class', 'title')
    //.attr('x', 0)
    //.attr('y', this.textOffset)
    //.style("text-anchor", "start")
    //.text('Top ' + this.data.length + ' shares sorted by % used')

    //// Data rows
    //var dataRow = this.svg.selectAll('g.data-row')
    //.data(this.data)
    //.enter().append('g')
    //.attr('class', 'data-row')
    //.attr("transform", function(d, i) { 
      //return "translate(0," + ((i+1) * _this.rowHeight) + ")"; 
    //});
    
    //// % Used text 
    //dataRow.append("text")  
    //.attr('class', 'usedpc')
    //.attr('x', 45)
    //.attr('y', this.textOffset)
    //.style("text-anchor", "end")
    //.text(function(d) { return d.get('pUsed').toFixed(2) + '%' });
   
    //// % Unused bar 
    //dataRow.append('rect')
    //.attr('class', 'bar unused')
    ////.attr('x', function(d) { return 50 + _this.x(d.get('pUsed'));})
    //.attr('x', 50)
    //.attr('y', 0)
    //.attr('rx', 4)
    //.attr('ry', 4)
    //.attr('width', _this.barWidth)
    ////.attr('width', function(d) { return _this.barWidth - _this.x(d.get('pUsed')); })
    //.attr('height', this.barHeight - 2);
    
    //// % Used bar 
    //dataRow.append('rect')
    //.attr('class', 'bar used')
    //.attr('x', 50)
    //.attr('y', 0)
    //.attr('rx', 4)
    //.attr('ry', 4)
    //.attr('width', function(d) { return _this.x(d.get('pUsed')); })
    //.attr('height', this.barHeight - 2);
    
    //// Share Name
    //dataRow.append("text")  
    //.attr('class', 'share-name')
    //.attr('x', 45 + this.barWidth)
    //.attr('y', this.textOffset)
    //.style("text-anchor", "end")
    //.text(function(d) { 
      //var n = d.get('name');
      //// truncate name to 15 chars
      //if (n.length > 15) {
        //n = n.slice(0,12) + '...';
      //}
      //return n + ' (' + humanize.filesize(d.get('r_usage')*1024) + 
        //'/' + humanize.filesize(d.get('size')*1024) + 
        //')' ; 
    //})
    //.on('mouseover', tip.show)
    //.on('mouseout', tip.hide);
    
    //// Legend
    //var legend = this.svg.append('g')
    //.attr('class', 'legend')
    //.attr("transform", function(d, i) { 
      //return "translate(0," + ((_this.data.length + 1) * _this.rowHeight) + ")"; 
    //});

    //legend.append('rect')
    //.attr('x', 50)
    //.attr('y', 10)
    //.attr('width', 10)
    //.attr('height', 10)
    //.attr('class', 'bar used');
    
    //legend.append('text')
    //.attr('x', 50 + 10 + 2)
    //.attr('y', 20)
    //.style("text-anchor", "start")
    //.text('Used');

    //legend.append('rect')
    //.attr('x', 50 + 50)
    //.attr('y', 10)
    //.attr('width', 10)
    //.attr('height', 10)
    //.attr('class', 'bar unused');

    //legend.append('text')
    //.attr('x', 50 + 50 + 10 + 2)
    //.attr('y', 20)
    //.style("text-anchor", "start")
    //.text('Free');

  //},

  renderMetrics: function() {
    var _this = this;
   
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

    // Pools
    var poolsColumn = this.svg.append('g').attr('class', 'pools-column')
    .attr("transform", function(d, i) { 
      var x = _this.diskColOffset + _this.diskWidth + _this.poolColOffset;
      return "translate(" + x + ",0)";
    });

    var poolRects = poolsColumn.selectAll('g.pool-rect')
    .data(_this.pools)
    .enter()
    .append('rect')
    .attr('class', function(d,i) {
      return 'pool-rect';
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
      return _this.y(d.sizeGB()) - 2;
    })
   
     
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
    
    
  },

  renderLegend: function() {
    this.$('#ph-metrics-legend').empty();
    var html = 'Raw Storage capacity: ' + this.rawStorageCapacity + ' GB';
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
    var dataset = [this.rawStorageCapacity, this.diskProvisioned, this.diskFree]
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




