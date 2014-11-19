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

NfsView = Backbone.View.extend({
  
  initialize: function() {
    var _this = this;
    this.probe = this.options.probe;
    this.template = window.JST.probes_nfs;
    this.updateInterval = 5000; // update every updateInterval seconds
    this.rawData = null; // data returned from probe backend
    // nfs attributes
    this.attrs = ["num_read", "num_write", "num_lookup", 
    "num_create", "num_commit", "num_remove", "sum_read", "sum_write"];
    this.numSamples = 60; // number of data points stored for graph
    // Initialize empty arrays of length numSamples for attributes
    this.attrArrays = {};
    _.each(this.attrs, function(a) { 
      _this.attrArrays[a] = []; 
      for (var i=0; i<_this.numSamples; i++) { 
        _this.attrArrays[a][i] = null; 
      }
    });
    this.attrGraphOptions = { 
      grid : { 
        //hoverable : true,
        borderWidth: { top: 1, right: 1, bottom: 0, left: 0 },
        borderColor: "#aaa"
      },
      xaxis: {
        min: 0,
        max: this.numSamples,
        tickSize: 60,
        tickFormatter: this.timeTickFormatter(this.numSamples, this.updateInterval),
        axisLabel: "Time (minutes)",
        axisLabelColour: "#000"
      },
      yaxis:  { 
        min: 0, 
        tickFormatter: this.valueTickFormatter,
        axisLabelColour: "#000"
      }, 
			series: {
        //stack: false,
        //bars: { show: false, barWidth: 0.4, fillColor: {colors:[{opacity: 1},{opacity: 1}]}, align: "center" },
        lines: { show: true, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
      legend : { 
        container: "#nfs-attrs-legend", 
        noColumns: 4,
        margin: [30,0],
        labelBoxBorderColor: "#fff"

      },
      //tooltip: true,
      //tooltipOpts: {
        //content: "%s (%y.2)" 
      //}
    };
    this.dataGraphOptions = { 
      grid : { 
        //hoverable : true,
        borderWidth: { top: 1, right: 1, bottom: 0, left: 0 },
        borderColor: "#aaa"
      },
      xaxis: {
        min: 0,
        max: this.numSamples,
        tickSize: 60,
        tickFormatter: this.timeTickFormatter(this.numSamples, this.updateInterval),
        axisLabel: "Time (minutes)",
        axisLabelColour: "#000"
      },
      yaxis:  { 
        min: 0, 
        tickFormatter: this.valueTickFormatter,
        axisLabelColour: "#000"
      }, 
			series: {
        //stack: false,
        //bars: { show: false, barWidth: 0.4, fillColor: {colors:[{opacity: 1},{opacity: 1}]}, align: "center" },
        lines: { show: true, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
      legend : { 
        container: "#nfs-data-legend", 
        noColumns: 4,
        margin: [30,0],
        labelBoxBorderColor: "#fff"

      },
      //tooltip: true,
      //tooltipOpts: {
        //content: "%s (%y.2)" 
      //}
    };
    this.colors = ["#E41A1C", "#377EB8", "#4DAF4A", "#FFFFFF"];
  },

  render: function() {
    $(this.el).html(this.template({
      probe: this.probe, 
      updateInterval: this.updateInterval,
      treeType: this.treeType
    }));
    var _this = this;
    if (this.probe.get("state") == probeStates.RUNNING) {
      var t2 = this.probe.get("start");
      var t1 = moment(t2).subtract("ms",this.updateInterval).toISOString();
      this.update(this.probe, t1, t2, true, this.updateInterval);
    } else if (this.probe.get("state") == probeStates.STOPPED) {
      var t1 = this.probe.get("start");
      var t2 = this.probe.get("end");
      this.update(this.probe, t1, t2, false, null);
    } 
    return this;
  },
  
  update: function(probe, t1, t2, repeat, updateInterval) {
    var _this = this;
    var dataUrl = this.probe.dataUrl() + "?t1=" + t1 + "&t2=" + t2;
    if (repeat) {
      this.renderIntervalId = window.setInterval(function() {
        _this.fetchAndRender(dataUrl);
        // update times
        t1 = t2;
        t2 = moment(t1).add("ms",_this.updateInterval).toISOString();
        dataUrl = _this.probe.dataUrl() + "?t1=" + t1 + "&t2=" + t2;
      }, updateInterval);
    } else {
      this.fetchAndRender(dataUrl);
    }
  },

  fetchAndRender: function(dataUrl) {
    var _this = this;
    $.ajax({
      url: dataUrl,
      type: "GET",
      dataType: "json",
      success: function(data, textStatus, jqXHR) {
        var results = data.results;
        //results = _this.generateData(); // TODO remove after test
        if (!_.isEmpty(results)) {
          _this.renderViz(results);
        }
      },
      error: function(request, status, error) {
       }
    });
  },

  renderViz: function(rawData) {
    var _this = this;
    // Sum all data points to get total for current interval
    var initial = {};
    _.each(this.attrs, function(a) { initial[a] = 0; });
    var data = _.reduce(rawData, function(memo, d) {
      var tmp = {};
      _.each(_this.attrs, function(a) {
        tmp[a] = memo[a] + d[a];
      });
      return tmp;
    }, initial);
    // Add current data point to array at the end, 
    // and remove the first value 
    _.each(this.attrs, function(a) {
      _this.attrArrays[a].push(data[a]);
      _this.attrArrays[a].splice(0,1);
    });
    this.renderAttribs(
      this.attrArrays["num_read"], 
      this.attrArrays["num_write"], 
      this.attrArrays["num_lookup"] 
    );
    this.renderData(this.attrArrays["sum_read"], 
    this.attrArrays["sum_write"]);
    
  },
  
  renderAttribs: function(reads, writes, lookups) {
    var tmp1 = [], tmp2 = [], tmp3 =[];
    for (var i=0; i < this.numSamples; i++) { 
      tmp1.push([i, reads[i]]); 
      tmp2.push([i, writes[i]]); 
      tmp3.push([i, lookups[i]]); 
    }
    var series1 = { label: "Reads", data: tmp1, color: this.colors[0] };
    var series2 = { label: "Writes", data: tmp2, color: this.colors[1] };
    var series3 = { label: "Lookups", data: tmp3, color: this.colors[2] };
    $.plot( this.$("#nfs-attrs"), 
           [series1, series2, series3], 
           this.attrGraphOptions);
  },

  renderData: function(dataRead, dataWritten) {
    var tmp1 = [], tmp2 = [];
    for (var i=0; i < this.numSamples; i++) { 
      tmp1.push([i, dataRead[i]]); 
      tmp2.push([i, dataWritten[i]]); 
    }
    var series1 = { label: "Data read", data: tmp1, color: this.colors[0] };
    var series2 = { label: "Data written", data: tmp2, color: this.colors[1] };
    $.plot( this.$("#nfs-data"), [series1, series2], this.dataGraphOptions);
  },

  cleanup: function() {
    if (!_.isUndefined(this.renderIntervalId) && 
    !_.isNull(this.renderIntervalId)) {
      window.clearInterval(this.renderIntervalId);
    }
  },

  timeTickFormatter: function(dataLength, updateInterval) {
    var t = updateInterval/1000;
    var n = dataLength * t;
     return function(val, axis) {
      return ((n/60) - (parseInt((val*t)/60))).toString() + ' m';
    };
  },

  generateData: function() {
    var data = [];
    for (i=1; i<=3; i++) {
      var ip = "10.0.0." + i;
      for (j=1; j<=2; j++) {
        var share = "share_" + j;
        var uid = 5000 + j;
        var gid = 5000 + j;
        data.push({
          share: share,
          client: ip,
          uid: uid,
          gid: gid,
          num_read: 5 + Math.floor(Math.random() * 5),
          num_write: 1 + Math.floor(Math.random() * 5),
          num_lookup: 1 + Math.floor(Math.random() * 5),
          sum_read: Math.floor(Math.random() * 10),
          sum_write: Math.floor(Math.random() * 15),
        });
      }
    }
    var ipRandom1 = "10.0.0." + (5 + (Math.floor(Math.random() * 5)));
    var share1 = "share_1";
    var uid1 = 5005;
    var gid1 = 5005;
    var ipRandom2 = "10.0.0." + (10 + (Math.floor(Math.random() * 5)));
    var share2 = "share_2";
    var uid2 = 5006;
    var gid2 = 5006;
    var ipRandom3 = "10.0.0." + (15 + (Math.floor(Math.random() * 5)));
    var share3 = "share_3";
    var uid3 = 5007;
    var gid3 = 5007;
    data.push({
      share: share1,
      client: ipRandom1,
      uid: uid1,
      gid: gid1,
      num_read: 5 + Math.floor(Math.random() * 5),
      num_write: 1 + Math.floor(Math.random() * 5),
      num_lookup: 1 + Math.floor(Math.random() * 5),
      sum_read: Math.floor(Math.random() * 10),
      sum_write: Math.floor(Math.random() * 15),
    });
    data.push({
      share: share2,
      client: ipRandom2,
      uid: uid2,
      gid: gid2,
      num_read: 5 + Math.floor(Math.random() * 5),
      num_write: 1 + Math.floor(Math.random() * 5),
      num_lookup: 1 + Math.floor(Math.random() * 5),
      sum_read: Math.floor(Math.random() * 10),
      sum_write: Math.floor(Math.random() * 15),
    });
    data.push({
      share: share3,
      client: ipRandom3,
      uid: uid3,
      gid: gid3,
      num_read: 5 + Math.floor(Math.random() * 5),
      num_write: 1 + Math.floor(Math.random() * 5),
      num_lookup: 1 + Math.floor(Math.random() * 5),
      sum_read: Math.floor(Math.random() * 10),
      sum_write: Math.floor(Math.random() * 15),
    });
    return data;
  },


});

RockStorProbeMap.push({
  name: 'nfs-1',
  view: 'NfsView',
  description: 'All NFS calls',
});




