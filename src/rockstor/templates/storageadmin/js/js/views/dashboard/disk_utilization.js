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
    this.numSamples = 60;
    // disks data is a map of diskname to array of values of length 
    // numSamples
    // each value is of the format of the data returned by the api
    // see genEmptyDiskData for an example of this format
    this.disksData = {};
    this.disks = new DiskCollection();
    this.topDisks = [];
    this.updateInterval = 1000;
    this.sortAttrs = ['reads_completed']; // attrs to sort by
    this.numTop = 5; // no of top shares
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
    var disks = ['sdb','sdc','sdd','sde'];
    //this.disks.each(function(disk) {
    _.each(disks, function(disk) {
      //var name = disk.get('name');
      var name = disk;
      _this.disksData[name] = [];
      for (var i=0; i<_this.numSamples; i++) {
        _this.disksData[name].push(_this.genEmptyDiskData());
      }
    });
  },

  startLoop: function() {
    var _this = this;
    this.intervalId = window.setTimeout(function() {
      return function() { _this.getData(_this); }
    }(), this.updateInterval)
  },

  getData: function(context, t1, t2) {
    var _this = context;
    //$.ajax({
      //url: "/api/sm/sprobes/diskstat/?group=name&limit=1", 
      //type: "GET",
      //dataType: "json",
      //global: false, // dont show global loading indicator
      //success: function(data, status, xhr) {
        //_this.update(data.results);
      //},
      //error: function(xhr, status, error) {
        //console.log(error);
      //}
    //});
  
    this.update(this.genRandomDisksData());
  },

  update: function(data) {
    this.updateDisksData(data);
    this.updateTopDisks();
    this.renderTopDisks();

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
    var sorted = _.sortBy(tmp, function(d) {
      return _.reduce(_this.sortAttrs, function(s, a) { return s + d[a]; }, 0); 
    }).reverse();
    this.topDisks = sorted.slice(0,_this.numTop);
    
  },

  renderTopDisks: function() {
    
    var root = {name: 'root', reads_completed: 0, children: this.topDisks};
    var partition = d3.layout.partition()
    .value(function(d) { return d.reads_completed; });
    var w = 200;
    var h = 50;
    var x = d3.scale.linear().range([0, w]);
    var y = d3.scale.linear().range([0, h]);
    
    var vis = d3.select(this.el).select('#top-disks-ph')
    .append('svg:svg')
    .attr('height', h)
    .attr('width', w);
    
    var g = vis.selectAll('g')
    .data(partition.nodes(root))
    .enter().append('svg:g')
    .attr('transform', function(d) {
      return 'translate(' + x(d.x) + ',' + y(d.y) + ')'; 
    });
    
    var kx = w / root.dx, ky = h / 1;

    g.append('svg:rect')
    .attr('width', function(d) { return d.dx * w; })
    .attr('height', function(d) { 
      if (d.name == 'root') { 
        return 0;
      } else {
        return 25;
      }
    })
    .attr('fill', 'steelblue');

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
        "reads_completed": 10, 
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
        "reads_completed": 20, 
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
        "reads_completed": 5, 
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
        "reads_completed": 7, 
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

  cleanup: function() {
    if (!_.isNull(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  },

});

RockStorWidgets.widgetDefs.push({ 
    name: 'disk_utilization', 
    displayName: 'Disk Usage', 
    view: 'DiskUtilizationWidget',
    description: 'Display disk utilization',
    defaultWidget: false,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage', 
});


