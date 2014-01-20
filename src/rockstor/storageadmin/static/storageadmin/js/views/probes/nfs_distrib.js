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

NfsDistribView = Backbone.View.extend({
  initialize: function() {
    this.probe = this.options.probe;
    this.template = window.JST.probes_nfs_distrib;
  },

  render: function() {
    $(this.el).html(this.template({probe: this.probe}));
    this.showNfsIO(this.probe.dataUrl());
    return this;
  },

  showNfsIO: function(probeDataUrl) {
    var _this = this;
    // set title
    this.$('#nfs-title').html(this.probe.get('name'));

    // clear rendering area
    this.$('#nfs-graph').empty();

    // create context
    this.cubism_context = cubism.context()
    .step(1e3)
    .size(600);
    
    // create horizon
    this.horizon = this.cubism_context.horizon()
    .colors(['#08519c', '#bae4b3'])
    .height(60);

    // axis
    d3.select(this.el).select("#nfs-graph").selectAll(".axis")
    .data(["top", "bottom"])
    .enter().append("div")
    .attr("class", function(d) { return d + " axis"; })
    .each(function(d) { 
      d3.select(this).call(_this.cubism_context.axis().ticks(12).orient(d)); 
    });

    d3.select(this.el).select("#nfs-graph").append("div")
    .attr("class", "rule")
    .call(_this.cubism_context.rule());
    
    var nfsContext = this.cubism_context.nfs();
    var nfsMetricRead = nfsContext.metric('Reads/sec', 'num_read', probeDataUrl);
    var nfsMetricWrites = nfsContext.metric('Writes/sec', 'num_write', probeDataUrl);
    //var nfsMetricLookups = nfsContext.metric('Lookups/sec', recipe_uri);
    //var nfsMetricReadBytes = nfsContext.metric('Bytes read/sec', recipe_uri);
    //var nfsMetricWriteBytes = nfsContext.metric('Bytes written/sec', recipe_uri);

    d3.select(this.el).select("#nfs-graph").selectAll(".horizon")
    .data([nfsMetricRead, nfsMetricWrites ])
    .enter().insert("div", ".bottom")
    .attr("class", "horizon")
    .call(_this.horizon);

    this.cubism_context.on("focus", function(i) {
      d3.selectAll(".value").style("right", i == null ? null : _this.cubism_context.size() - i + "px");
    });


  },

  cleanup: function() {
    logger.debug('calling cleanup');
    if (!_.isUndefined(this.horizon) && !_.isNull(this.horizon)) {
      d3.select(this.el).select("#nfs-graph").selectAll(".horizon")
      .call(this.horizon.remove).remove();
    }
    logger.debug('removing axes');
    d3.select(this.el).select("#nfs-graph").selectAll(".axis").remove();
    this.cubism_context.stop();

  }

});

RockStorProbeMap.push({
  name: 'nfs-distrib',
  view: 'NfsDistribView',
  description: 'NFS Call Distribution',
});

