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


MemoryUtilizationWidget = RockStorWidgetView.extend({
  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_memory_utilization;
    this.begin = null;
    this.refreshInterval = 1000;
    this.end = null;
    var emptyData = {"id": 0, "total": 0, "free": 0, "buffers": 0, "cached": 0, "swap_total": 0, "swap_free": 0, "active": 0, "inactive": 0, "dirty": 0, "ts": "2013-07-17T00:00:16.109Z"};
    this.dataBuffer = [];
    this.dataLength = 60;
    for (i=0; i<this.dataLength; i++) {
      this.dataBuffer.push(emptyData);
    }
    this.totalMem = 0;
    this.graphOptions = { 
      grid : { 
        hoverable : true,
        borderWidth: {
          top: 1,
          right: 1,
          bottom: 0,
          left: 0
        },
        borderColor: "#aaa"
      },
      xaxis: {
        min: 0,
        max: this.dataLength,
        tickFormatter: this.memTimeTickFormatter(this.dataLength)
      },
			series: {
        //stack: false,
        //bars: { show: false, barWidth: 0.4, fillColor: {colors:[{opacity: 1},{opacity: 1}]}, align: "center" },
        lines: { show: true, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
      legend : { container : "#legends", noColumns : 3 },
      tooltip: true,
      tooltipOpts: {
        content: "%s (%y)" 
      }
    };
  },
  
  render: function() {
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName,
    }));
    var _this = this;
    this.intervalId = window.setInterval(function() {
      return function() { 
        _this.getData(_this, _this.begin, _this.end); 
        _this.begin = _this.end;
        _this.end = _this.begin + _this.refreshInterval;
      }
    }(), _this.refreshInterval);
    return this;
  },


  getData: function(context, t1, t2) {
    var _this = context;
    var data = {"id": 7120, "total": 2055148, "free": 1524904, "buffers": 140224, "cached": 139152, "swap_total": 4128764, "swap_free": 4128764, "active": 324000, "inactive": 123260, "dirty": 56, "ts": "2013-07-17T00:00:16.109Z"};
    _this.dataBuffer.push(data);
    if (_this.dataBuffer.length > _this.dataLength) {
      _this.dataBuffer.splice(0,1);
    }
    _this.update(_this.dataBuffer);

  },

  update: function(dataBuffer) {
    var new_data = this.modifyData(dataBuffer);
    $.plot(this.$("#mem-util-chart"), new_data, this.graphOptions);
  },

  // Creates series to be used by flot
  modifyData: function(dataBuffer) {
    var new_data = [];
    var free = [];
    var used = [];
    this.totalMem = dataBuffer[dataBuffer.length-1].total;
    console.log(this.totalMem);
    this.graphOptions.yaxis = {
      min: 0,
      max: this.totalMem,
      tickFormatter: this.memValueTickFormatter,
    }
    _.each(dataBuffer, function(d,i) {
      free.push([i, d["free"]]);
      used.push([i, d["total"] - d["free"]]);
    });
  
    new_data.push({"label": "free", "data": free});
    new_data.push({"label": "used", "data": used});
    return new_data;
  },

  memValueTickFormatter: function(val, axis) {
    return humanize.filesize(val, 1024, 1); 
  },

  memTimeTickFormatter: function(dataLength) {
    return function(val, axis) {
      return dataLength - val;
    };
  },

  tooltipFormatter: function(label, xval, yval) {
    return "%s (%p.2%)"
    //return "%s (" + humanize.filesize(xval, 1024, 1) + ")"; 
  }

});

RockStorWidgets.available_widgets.push({ 
    name: 'memory_utilization', 
    displayName: 'Memory Utilization', 
    view: 'MemoryUtilizationWidget',
    description: 'Display memory utilization',
    defaultWidget: false,
    rows: 1,
    cols: 2,
    category: 'Compute', 
});

