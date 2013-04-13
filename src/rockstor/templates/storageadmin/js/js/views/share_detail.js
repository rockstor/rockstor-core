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
 * Share Detail View
 */

ShareDetailView = Backbone.View.extend({
  tagName: 'div',
  initialize: function() { 
    this.snapshotsTableView = new SnapshotsTableView(); 
  },
  render: function() {
    this.template = window.JST.share_share_detail_template;
    var _this = this;
    this.model.fetch({
      success: function(model, response) {
        $(_this.el).empty();
        $(_this.el).append(_this.template({ share: model }));
               
        // Pie chart
        var w = 250,                        //width
        h = 250,                            //height
        r = 100,                            //radius
        //color = d3.scale.category20c();     //builtin range of colors
        total_size = parseInt(model.get('size'));
        free_size = parseInt(model.get('free'));
        used_size = total_size - free_size;
        data = [{"label":"used", "value":used_size, "color":"#7C807D"},
        {"label":"free", "value":free_size, "color": "#3AF265"}];

        var vis = d3.select("#chart")
        .append("svg:svg")              //create the SVG element inside the <body>
        .data([data])                   //associate our data with the document
        .attr("width", w)           //set the width and height of our visualization (these will be attributes of the <svg> tag
          .attr("height", h)
          .append("svg:g")                //make a group to hold our pie chart
          .attr("transform", "translate(" + r + "," + r + ")")    //move the center of the pie chart from 0, 0 to radius, radius

          var arc = d3.svg.arc()              //this will create <path> elements for us using arc data
          .outerRadius(r);

          var pie = d3.layout.pie()           //this will create arc data for us given a list of values
          .value(function(d) { return d.value; });    //we must tell it out to access the value of each element in our data array

          var arcs = vis.selectAll("g.slice")     //this selects all <g> elements with class slice (there aren't any yet)
          .data(pie)                          //associate the generated pie data (an array of arcs, each having startAngle, endAngle and value properties)
          .enter()                            //this will create <g> elements for every "extra" data element that should be associated with a selection. The result is creating a <g> for every object in the data array
          .append("svg:g")                //create a group to hold each slice (we will have a <path> and a <text> element associated with each slice)
          .attr("class", "slice");    //allow us to style things in the slices (like text)

          arcs.append("svg:path")
          .attr("fill", function(d, i) { return data[i].color; } ) //set the color for each slice to be chosen from the color function defined above
          .attr("d", arc);                                    //this creates the actual SVG path using the associated data (pie) with the arc drawing function

          arcs.append("svg:text")                                     //add a label to each slice
          .attr("transform", function(d) {                    //set the label's origin to the center of the arc
            //we have to make sure to set these before calling arc.centroid
            d.innerRadius = 0;
            d.outerRadius = r;
            return "translate(" + arc.centroid(d) + ")";        //this gives us a pair of coordinates like [50, 50]
          })
          .attr("text-anchor", "middle")                          //center the text on it's origin
          .text(function(d, i) { return data[i].label; });        //get the label from our original data array
          
          // create snapshot button
          _this.$('button[rel]').overlay();

          // create snapshot form submit
          _this.$('#create_snapshot').click(function() {
            $.ajax({
              url: "/api/shares/" + model.get('name') + "/snapshots/",
              type: "POST",
              dataType: "json",
              data: { name: $('#snapshot_name').val()}
            }).done(function() {
              _this.$('#snapshot_popup_button').overlay().close();
              _this.$('#snapshots').empty().append(_this.snapshotsTableView.render().el);
            }).fail(function() {
              alert('error while creating snapshot');
            });
          });

          _this.$('#export_nfs').click(function() {
            console.log('exporting!');
            $.ajax({
              url: "/api/shares/"+_this.model.get('name')+'/nfs-export/',
              type: "PUT",
              dataType: "json",
              data: { pool: model.get('pool'), name: model.get('name'), size: '10', mount: '/mnt2/'+model.get('name'), host_str: $('#host_string').val(), options: $('#nfs_option').val()},
	      success: function() {
		  _this.$('button[rel]').overlay().close();
		  console.log('exported nfs');
	      },
	      error: function(request, status, error) {
		  alert(request.responseText);
	      }
            });
          });

	  _this.$('#smb_share').click(function() {
	    $.ajax({
	      url: "/api/shares/"+_this.model.get('name')+'/cifs-export/',
	      type: "PUT",
	      dataType: "json",
              data: { pool: model.get("pool"), name: model.get('name'), size: '10', mount: '/mnt2/'+model.get('name')},
	      success: function() {
		  _this.$('button[rel]').overlay().close();
	      },
	      error: function(request, status, error) {
		  alert(request.responseText);
	      }
	    });
	  });

          // snapshot list
          _this.snapshotsTableView.setShareName(model.get('name'));
          _this.$('#snapshots').empty().append(_this.snapshotsTableView.render().el);
      }
    });

    return this;
  }
});
