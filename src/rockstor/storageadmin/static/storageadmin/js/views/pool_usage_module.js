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

PoolUsageModule = RockstorModuleView.extend({
    initialize: function() {
        this.template = window.JST.pool_pool_usage_module;
        this.module_name = 'pool-usage';
    },

    render: function() {
        $(this.el).html(this.template({
            module_name: this.module_name,
            model: this.model,
            collection: this.collection
        }));
        this.renderGraph();
        return this;
    },

    renderGraph: function() {
        // Pie chart
        var w = 350; //width
        var h = 130; //height
        var outerRadius = 50;
        var innerRadius = 0;

        total = parseInt(this.model.get('size') * 1024);
        used = parseInt((this.model.get('size') - this.model.get('reclaimable') - this.model.get('free')) * 1024);
        free = this.model.get('free') * 1024;

        var dataset = [free, used];
        var dataLabels = ['free', 'used'];

        var svg = d3.select(this.el).select('#chart')
            .append('svg')
            .attr('width', w)
            .attr('height', h);

        displayUsagePieChart(svg, outerRadius, innerRadius, w, h, dataset, dataLabels);

    }
});