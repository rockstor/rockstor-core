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

CpuUsageModule = RockstorModuleView.extend({

    initialize: function() {
        this.template = window.JST.home_cpuusage;
        this.module_name = 'cpuusage';
    },
    render: function() {
        var _this = this;
        $(this.el).html(this.template({
            module_name: this.module_name
        }));

        // display cpu graph 
        var w = 300; // width
        var h = 200; // height
        var padding = 30;
        var id = '#cpuusage';
        /*
        var graph = d3.select(this.el).select(id).append("svg:svg")
        .attr("width", w)
        .attr("height", h);
        */
        var elem = this.$(id)[0];
        var max_y = 100;
        var xscale = d3.scale.linear().domain([0, 120]).range([padding, w]);
        var yscale = d3.scale.linear().domain([0, 100]).range([0, h - padding]);
        var xdiff = xscale(1) - xscale(0);

        var initial = true;
        var cpu_data = null;
        displayGraph(elem, w, h, padding, cpu_data, xscale, yscale, 1000, 1000);

        /*
        RockStorSocket.addListener(function(cpu_data) {
          if (!_.isNull(cpu_data)) {
            if (initial) {
              displayGraph(elem, w, h, padding, cpu_data, 
              xscale, yscale, 1000, 1000);
              initial = false;

            } else {
              redrawWithAnimation(elem, 
              cpu_data, w, h, padding, xscale, yscale, xdiff);

            }
          }
        }, this, 'cpu_util');
        */
        return this;
    }

});