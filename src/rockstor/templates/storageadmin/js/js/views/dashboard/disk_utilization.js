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
    this.readsArray = {};
    this.begin = 100;
    this.dataLength = 5;
    this.refreshInterval = 1000;
    this.end = this.begin + this.dataLength-1;
    this.cols = ["reads_completed", "writes_completed", "sectors_read", 
    "sectors_written"];
    var _this = this;
    _.each(['sdb','sdc','sdd','sde'], function(d,i) {
      if (_.isUndefined(_this.readsArray[d])) {
        _this.readsArray[d] = [0,0,0,0,0,0,0,0,0,0];
      }
    });

    this.writesArray = [];
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
          return function() { 
            _this.getData(_this, _this.begin, _this.end); 
            _this.begin = _this.begin + _this.refreshInterval;
            _this.end = _this.begin + _this.dataLength;
          }
        }(), _this.refreshInterval);
        
      },
      error: function(request, response) {
          logger.debug('failed to fetch disks in disk_utilization');
      }
    });
    return this;
  },

  getData: function(context, t1, t2) {
    var _this = context;
    var rawData = [];
    for (i=0; i<t2-t1; i++) {
      rawData.push( {name: 'sdb', t: t1+i, reads_completed: Math.floor(200 + Math.random()*50), writes_completed: Math.floor(100 + Math.random()*50), sectors_read: 0, sectors_written: 0});
      rawData.push({name: 'sdc', t: t1+i, reads_completed: Math.floor(300 + Math.random()*50), writes_completed: Math.floor(200 + Math.random()*50), sectors_read: 0, sectors_written: 0});
      rawData.push({name: 'sdd', t: t1+i, reads_completed: Math.floor(50 + Math.random()*50), writes_completed: Math.floor(400 + Math.random()*50), sectors_read: 0, sectors_written: 0});
      rawData.push({name: 'sde', t: t1+i, reads_completed: Math.floor(10 + Math.random()*50), writes_completed: Math.floor(20 + Math.random()*50), sectors_read: 0, sectors_written: 0});
    }
    console.log(rawData); 
    var data = _this.formatData(rawData);
    console.log(data);

    // get data point of most recent timestamp 
    var data_current = [];
    var current_t = _this.timestamps[0];
    _.each(this.diskNames, function(name) {
      var x = data[name][current_t];
      var y = [];
      y.push(name);
      _.each(_this.cols, function(c) {
        y.push(x[c]);
      });
      console.log(y);
      data_current.push(y);
    });

    console.log(data_current);
    /*
    _.each(['sdb','sdc','sdd','sde'], function(d,i) {
      _this.readsArray[d].push(data[i].reads);
      if (_this.readsArray[d].length > 10) {
        _this.readsArray[d].splice(0,1);
      }
    });
    */
    if (!_this.created) {
      _this.createRows(data_current, _this); 
      _this.$("#disk-utilization-table").tablesorter();
    } else {
      _this.updateRows(data_current, _this); 
    }
    

  },
  
  createRows: function(data, _this) {
    var columns = ["name", "reads", "writes", "kbread", "kbwrite"];
    var rows = d3.select(this.el)
    .select("table#disk-utilization-table")
    .select("tbody")
    .selectAll("tr.data-utilization-row")
    .data(data, function(d) { return d[0] })
    .enter()
    .append("tr")
    .attr("class","data-utilization-row");
   
    var cells = rows.selectAll("td")
    .data(function(d) {
      return d;
    });

    cells.enter().append("td")
    .append("span")
    .attr("class", "graph");
   
    /*
    cells.select("span.graph")
    .each(function(d,i) {
      if (d.name == 'reads') {
        $(this).sparkline(_this.readsArray["sdb"], {composite: false, height: '1.3em', fillColor:false, lineColor:'black', tooltipPrefix: 'Index: '});
      }
    });
    */

    cells.append("span")
    .attr("class","value")
    .text(function(d) { return " " + d; });
   
    this.created = true;
    
  },

  updateRows: function(data, _this) {
    var columns = ["name", "reads", "writes", "kbread", "kbwrite"];
    var rows = d3.select(this.el)
    .select("table#disk-utilization-table")
    .select("tbody")
    .selectAll("tr.data-utilization-row")
    .data(data, function(d) { return d[0] });
   
    var cells = rows.selectAll("td")
    .data(function(d) { return d; });

    cells.select("span.value").text(function(d) { return " " + d });
   
    /*
    cells.select("span.graph")
    .each(function(d,i) {
      if (d.name == 'reads') {
        $(this).sparkline(_this.readsArray["sdb"], {composite: false, height: '1.3em', fillColor:false, lineColor:'black', tooltipPrefix: 'Index: '});
      }
    });
    */

    //cells.text(function(d) { return d.value });
    
  },

  cleanup: function() {
    if (!_.isNull(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  },

  // /api/probes/disk-stat/1/data/?t1=x&t2=y
  // gets data between timestamps t1 and t2
  //  { t: <timestamp>, name: <disk-name>, reads: <reads>, 
  // writes: <writes>,... }
  // for example, if t1=95 and t=100, and there are two disks, 
  // sdb and sdc
  // data is
  // [
  //   {name: 'sdb', t: 100, reads_completed: 500}, 
  //   {name: 'sdc', t: 100, reads_completed: 200} ,
  //   {name: 'sdb', t: 99, reads_completed: 490}, 
  //   {name: 'sdc', t: 99, reads_completed: 200},
  //   {name: 'sdb', t: 98, reads_completed: 490}, 
  //   {name: 'sdc', t: 98, reads_completed: 200},
  //   {name: 'sdb', t: 97, reads_completed: 490}, 
  //   {name: 'sdc', t: 97, reads_completed: 200},
  //   {name: 'sdb', t: 96, reads_completed: 490}, 
  //   {name: 'sdc', t: 96, reads_completed: 200},
  //   {name: 'sdb', t: 95, reads_completed: 490}, 
  //   {name: 'sdc', t: 95, reads_completed: 200},
  // ]
  //
  formatData: function(rawData) {
    var DATA_LEN_MAX = 600;
    var rows = [];
    var data = {};

    // get disknames and timestamps
    this.diskNames = [];
    this.timestamps = [];
    var _this = this;
    _.each(rawData, function(d) {
      if (!_.contains(_this.diskNames, d.name)) {
        _this.diskNames.push(d.name);
      }
      if (!_.contains(_this.timestamps, d.t)) {
        _this.timestamps.push(d.t);
      }
    });
    this.timestamps = _.sortBy(this.timestamps, function(ts) {
      return ts;
    }).reverse();
    console.log(this.diskNames);
    console.log(this.timestamps);
    // initialize everything to 0
    _.each(this.diskNames, function(name) {
      if (_.isUndefined(data[name])) {
        data[name] = {};
      }
      _.each(_this.timestamps, function(t) {
        if (_.isUndefined(data[name][t])) {
          data[name][t] = {};
          _.each(_this.cols, function(c) {
            data[name][t][c] = 0;
          });
        }
      });
    });
    _.each(rawData, function(d) {
      if (_.isUndefined(data[d.name])) {
        data[d.name] = {};
      }
      if (_.isUndefined(data[d.name][d.t])) {
        data[d.name][d.t] = {};
      }
      _.each(_this.cols, function(c) {
        data[d.name][d.t][c] = d[c];
      });
    });
    return data;

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


