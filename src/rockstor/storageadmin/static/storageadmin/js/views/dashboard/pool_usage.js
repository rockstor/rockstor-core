/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2013-2016 RockStor, Inc. <http://rockstor.com>
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

        var _this = this;
        _this.data = this.pools.sortBy(function(p) {
            return p.get('name');
        }).slice(0, this.numTop);
        _this.data.map(function(d) {
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

        var _this = this;
        _this.barHeight = _this.maximized ? 40 : 18;
        _this.barWidth = _this.maximized ? 440 : 190;
        _this.valign = _this.maximized ? 10 : 0;
    },

    renderPools: function() {

        var _this = this;
        _.each(_this.data, function(d) {
            var html = _this.buildProgressbar();
            this.$('#pool-usage-graph').append(html);
        });

        this.$('.pused').each(function(index) {
            $(this).text(_this.data[index].get('percentUsed').toFixed(2) + '%');
        });
        var truncate = _this.maximized ? 100 : 12;
        this.$('.progress-animate').each(function(index) {
            $(this).find('span')
                .text(humanize.truncatechars(_this.data[index].get('name'), truncate) +
                    '(' + humanize.filesize(_this.data[index].get('bytesUsed') * 1024) +
                    '/' + humanize.filesize(_this.data[index].get('bytesFree') * 1024) +
                    ')');
            $(this).animate({
                width: _this.data[index].get('percentUsed').toFixed(2) + '%'
            }, 1000);
        });
    },

    buildProgressbar: function() {

        var _this = this;
        var percent_div = {
            class: 'pused',
            style: 'font-size: 10px; text-align: right; padding-right: 5px; display: table-cell; width: 50px; vertical-align: middle;'
        };
        var progressbar_container = {
            class: 'progress',
            style: 'display: inline-block; margin: 0px; position: relative; height: ' + _this.barHeight + 'px; width: ' + _this.barWidth + 'px;'
        };
        var progressbars_defaults = {
            class: 'progress-bar progress-animate',
            role: 'progressbar',
            style: 'width: 0%; -webkit-transition: none !important; transition: none !important;'
        };
        var progressbar_span = {
            style: 'font-size: 10px; position: absolute; color: black; right: 5px; top: ' + _this.valign + 'px'
        };

        var html = '<div style="display: table;"><div class="' + percent_div['class'] + '" style="' + percent_div['style'] + '"></div>';
        html += '<div class="' + progressbar_container['class'] + '" style="' + progressbar_container['style'] + '">';
        html += '<div class="' + progressbars_defaults['class'] + '" style="' + progressbars_defaults['style'] + '" ';
        html += 'role="' + progressbars_defaults['role'] + '">';
        html += '<span style="' + progressbar_span['style'] + '"></span></div></div></div>';

        return html;
    },

    resize: function(event) {

        var _this = this;
        this.constructor.__super__.resize.apply(this, arguments);
        _this.$('#pool-usage-graph').empty();
        _this.setGraphDimensions();
        _this.renderPools();
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