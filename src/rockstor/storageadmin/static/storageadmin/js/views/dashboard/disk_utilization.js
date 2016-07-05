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
    RockStorSocket.diskWidget = io.connect('/disk-widget', {'secure': true,
                                                     'force new connection': true});
    var _this = this;
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_disk_utilization;
    this.diskUtilSelect = window.JST.dashboard_widgets_disk_util_select;
    this.dataLength = 300;
    this.topDiskColors = [];
    // calculate colors from dark to light for top disks
    var startColor = d3.rgb('#CC6104');
    for (var i=0; i<5; i++)  {
      this.topDiskColors.push(startColor.toString());
      startColor = startColor.brighter(2);
    }
    this.colors = ["#4DAF4A", "#377EB8"];
    // disks data is a map of diskname to array of values of length
    // dataLength
    // each value is of the format of the data returned by the api
    // see genEmptyDiskData for an example of this format
    this.disksData = {};
      this.disks = new DiskCollection();
      this.disks.pageSize = RockStorGlobals.maxPageSize;

    this.topDisks = [];
    this.topDisksWidth = this.maximized ? 520 : 240;
    this.topDisksHeight = 50;

    this.selectedDisk = null;

    this.updateFreq = 1000;
    this.sortAttrs = ['reads_completed']; // attrs to sort by
    this.numTop = 5; // maximum number of top disks to display
    this.partition = d3.layout.partition()
    .value(function(d) {
      return _.reduce(_this.sortAttrs, function(s, a) { return s + d[a]; }, 0);
    });
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
        max: this.dataLength-1,
        tickFormatter: this.timeTickFormatter(this.dataLength),
        axisLabel: "Time (minutes)",
        axisLabelColour: "#000"
      },
      yaxis: {
        min: 0
      },
      series: {
        lines: {show: true, fill: false},
        shadowSize: 0 // Drawing is faster without shadows
      }
    };
    this.dataGraphOptions = {
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
        max: this.dataLength-1,
        tickFormatter: this.timeTickFormatter(this.dataLength),
        axisLabel: "Time (minutes)",
        axisLabelColour: "#000"
      },
      yaxis: {
        min: 0,
        tickFormatter: this.valueTickFormatter
      },
      series: {
        lines: {show: true, fill: false},
        shadowSize: 0 // Drawing is faster without shadows
      }
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

    this.$('.diskSortAttr').change(function(event) {
      var cbox = $(event.currentTarget);
      var v = cbox.val();
      if (cbox.is(':checked')) {
        if (_.indexOf(_this.sortAttrs, v) == -1 ) {
          _this.sortAttrs.push(v);
        }
      } else {
        if (_.indexOf(_this.sortAttrs, v) != -1 ) {
          if (_this.sortAttrs.length > 1) {
            _this.sortAttrs = _.without(_this.sortAttrs, v);
          } else {
            // dont allow the last attr to be unchecked
            cbox.prop('checked', true);
          }
        }
      }
    });
    this.$('#top-disks-ph').css('width', this.topDisksWidth);
    this.topDisksPh = d3.select(this.el).select('#top-disks-ph');

    this.topDisksVis = this.topDisksPh
    .append('svg:svg')
    .attr('id', 'top-disks-svg')
    .attr('height', 75)
    .attr('width', this.topDisksWidth);

    this.disks.fetch({
      success: function(collection, response, options) {
        _this.initializeDisksData();
        RockStorSocket.addListener(_this.getData, _this, 'diskWidget:top_disks');
      }
    });
    return this;
  },

  // initialize disksData with disk names and empty value arrays
  initializeDisksData: function() {
    var _this = this;
    this.disks.each(function(disk) {
      var name = disk.get('name');
      var temp_name = disk.get('temp_name');
      _this.disksData[name] = [];
      for (var i=0; i<_this.dataLength; i++) {
        _this.disksData[name].push(_this.genEmptyDiskData());
      }
    });
    if (this.maximized) {
      // initialize disk-select
      this.$('#disk-details-ph').html(this.diskUtilSelect({
          disks: this.disks.toJSON()
      }));
      if (this.selectedDisk) {
        this.$('#disk-select').val(this.selectedDisk);
      }
      this.$('#disk-select').change(function(event) {
        _this.selectedDisk = _this.$('#disk-select').val();
      });
    } else {
      this.$('#disk-details-ph').html("<a href=\"#\" class=\"resize-widget\">Expand</a> for details");
    }
  },

  getData: function(data) {
    var _this = this;
    _this.startTime = new Date().getTime();
    _this.update(data);
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
    });
    _.each(_.keys(_this.disksData), function(diskName) {
      var diskData = _this.disksData[diskName];
      if (diskData.length > _this.dataLength) {
        diskData.splice(0, diskData.length - _this.dataLength);
      }
    });
  },

  // sorts latest values in disksData by sortAttrs and returns top n
  updateTopDisks: function() {
    var _this = this;
    var tmp = _.map(_.keys(_this.disksData), function(k) {
      return _this.disksData[k][_this.dataLength - 1];
    });
    tmp = _.reject(tmp, function(d) {
      var x = _.reduce(_this.sortAttrs, function(s, a) { return s + d[a]; }, 0);
      return x == 0;
    });
    var sorted = _.sortBy(tmp, function(d) {
      return _.reduce(_this.sortAttrs, function(s, a) { return s + d[a]; }, 0);
    }).reverse();
    this.topDisks = sorted.slice(0,_this.numTop);
  },

  // render bars for top disks. the width of each bar is proportional
  // to the sort value. Use d3 partition layout to calculate coordinates.
  renderTopDisks: function() {
    var _this = this;
    var w = this.topDisksWidth;
    var h = this.topDisksHeight;
    // calculate total value of all sortAttrs over all disks
    var totalAttr = _.reduce(this.topDisks, function(total, disk) {
      return total + _.reduce(_this.sortAttrs, function(s, a) {
        return s + disk[a];
      }, 0);
    }, 0);
    this.$('#attr-total').html(totalAttr);

    if (this.topDisks.length == 0) {
      if (!this.noDisks) {
        this.$('#top-disks-svg').empty();
        this.topDisksVis.append('g')
        .append('svg:text')
        .attr("transform", function(d) {
          return 'translate(0,' + 32 + ')';
        })
        .text('No disk activity')
        .attr('fill-opacity', 1.0);
        this.noDisks = true;
      }
    } else {
      if (this.noDisks) {
        // clear no disk activity msg
        this.$('#top-disks-svg').empty();
      }
      this.noDisks = false;
      var root = {name: 'root',
        reads_completed: 0,
        writes_completed: 0,
        children: this.topDisks
      };
      var x = d3.scale.linear().range([0, w]);
      var y = d3.scale.linear().range([0, h]);
      var diskNodes = this.partition.nodes(root);
      var kx = w / root.dx, ky = h / 1;
      var duration = 200;

      var disk = this.topDisksVis.selectAll('g')
      .data(diskNodes, function(d, i) { return d.name; });

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
      .attr('fill', function(d,i) { return _this.topDiskColors[i-1]; });

      diskEnter.append("svg:text")
      .attr('class', 'diskText')
      .attr("transform", function(d) {
        return 'translate(0,' + 32 + ')';
      })
      .text(function(d) {
        if (d.name == 'root') {
          return '';
        } else {
          return d.name.split('_').pop();
        }
      })
      .attr('fill-opacity', 1.0);

      var diskUpdate = disk.transition()
      .duration(duration)
      .attr('transform', function(d) {
        return 'translate(' + x(d.x) + ',' + y(d.y) + ')';
      });

      var diskRectUpdate = diskUpdate.select('rect.diskRect')
      .attr('width', function(d) { return (d.dx * w) - 1; })
      .attr('fill', function(d,i) { return _this.topDiskColors[i-1]; });

      var diskExit = disk.exit().remove();
    }
  },

  renderDiskGraph: function() {
    if (!this.selectedDisk) {
      if (this.topDisks.length > 0) {
        this.selectedDisk = this.topDisks[0].name;
      } else {
        this.selectedDisk = this.disks.at(0).get('name');
      }
      this.$('#disk-select').val(this.selectedDisk);
    }

    var vals = this.disksData[this.selectedDisk];
    var tmpReads = [];
    for (var i=0; i<this.dataLength; i++) {
      tmpReads.push([i, vals[i].reads_completed]);
    }
    var tmpWrites = [];
    for (var i=0; i<this.dataLength; i++) {
      tmpWrites.push([i, vals[i].writes_completed]);
    }
    var series1 = [
      { label: 'Reads', data: tmpReads, color: this.colors[0] },
      { label: 'Writes', data: tmpWrites, color: this.colors[1] }
    ];
    $.plot(this.$('#disk-graph-reads-ph'), series1, this.graphOptions);

    var tmpReadData = [];
    for (var i=0; i<this.dataLength; i++) {
      tmpReadData.push([i, vals[i].sectors_read * 512]);
    }
    var tmpWriteData = [];
    for (var i=0; i<this.dataLength; i++) {
      tmpWriteData.push([i, vals[i].sectors_written * 512]);
    }
    var series2 = [
      { label: 'KB read', data: tmpReadData, color: this.colors[0] },
      { label: 'KB written', data: tmpWriteData, color: this.colors[1] }
    ];
    $.plot(this.$('#disk-graph-data-ph'), series2, this.dataGraphOptions);
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
    };
  },

  resize: function(event) {
    var _this = this;
    this.constructor.__super__.resize.apply(this, arguments);
    this.topDisksWidth = this.maximized ? 520 : 240;
    //this.$('#top-disks-ph').empty();
    this.$('#top-disks-ph').css('width', this.topDisksWidth);
    this.topDisksVis.attr('width', this.topDisksWidth);
    this.renderTopDisks();
    if (this.maximized) {
      this.$('#disk-details-ph').html(this.diskUtilSelect({
          disks: this.disks.toJSON()
      }));
      if (this.selectedDisk) {
        this.$('#disk-select').val(this.selectedDisk);
      }
      this.$('#disk-select').change(function(event) {
        _this.selectedDisk = _this.$('#disk-select').val();
      });
    } else {
      this.$('#disk-details-ph').html("<a href=\"#\" class=\"resize-widget\">Expand</a> for details");
    }
  },

  timeTickFormatter: function(dataLength) {
    return function(val, axis) {
      return ((dataLength/60) - (parseInt(val/60))).toString() + ' m';
    };
  },

  valueTickFormatter: function(val, axis) {
    return humanize.filesize(val, 1024, 2);
  },

  setSelectedDisk: function(event) {
    this.selectedDisk = this.$('#disk-select').val();
  },

  cleanup: function() {
    RockStorSocket.removeOneListener('diskWidget');
  }

});

RockStorWidgets.widgetDefs.push({
    name: 'disk_utilization',
    displayName: 'Disk Activity',
    view: 'DiskUtilizationWidget',
    description: 'Display disk activity',
    defaultWidget: true,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage',
    position: 1
});
