/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2016 RockStor, Inc. <http://rockstor.com>
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

PoolUsageWidget = RockStorWidgetView.extend({
    initialize: function() {
        var _this = this;
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.dashboard_widgets_pool_usage;
        this.pools = new PoolCollection();
        this.pools.pageSize = RockStorGlobals.maxPageSize;
        this.numTop = 10;
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
        this.pools.fetch({
            success: function(collection, response, options) {
                _this.setData();
                _this.setGraphDimensions();
                _this.renderPools();
        }
        });
        return this;
    },

    setData: function() {
        this.data = this.pools.sortBy(function(p) { return p.get('name'); }).slice(0, this.numTop);
        this.data.map(function(d) {
            var size = d.get('size');
            var bytesFree = d.get('free');
            var bytesUsed = size - bytesFree;
            var percentUsed = 100 * bytesUsed / size;
            d.set({
                'bytesFree': bytesFree,
                'bytesUsed': bytesUsed,
                'percentUsed': percentUsed
            });
        });
    },

    setGraphDimensions: function() {
        this.graphWidth = this.maximized ? 500 : 250;
        this.rowHeight = this.maximized ? 40 : 20;
        this.barHeight = this.maximized? 40: 20;
        this.barWidth = this.maximized ? 350 : 175;
        this.textOffset = this.maximized ? 25 : 12.5;
        this.x = d3.scale.linear().domain([0,100]).range([0, this.barWidth]);
    },

    renderPools: function() {
        var _this = this;

        // Get pool data
        var tip = d3.tip()
        .attr('class', 'd3-tip')
        .offset([-10, 0])
        .html(function(d) {
        return '<strong>' + d.get('name') + '</strong><br>' +
            '   <strong>Used:</strong> ' +
            humanize.filesize(d.get('bytesUsed') * 1024) + '<br>' +
            ' <strong>Free:</strong> ' +
            humanize.filesize(d.get('bytesFree') * 1024);
        })

        this.svg = d3.select(this.el).select('#pool-usage-graph')
        .append('svg')
        .attr('class', 'top-shares') // borrow styling from shares widget
        .attr('width', this.graphWidth)
        .attr('height', this.rowHeight * (this.data.length+2))

        this.svg.call(tip);

        // Header
        var titleRow = this.svg.append('g')
        .attr('class','.title-row');

        titleRow.append("text")
        .attr('class', 'title')
        .attr('x', 0)
        .attr('y', this.textOffset)
        .style("text-anchor", "start")
        .text('Relative and absolute usage of system pools')

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
        .attr('class', 'usedpc')
        .attr('x', 45)
        .attr('y', this.textOffset)
        .style("text-anchor", "end")
        .text(function(d) { return d.get('percentUsed').toFixed(2) + '%' });

        // % Unused bar
        dataRow.append('rect')
        .attr('class', 'bar unused')
        .attr('x', 50)
        .attr('y', 0)
        .attr('rx', 4)
        .attr('ry', 4)
        .attr('width', _this.barWidth)
        .attr('height', this.barHeight - 2);

        // % Used bar
        dataRow.append('rect')
        .attr('class', 'bar used')
        .attr('x', 50)
        .attr('y', 0)
        .attr('rx', 4)
        .attr('ry', 4)
        .attr('width', function(d) { return _this.x(d.get('percentUsed')); })
        .attr('height', this.barHeight - 2);

        // Pool Name
        dataRow.append("text")
        .attr('class', 'share-name')
        .attr('x', 45 + this.barWidth)
        .attr('y', this.textOffset)
        .style("text-anchor", "end")
        .text(function(d) {
            var n = d.get('name');
            // truncate name to 15 chars
            if (n.length > 15) {
                n = n.slice(0,12) + '...';
            }
            return n + ' (' + humanize.filesize(d.get('bytesUsed') * 1024) +
                '/' + humanize.filesize(d.get('size') * 1024) +
                ')' ;
        })
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
        this.$('#pool-usage-graph').empty();
        this.setGraphDimensions();
        this.renderPools();
    }
});

RockStorWidgets.widgetDefs.push({
    name: 'pool_usage',
    displayName: 'Pool Capacity and Usage',
    view: 'PoolUsageWidget',
    description: 'Display pool usage',
    defaultWidget: true,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage',
    position: 3,
});
