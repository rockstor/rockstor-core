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


DiskUtilizationWidget = RockStorWidgetView.extend({

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_disk_utilization;
    this.diskUtilSelect = window.JST.dashboard_widgets_disk_util_select;
    this.numSamples = 600;
    this.colors = ["#E41A1C", "#377EB8", "#4DAF4A", "#FFFFFF"];
    // disks data is a map of diskname to array of values of length 
    // numSamples
    // each value is of the format of the data returned by the api
    // see genEmptyDiskData for an example of this format
    this.disksData = {};
    this.disks = new DiskCollection();
    
    this.topDisks = [];
    this.topDisksWidth = this.maximized ? 400 : 200;
    this.topDisksHeight = 50;

    this.updateInterval = 1000;
    this.sortAttrs = ['reads_completed', 'writes_completed']; // attrs to sort by
    this.numTop = 5; // no of top shares
    this.partition = d3.layout.partition()
    .value(function(d) { return d.reads_completed; });
    this.graphOptions = { 
      grid : { 
        //hoverable : true,
        borderWidth: {
          top: 1,
          right: 1,
          bottom: 1,
          left: 1
        },
        borderColor: "#ddd"
      },
      xaxis: {
        min: 0,
        max: this.numSamples-1,
        axisLabel: "Time (minutes)",
        axisLabelColour: "#000"
      },
      yaxis: { 
        min: 0, 
      },
			series: {
        lines: { show: true, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
    };
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
    this.$('#top-disks-ph').css('width', this.topDisksWidth);
    this.topDisksPh = d3.select(this.el).select('#top-disks-ph');
    
    this.topDisksVis = this.topDisksPh 
    .append('svg:svg')
    .attr('height', 75)
    .attr('width', this.topDisksWidth);
    
    this.disks.fetch({
      success: function(collection, response, options) {
        _this.initializeDisksData();
        _this.startLoop();
      }
    });
    return this;
  },
  
  // initialize disksData with disk names and empty value arrays
  initializeDisksData: function() {
    var _this = this;
    // TODO remove after test
    //var disks = ['sdb','sdc','sdd','sde'];
    this.disks.each(function(disk) {
    //_.each(disks, function(disk) {
      var name = disk.get('name');
      //var name = disk;
      _this.disksData[name] = [];
      for (var i=0; i<_this.numSamples; i++) {
        _this.disksData[name].push(_this.genEmptyDiskData());
      }
    });
    if (this.maximized) {
      // initialize disk-select
      this.$('#disk-select-ph').html(this.diskUtilSelect({
        disks: this.disks
      }));
    }
  },

  startLoop: function() {
    var _this = this;
    this.intervalId = window.setInterval(function() {
      return function() { _this.getData(_this); }
    }(), this.updateInterval)
  },

  getData: function(context, t1, t2) {
    var _this = context;
    $.ajax({
      url: "/api/sm/sprobes/diskstat/?group=name&limit=1", 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        _this.update(data.results);
      },
      error: function(xhr, status, error) {
        console.log(error);
      }
    });
  
    //this.update(this.genRandomDisksData());
  },

  update: function(data) {
    this.updateDisksData(data);
    this.updateTopDisks();
    this.renderTopDisks();
    if (this.maximized) this.renderDiskGraph();
  },

  updateDisksData: function(data) {
    var _this = this;
    _.each(data, function(d) {
      _this.disksData[d.name].push(d);
      _this.disksData[d.name].splice(0,1);
    });
  },

  // sorts latest values in disksData by sortAttrs and returns top n
  updateTopDisks: function() {
    var _this = this;
    var tmp = _.map(_.keys(_this.disksData), function(k) {
      return _this.disksData[k][_this.numSamples - 1];
    });
    tmp = _.reject(tmp, function(d) {
      var x = _.reduce(_this.sortAttrs, function(s, a) { return s + d[a]; }, 0); 
      return x == 0;
    });
    var sorted = _.sortBy(tmp, function(d) {
      return _.reduce(_this.sortAttrs, function(s, a) { return s + d[a]; }, 0); 
    }).reverse();
    this.topDisks = sorted.slice(0,_this.numTop);
    console.log(this.topDisks);
  },

  // render bars for top disks. the width of each bar is proportional
  // to the sort value. Use d3 partition layout to calculate coordinates.
  renderTopDisks: function() {
    var w = this.topDisksWidth;
    var h = this.topDisksHeight;
    if (this.topDisks.length == 0) {
      this.$('#top-disks-ph').html('<h4>No disk activity</h4>');
    } else { 
      var root = {name: 'root', reads_completed: 0, children: this.topDisks};
      var x = d3.scale.linear().range([0, w]);
      var y = d3.scale.linear().range([0, h]);
      var diskNodes = this.partition.nodes(root);
      var kx = w / root.dx, ky = h / 1;
      var duration = 1000;

      var disk = this.topDisksVis.selectAll('g')
      .data(diskNodes, function(d) { return d.name; });

      // Create g elements - each g element is positioned at appropriate
      // x coordinate, and contains a rect with width acc to disk sort value,
      // and a text element with the disk name 
      var diskEnter = disk
      .enter().append('svg:g');

      diskEnter.append('svg:rect')
      .attr('class', 'diskRect')
      .attr('height', function(d) { 
        if (d.name == 'root') { 
          return 0;
        } else {
          return 25;
        }
      })
      .attr('fill', 'steelblue');

      diskEnter.append("svg:text")
      .attr('class', 'diskText')
      .attr("transform", function(d) {
        return 'translate(0,' + 32 + ')'; 
      })
      .text(function(d) { 
        if (d.name == 'root') {
          return '';
        } else {
          return d.name; 
        }
      })
      .attr('fill-opacity', 1.0);

      var diskUpdate = disk.transition() 
      .duration(duration)
      .attr('transform', function(d) {
        return 'translate(' + x(d.x) + ',' + y(d.y) + ')'; 
      });

      var diskRectUpdate = diskUpdate.select('rect.diskRect')
      .attr('width', function(d) { return (d.dx * w) - 1; });

      var diskExit = disk.exit().remove();
    }    
  },

  renderDiskGraph: function() {
    if (this.topDisks.length > 0) {
      var name = this.topDisks[0].name;
    } else {
      var name = this.disks.at(0).get('name');
    }
    this.$('#disk-select').val(name);

    var vals = this.disksData[name];
    var tmpReads = [];
    for (var i=0; i<this.numSamples; i++) {
      tmpReads.push([i, vals[i].reads_completed]);
    }
    var tmpWrites = [];
    for (var i=0; i<this.numSamples; i++) {
      tmpWrites.push([i, vals[i].writes_completed]);
    }
    var series = [
      { label: 'Reads', data: tmpReads, color: this.colors[0] },
      { label: 'Writes', data: tmpWrites, color: this.colors[1] }
    ];
    $.plot(this.$('#disk-graph-ph'), series, this.graphOptions);
  },

  genEmptyDiskData: function() {
    // empty disk data
    return {
      "reads_completed": 0, 
      "reads_merged": 0, 
      "sectors_read": 0, 
      "ms_reading": 0, 
      "writes_completed": 0, 
      "writes_merged": 0, 
      "sectors_written": 0, 
      "ms_writing": 0, 
      "ios_progress": 0, 
      "ms_ios": 0, 
      "weighted_ios": 0, 
      "ts": 0
    }
  },

  genRandomDisksData: function() {
    return [
      {
        'name': 'sdb',
        "reads_completed": 10 + parseInt(Math.random()*10), 
        "reads_merged": 0, 
        "sectors_read": 0, 
        "ms_reading": 0, 
        "writes_completed": 0, 
        "writes_merged": 0, 
        "sectors_written": 0, 
        "ms_writing": 0, 
        "ios_progress": 0, 
        "ms_ios": 0, 
        "weighted_ios": 0, 
        "ts": 0
      },
      {
        'name': 'sdc',
        "reads_completed": 20 + parseInt(Math.random()*10), 
        "reads_merged": 0, 
        "sectors_read": 0, 
        "ms_reading": 0, 
        "writes_completed": 0, 
        "writes_merged": 0, 
        "sectors_written": 0, 
        "ms_writing": 0, 
        "ios_progress": 0, 
        "ms_ios": 0, 
        "weighted_ios": 0, 
        "ts": 0
      },
      {
        'name': 'sdd',
        "reads_completed": 5 + parseInt(Math.random()*5), 
        "reads_merged": 0, 
        "sectors_read": 0, 
        "ms_reading": 0, 
        "writes_completed": 0, 
        "writes_merged": 0, 
        "sectors_written": 0, 
        "ms_writing": 0, 
        "ios_progress": 0, 
        "ms_ios": 0, 
        "weighted_ios": 0, 
        "ts": 0
      },
      {
        'name': 'sde',
        "reads_completed": 7 + parseInt(Math.random()*5), 
        "reads_merged": 0, 
        "sectors_read": 0, 
        "ms_reading": 0, 
        "writes_completed": 0, 
        "writes_merged": 0, 
        "sectors_written": 0, 
        "ms_writing": 0, 
        "ios_progress": 0, 
        "ms_ios": 0, 
        "weighted_ios": 0, 
        "ts": 0
      }
    ];


  },
  
  resize: function(event) {
    this.constructor.__super__.resize.apply(this, arguments);
    this.topDisksWidth = this.maximized ? 400 : 200;
    //this.$('#top-disks-ph').empty();
    this.$('#top-disks-ph').css('width', this.topDisksWidth);
    this.topDisksVis.attr('width', this.topDisksWidth);
    this.renderTopDisks();
    if (this.maximized) {
      this.$('#disk-select-ph').html(this.diskUtilSelect({
        disks: this.disks
      }));
    } else {
      this.$('#disk-select-ph').empty();
    }
  },

  cleanup: function() {
    if (!_.isNull(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  },

});

RockStorWidgets.widgetDefs.push({ 
    name: 'disk_utilization', 
    displayName: 'Disk Activity', 
    view: 'DiskUtilizationWidget',
    description: 'Display disk activity',
    defaultWidget: false,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage', 
});


