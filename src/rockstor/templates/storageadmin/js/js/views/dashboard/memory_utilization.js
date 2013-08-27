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
    this.dataLength = 300;
    this.currentTs = null;
    this.colors = ["#04BA44", "#C95351"];
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
        tickSize: 60,
        tickFormatter: this.memTimeTickFormatter(this.dataLength)
      },
      yaxis: {
        min: 0,
        max: 100,
        tickSize: 20,
        tickFormatter: this.memValueTickFormatter,
      },
			series: {
        //stack: false,
        //bars: { show: false, barWidth: 0.4, fillColor: {colors:[{opacity: 1},{opacity: 1}]}, align: "center" },
        lines: { show: true, fill: 0.5 },
        shadowSize: 0	// Drawing is faster without shadows
			},
      legend : { 
        container: "#mem-legend", 
        noColumns: 1,
        margin: [10,0],
        labelBoxBorderColor: "#fff"

      },
      tooltip: true,
      tooltipOpts: {
        content: "%s (%y.2%)" 
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
    $.ajax({
      url: "/api/sm/sprobes/meminfo/?limit=" + this.dataLength + "&format=json", 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        // fill dataBuffer
        _.each(data.results, function(d) {
          _this.dataBuffer.push(d);
        });
        if (_this.dataBuffer.length > _this.dataLength) {
          _this.dataBuffer.splice(0,
          _this.dataBuffer.length - _this.dataLength);
        }
        this.intervalId = window.setInterval(function() {
          return function() { 
            _this.getData(_this, _this.begin, _this.end); 
            _this.begin = _this.end;
            _this.end = _this.begin + _this.refreshInterval;
          }
        }(), _this.refreshInterval);
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }

    });
    return this;
  },


  getData: function(context, t1, t2) {
    var _this = context;
    //var data = {"id": 7120, "total": 2055148, "free": 1524904, "buffers": 140224, "cached": 139152, "swap_total": 4128764, "swap_free": 4128764, "active": 324000, "inactive": 123260, "dirty": 56, "ts": "2013-07-17T00:00:16.109Z"};
    $.ajax({
      url: "/api/sm/sprobes/meminfo/?limit=1&format=json", 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        _this.dataBuffer.push(data.results[0]);
        if (_this.dataBuffer.length > _this.dataLength) {
          _this.dataBuffer.splice(0,1);
        }
        _this.update(_this.dataBuffer);
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }

    });

  },

  update: function(dataBuffer) {
    var newData = this.modifyData(dataBuffer);
    $.plot(this.$("#mem-util-chart"), newData, this.graphOptions);
    var currentData = this.dataBuffer[this.dataBuffer.length-1];
    // Memory
    this.$("#mem-total").html(humanize.filesize(currentData["total"]*1024));
    this.$("#mem-used").html(humanize.filesize((currentData["total"] - currentData["free"])*1024));  
    this.$("#mem-free").html(humanize.filesize(currentData["free"]*1024));
    // Swap
    this.$("#mem-totalswap").html(humanize.filesize(
    currentData["swap_total"]*1024));
    this.$("#mem-usedswap").html(humanize.filesize(
      (currentData["swap_total"] - currentData["swap_free"])*1024));  
    this.$("#mem-freeswap").html(humanize.filesize(
    currentData["swap_free"]*1024));
  },

  // Creates series to be used by flot
  modifyData: function(dataBuffer) {
    var _this = this;
    var new_data = [];
    var free = [];
    var used = [];
    this.totalMem = dataBuffer[dataBuffer.length-1].total;
    this.currentTs = dataBuffer[dataBuffer.length-1].ts;

    //this.graphOptions.yaxis = {
     // min: 0,
      //max: 100,
      //tickFormatter: this.memValueTickFormatter,
    //}
    _.each(dataBuffer, function(d,i) {
      free.push([i, (d["free"]/_this.totalMem)*100]);
      used.push([i, ((d["total"] - d["free"])/_this.totalMem)*100]);
    });
  
    new_data.push({"label": "free", "data": free, "color": this.colors[0]});
    new_data.push({"label": "used", "data": used, "color": this.colors[1]});
    return new_data;
  },

  download: function(event) {
    if (!_.isUndefined(event) && !_.isNull(event)) {
      event.preventDefault();
    }
    // calculate date 24hrs ago
    console.log(this.currentTs);
    var t2Date = new Date(this.currentTs);
    var t1Date =  new Date(t2Date - 1000 * 60 * 60 * 24); // one day ago
    console.log(t2Date);
    console.log(t1Date);
    var t2 = t2Date.toISOString();
    var t1 = t1Date.toISOString();
    document.location.href = "/api/sm/sprobes/meminfo/?t1="+t1+"&t2="+t2+"&download=true";
  },

  memValueTickFormatter: function(val, axis) {
    return val + "%";
  },

  memTimeTickFormatter: function(dataLength) {
    return function(val, axis) {
      return (dataLength/60) - (parseInt(val/60)).toString() + ' m';
      //return dataLength - val;
    };
  },

  tooltipFormatter: function(label, xval, yval) {
    return "%s (%p.2%)"
    //return "%s (" + humanize.filesize(xval, 1024, 1) + ")"; 
  },
  
  cleanup: function() {
    logger.debug('clearing setInterval in memory_utilization widget'); 
    if (!_.isUndefined(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  }

});

RockStorWidgets.available_widgets.push({ 
    name: 'memory_utilization', 
    displayName: 'Memory Utilization', 
    view: 'MemoryUtilizationWidget',
    description: 'Display memory utilization',
    defaultWidget: true,
    rows: 1,
    cols: 2,
    category: 'Compute', 
    position: 2
});

