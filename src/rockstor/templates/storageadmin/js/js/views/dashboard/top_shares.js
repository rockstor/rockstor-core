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
    this.numTop = 10;
    this.graphWidth = this.maximized ? 400 : 250;
    this.rowHeight = this.maximized ? 40 : 20;
    this.barHeight = 12;
    this.barWidth = this.maximized ? 120 : 60;
    this.x = d3.scale.linear().domain([0,100]).range([0, this.barWidth]);
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
        _this.renderTopShares();
      }
    }) 
    return this;
  },
 
  renderTopShares: function() {
    var _this = this;
    this.data = this.shares.sortBy(function(s) {
      return ((s.get('usage')/s.get('size'))*100);
    }).slice(0,this.numTop).reverse();
    this.data.map(function(d) { 
      d.set({'pUsed': ((d.get('usage')/d.get('size'))*100)});
    });

    this.svg = d3.select(this.el).select('#ph-top-shares-graph')
    .append('svg')
    .attr('class', 'top-shares')
    .attr('width', this.graphWidth)
    .attr('height', this.rowHeight * this.data.length)
   
    // Header 
    var titleRow = this.svg.append('g')
    .attr('class','.title-row');
    
    titleRow.append("text")  
    .attr('class', 'title')
    .attr('x', 0)
    .attr('y', 10)
    .style("text-anchor", "left")
    .text('Share')

    titleRow.append("text")  
    .attr('class', 'title')
    .attr('x', 75)
    .attr('y', 10)
    .style("text-anchor", "left")
    .text('Used')

    titleRow.append("text")  
    .attr('class', 'title')
    .attr('x', 75 + 75)
    .attr('y', 10)
    .style("text-anchor", "left")
    .text('% Used')

    var dataRow = this.svg.selectAll('g.data-row')
    .data(this.data)
    .attr('class', 'data-row')
    .enter().append('g')
    .attr("transform", function(d, i) { 
      return "translate(0," + ((i+1) * _this.rowHeight) + ")"; 
    });

    // Share Name
    dataRow.append("text")  
    .attr('x', 0)
    .attr('y', 10)
    .style("text-anchor", "left")
    .text(function(d) { return d.get('name'); });
    
    // Share usage in KB
    dataRow.append("text")  
    .attr('x', 75)
    .attr('y', 10)
    .style("text-anchor", "left")
    .text(function(d) { return humanize.filesize(d.get('usage')*1024); });

    // % Used bar
    dataRow.append('rect')
    .attr('class', 'bar used')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', function(d) { return _this.x(d.get('pUsed')); })
    .attr('height', this.barHeight - 1)
    .attr('transform', function(d, i) { return 'translate(' + (75 + 75) + ',0)'; });
   
    // % Unused bar 
    dataRow.append('rect')
    .attr('class', 'bar unused')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', function(d) { return _this.barWidth - _this.x(d.get('pUsed')); })
    .attr('height', this.barHeight - 1)
    .attr('transform', function(d, i) { return 'translate(' +  (75 + 75 + _this.x(d.get('pUsed'))) + ',0)'; });
    
    // % Used text 
    dataRow.append("text")  
    .attr('x', 75 + 75 + this.barWidth + 2)
    .attr('y', 10)
    .style("text-anchor", "left")
    .text(function(d) { return d.get('pUsed').toFixed(2) + '%' });

  },

  resize: function(event) {
    this.constructor.__super__.resize.apply(this, arguments);
    this.graphWidth = this.maximized ? 400 : 200;
    this.barHeight = this.maximized ? 40 : 20;
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



