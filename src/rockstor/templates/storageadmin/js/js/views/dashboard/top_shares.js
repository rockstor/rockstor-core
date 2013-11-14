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


TopSharesWidget = RockStorWidgetView.extend({

  initialize: function() {
    var _this = this;
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_top_shares;
    this.shares = new ShareCollection();
    this.shares.pageSize = 1000;
    this.numTop = 5;
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
    this.shares.fetch({
      success: function(collection, response, options) {
        _this.setData();
        _this.setGraphDimensions();
        _this.renderTopShares();
      }
    }) 
    return this;
  },
  
  setData: function() {
    this.data = this.shares.sortBy(function(s) {
      return ((s.get('usage')/s.get('size'))*100);
    }).reverse().slice(0,this.numTop);
    this.data.map(function(d) { 
      d.set({'pUsed': ((d.get('usage')/d.get('size'))*100)});
    });
  },

  setGraphDimensions: function() {
    this.graphWidth = this.maximized ? 500 : 250;
    this.rowHeight = this.maximized ? 60 : 30;
    this.barHeight = this.maximized? 60: 30;
    this.barWidth = this.maximized ? 350 : 175;
    this.x = d3.scale.linear().domain([0,100]).range([0, this.barWidth]);
  },

  renderTopShares: function() {
    var _this = this;

    // Get top shares by % used
    var tip = d3.tip()
    .attr('class', 'd3-tip')
    .offset([-10, 0])
    .html(function(d) {
      return '<strong>' + d.get('name') + '</strong>' + '<br>' + 'Used: ' +
        humanize.filesize(d.get('usage')*1024) + '<br>' +
        'Free: ' + 
        humanize.filesize((d.get('size')-d.get('usage'))*1024); 
    })

    this.svg = d3.select(this.el).select('#ph-top-shares-graph')
    .append('svg')
    .attr('class', 'top-shares')
    .attr('width', this.graphWidth)
    .attr('height', this.rowHeight * (this.data.length+2))
    
    this.svg.call(tip);

    // Header 
    var titleRow = this.svg.append('g')
    .attr('class','.title-row');
    
    titleRow.append("text")  
    .attr('class', 'title')
    .attr('x', 0)
    .attr('y', 10)
    .style("text-anchor", "start")
    .text('Top ' + this.numTop + ' shares sorted by % used')

    // Data rows
    var dataRow = this.svg.selectAll('g.data-row')
    .data(this.data)
    .enter().append('g')
    .attr('class', 'data-row')
    .attr("transform", function(d, i) { 
      return "translate(0," + ((i+1) * _this.rowHeight) + ")"; 
    });
    
    // % Used text 
    dataRow.append("text")  
    .attr('x', 0)
    .attr('y', 20)
    .style("text-anchor", "start")
    .text(function(d) { return d.get('pUsed').toFixed(2) + '%' });
   
    // % Used bar 
    dataRow.append('rect')
    .attr('class', 'bar used')
    .attr('x', 50)
    .attr('y', 0)
    .attr('width', function(d) { return _this.x(d.get('pUsed')); })
    .attr('height', this.barHeight - 2);
   
    // % Unused bar 
    dataRow.append('rect')
    .attr('class', 'bar unused')
    .attr('x', function(d) { return 50 + _this.x(d.get('pUsed'));})
    .attr('y', 0)
    .attr('width', function(d) { return _this.barWidth - _this.x(d.get('pUsed')); })
    .attr('height', this.barHeight - 2);
    
    // Share Name
    dataRow.append("text")  
    .attr('class', 'share-name')
    .attr('x', 45 + this.barWidth)
    .attr('y', 20)
    .style("text-anchor", "end")
    .text(function(d) { return d.get('name') + ' (' + humanize.filesize(d.get('usage')*1024) + ')'; })
    .on('mouseover', tip.show)
    .on('mouseout', tip.hide);
    
    // Legend

    var legend = this.svg.append('g')
    .attr('class', 'legend')
    .attr("transform", function(d, i) { 
      return "translate(0," + ((_this.data.length + 1) * _this.rowHeight) + ")"; 
    });

    legend.append('rect')
    .attr('x', 50)
    .attr('y', 10)
    .attr('width', 10)
    .attr('height', 10)
    .attr('class', 'bar used');
    
    legend.append('text')
    .attr('x', 50 + 10 + 2)
    .attr('y', 20)
    .style("text-anchor", "start")
    .text('Used');

    legend.append('rect')
    .attr('x', 50 + 50)
    .attr('y', 10)
    .attr('width', 10)
    .attr('height', 10)
    .attr('class', 'bar unused');

    legend.append('text')
    .attr('x', 50 + 50 + 10 + 2)
    .attr('y', 20)
    .style("text-anchor", "start")
    .text('Free');

  },
  
  resize: function(event) {
    this.constructor.__super__.resize.apply(this, arguments);
    this.$('#ph-top-shares-graph').empty();
    this.setGraphDimensions();
    this.renderTopShares();
  }

});

RockStorWidgets.widgetDefs.push({ 
    name: 'top_shares', 
    displayName: 'Top Shares by Usage', 
    view: 'TopSharesWidget',
    description: 'Display top shares by usage',
    defaultWidget: false,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage', 
});



