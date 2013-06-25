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
    this.displayName = this.options.displayName;
    this.disks = new DiskCollection();
    this.created = false;
    this.intervalId = null;
  },

  render: function() {
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    var _this = this;
    this.disks.fetch({
      success: function(request) {
        $(_this.el).html(_this.template({ 
          module_name: _this.module_name,
          displayName: _this.displayName,
          disks: _this.disks
        }));
        _this.intervalId = window.setInterval(function() {
          return function() { _this.getData(_this); }
        }(), 2000)
      },
      error: function(request, response) {
          logger.debug('failed to fetch disks in disk_utilization');
      }
    });
    return this;
  },

  getData: function(context) {
    var _this = context;
    var data = [
      {name: 'sdb', reads: Math.floor(200 + Math.random()*50), writes: Math.floor(100 + Math.random()*50)},
      {name: 'sdc', reads: Math.floor(300 + Math.random()*50), writes: Math.floor(200 + Math.random()*50)},
      {name: 'sdd', reads: Math.floor(50 + Math.random()*50), writes: Math.floor(400 + Math.random()*50)},
      {name: 'sde', reads: Math.floor(10 + Math.random()*50), writes: Math.floor(20 + Math.random()*50)},
    ];
    if (!_this.created) {
      _this.createRows(data); 
      _this.$("#disk-utilization-table").tablesorter();
    } else {
      _this.updateRows(data); 
    }

  },
  
  createRows: function(data) {
    var columns = ["name", "reads", "writes"];
    var rows = d3.select(this.el)
    .select("table#disk-utilization-table")
    .select("tbody")
    .selectAll("tr.data-utilization-row")
    .data(data, function(d) { return d.name })
    .enter()
    .append("tr")
    .attr("class","data-utilization-row");
   
    var cells = rows.selectAll("td")
    .data(function(row) {
      return _.map(columns, function(c) {
        return {name: c, value: row[c]}
      });
    }, function(d) { return d.name; })
    .enter()
    .append("td")
    .text(function(d) { return d.value });
   
    this.created = true;
    
  },

  updateRows: function(data) {
    var columns = ["name", "reads", "writes"];
    var rows = d3.select(this.el)
    .select("table#disk-utilization-table")
    .select("tbody")
    .selectAll("tr.data-utilization-row")
    .data(data, function(d) { return d.name });
   
    var cells = rows.selectAll("td")
    .data(function(row) {
      return _.map(columns, function(c) {
        return {name: c, value: row[c]}
      });
    }, function(d) { return d.name; })
    .text(function(d) { return d.value });
    
  },

  cleanup: function() {
    if (!_.isNull(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  }

});

RockStorWidgets.available_widgets.push({ 
    name: 'disk_utilization', 
    displayName: 'Disk Utilization', 
    view: 'DiskUtilizationWidget',
    description: 'Display disk utilization',
    defaultWidget: false,
    rows: 1,
    cols: 2,
    category: 'Storage', 
});


