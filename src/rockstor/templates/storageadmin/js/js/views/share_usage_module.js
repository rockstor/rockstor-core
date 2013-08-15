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

ShareUsageModule = RockstoreModuleView.extend({
  
  initialize: function() {
    this.template = window.JST.share_share_usage_module;
    this.module_name = 'share-usage';
  },

  render: function() {
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      model: this.model,
      collection: this.collection
    }));
    //this.renderGraph();
    this.renderBar();
    return this;
  },
   
  renderBar: function() {
    var _this = this;
    var w = 300;
    var h = 100;
    var barHeight = 10; 

    total = parseInt(this.model.get('size')*1024);
    used = parseInt(this.model.get('usage')*1024);
    free = total - used;
    var dataSet = [70, 30]; 
    //var data = [Math.round((used/total)*100), 
    //Math.round((free/total)*100)];
    var data = [70,30]; //convert to percentages
    var dataLabels = ['used', 'free']
    var colors = {
      used: {fill: "rgb(128,128,128)", stroke: "rgb(122,122,122)"},
      free: {fill: "rgb(168,247,171)", stroke: "rgb(122,122,122)"}, 
    };

    var svg = d3.select(this.el).select("#chart")
    .append("svg")
    .attr("width", w)
    .attr("height", h);

    var xScale = d3.scale.linear().domain([0, 100]).range([0, w]);
    var xOffset = function(i) {
      return i == 0 ? 0 : xScale(data[i-1]);
    }

    var gridContainer = svg.append("g");
    gridContainer.selectAll("rect")
    .data(data)
    .enter()
    .append("rect")
    .attr("y",0)
    .attr("height", barHeight)
    .attr("x", function(d, i) { return xOffset(i); })
    .attr("width", function(d) { return xScale(d); })
    .attr("fill", function(d, i) {
      return colors[dataLabels[i]].fill;
    })
    .attr("stroke", function(d, i) {
      return colors[dataLabels[i]].stroke;
    })

    var labels = svg.selectAll("g.labels")
    .data(dataLabels)
    .enter()
    .append("g")
    .attr("transform", function(d,i) {
      return "translate(10," + (15 + i*30)+ ")";
    });

    labels.append("rect")
    .attr("width", 13)
    .attr("height", 13)
    .attr("fill", function(d, i) {
      return colors[d].fill;
    })
    .attr("stroke", function(d, i) {
      return colors[d].stroke;
    });

    labels.append("text")
    .attr("text-anchor", "left")
    .attr("class", "legend")
    .attr("transform", function(d,i) {
      return "translate(16,13)";
    })
    .text(function(d,i) {
      return data[i] + '% ' + d + ' - ' + humanize.filesize(dataSet[i]);;
    });
  },

  renderGraph: function() {
    var w = 350;                        //width
    h = 250;                            //height
    var outerRadius = 50;
    var innerRadius = 0;
    
    total = parseInt(this.model.get('size')*1024);
    used = parseInt(this.model.get('usage')*1024);
    free = total - used;
    var data = [Math.round((used/total)*100), 
    Math.round((free/total)*100)];
    var labels = ['used', 'free']

    var svg = d3.select(this.el).select("#chart")
    .append("svg")
    .attr("width", w)
    .attr("height", h);
    
    displayUsagePieChart(svg, outerRadius, innerRadius, w, h, dataset, dataLabels);

  }
});


