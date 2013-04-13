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

/*
 * Pool Detail View
 */

PoolDetailView = Backbone.View.extend({
  tagName: 'div',
  initialize: function() { 
    this.disks = new DiskCollection();
  },
  
  render: function() {
    this.template = window.JST.pool_pool_detail_template;
    this.select_disks_template = window.JST.disk_select_disks_template;
    var _this = this;
    
    this.model.fetch({
      success: function(model, response) {
        $(_this.el).empty();
        $(_this.el).append(_this.template({ pool: model }));

        //Pie chart
        var w = 300,
        h = 300,
        r = 100,

        total_size = parseInt(model.get('size'));
        free_size = parseInt(model.get('free'));
        used_size = total_size - free_size;
        data = [{"label":"used", "value": used_size, "color": "#7C807D"},
        /*{"label":"free", "value":free_size, "color": "#3AF265"}];*/
        {"label":"free", "value":free_size, "color": "#ff0000"}];

        var vis = d3.select("#chart")
        .append("svg:svg")
        .data([data])
        .attr("width", w)
        .attr("height", h)
        .append("svg:g")
        .attr("transform", "translate(" + r + "," + r + ")")

        var arc = d3.svg.arc()
        .outerRadius(r);
        var pie = d3.layout.pie()
        .value(function(d) { return d.value; });

        var arcs = vis.selectAll("g.slice")
        .data(pie)
        .enter()
        .append("svg:g")
        .attr("fill", "slice");

        arcs.append("svg:path")
        .attr("fill", function(d, i) { return data[i].color; })
        .attr("d", arc);

        arcs.append("svg:text")
        .attr("transform", function(d) {
          d.innerRadius = 0;
          d.outerRadius = r;
          return "translate(" + arc.centroid(d) + ")";
        })
        .attr("text-anchor", "middle")
        .text(function(d, i) { return data[i].label; });
        
        _this.$('button[rel]').click(function() {
          _this.disks.fetch({
            success: function(collection, response) {
              console.log('got disks');
              _this.$('#disks_to_add').html(_this.select_disks_template({disks: _this.disks}));
              _this.$('#resize_pool').click(function() {
                var disk_names = '';
                var n = $("input:checked").length;
                $("input:checked").each(function(i) {
                  if (i < n-1) {
                    disk_names += $(this).val() + ',';
                  } else {
                    disk_names += $(this).val();	  
                  }
                });
                console.log(disk_names);
                $.ajax({
                  url: "/api/pools/"+_this.model.get('name')+'/add/',
                  type: "PUT",
                  dataType: "json",
                  data: {"disks": disk_names},
                  success: function() {
                    _this.$('button[rel]').overlay().close();
                  },
                  error: function(request, status, error) {
                    alert(request.responseText);
                  }
                });
              });
              $('#resize_pool_form').overlay().load();
            }});
        });
        _this.$('#resize_pool_form').overlay({ load: false });
      }
    });


      return this;
  }
});
