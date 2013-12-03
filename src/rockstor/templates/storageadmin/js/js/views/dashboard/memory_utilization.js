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
    this.updateFreq = 1000;
    this.end = null;
    this.emptyData = {"id": 0, "total": 0, "free": 0, "buffers": 0, "cached": 0, "swap_total": 0, "swap_free": 0, "active": 0, "inactive": 0, "dirty": 0, "ts": "2013-07-17T00:00:16.109Z"};
    this.dataBuffer = [];
    this.dataLength = 300;
    this.currentTs = null;
    this.colors = ["#04BA44", "#C95351"];
    //for (i=0; i<this.dataLength; i++) {
    //  this.dataBuffer.push(emptyData);
    //}
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
        stack: true,
        //bars: { show: false, barWidth: 0.4, fillColor: {colors:[{opacity: 1},{opacity: 1}]}, align: "center" },
        lines: { show: true, fill: 0.8 },
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
    // Start and end timestamps for api call
    this.windowLength = 300000;
    this.t2 = RockStorGlobals.currentTimeOnServer.getTime()-30000;
    //this.t2 = new Date('2013-12-03T17:18:06.312Z').getTime();
    this.t1 = this.t2 - this.windowLength;
  },
  
  render: function() {
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName,
    }));
    var _this = this;
    var t1Str = moment(_this.t1).toISOString();
    var t2Str = moment(_this.t2).toISOString();
    var pageSizeStr = '&page_size=' + RockStorGlobals.maxPageSize;
    $.ajax({
      url: '/api/sm/sprobes/meminfo/?format=json' + pageSizeStr + '&t1=' +
        t1Str + '&t2=' + t2Str, 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        // fill dataBuffer
        _.each(data.results, function(d) {
          _this.dataBuffer.push(d);
        });
        //if (_this.dataBuffer.length > _this.dataLength) {
          //_this.dataBuffer.splice(0,
          //_this.dataBuffer.length - _this.dataLength);
        //}

        if (_this.dataBuffer.length > 0) { 
          while (new Date(_this.dataBuffer[0].ts).getTime() < _this.t2-(_this.windowLength )) {
            _this.dataBuffer.shift();
          }
        } 
        _this.getData(_this); 
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }

    });
    return this;
  },


  getData: function(context) {
    var _this = context;
    //var data = {"id": 7120, "total": 2055148, "free": 1524904, "buffers": 140224, "cached": 139152, "swap_total": 4128764, "swap_free": 4128764, "active": 324000, "inactive": 123260, "dirty": 56, "ts": "2013-07-17T00:00:16.109Z"};
    _this.startTime = new Date().getTime(); 
    var t1Str = moment(_this.t1).toISOString();
    var t2Str = moment(_this.t2).toISOString();
    _this.jqXhr = $.ajax({
      url: "/api/sm/sprobes/meminfo/?format=json&t1=" + 
        t1Str + "&t2=" + t2Str, 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        _.each(data.results, function(d) {
          _this.dataBuffer.push(d);
        });
        if (_this.dataBuffer.length > _this.dataLength) {
          _this.dataBuffer.splice(0,
          _this.dataBuffer.length - _this.dataLength);
        }
        
        // remove data outside window
        if (_this.dataBuffer.length > 0) {
          while (new Date(_this.dataBuffer[0].ts).getTime() < _this.t2 - _this.windowLength) {
            _this.dataBuffer.shift();
          }
        }
        _this.update(_this.dataBuffer);
        // Check time interval from beginning of last call
        // and call getData or setTimeout accordingly
        var currentTime = new Date().getTime();
        var diff = currentTime - _this.startTime;
        if (diff > _this.updateFreq) {
          if (_this.dataBuffer.length > 0) {
            _this.t1 = new Date(_this.dataBuffer[_this.dataBuffer.length-1].ts).getTime();
          } else {
            _this.t1 = _this.t1 + diff;
          }
          _this.t2 = _this.t2 + diff;
          _this.getData(_this); 
        } else {
          _this.timeoutId = window.setTimeout( function() { 
            if (_this.dataBuffer.length > 0) {
              _this.t1 = new Date(_this.dataBuffer[_this.dataBuffer.length-1].ts).getTime();
            } else {
              _this.t1 = _this.t1 + _this.updateFreq;
            }
            _this.t2 = _this.t2 + _this.updateFreq;
            _this.getData(_this); 
          }, _this.updateFreq - diff)
        }
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }

    });

  },

  update: function(dataBuffer) {
    var newData = this.modifyData(dataBuffer);
    this.$('#mem-util-chart').empty();
    this.graphOptions.xaxis = {
      mode: 'time',
      min: this.t2 - this.windowLength,
      max: this.t2,
      timezone: 'browser'
    }
    $.plot(this.$("#mem-util-chart"), newData, this.graphOptions);
    var currentData = this.emptyData; 
    if (this.dataBuffer.length > 0) {
      currentData = this.dataBuffer[this.dataBuffer.length-1];
    }
    // Memory
    this.$("#mem-total").html(humanize.filesize(currentData["total"]*1024));
    this.$("#mem-used").html(humanize.filesize((currentData["total"] - currentData["free"])*1024));  
    this.$("#mem-free").html(humanize.filesize(currentData["free"]*1024));
    // Swap
    this.$("#mem-totalswap").html(humanize.filesize(currentData["swap_total"]*1024));
    this.$("#mem-usedswap").html(humanize.filesize((currentData["swap_total"] - currentData["swap_free"])*1024));  
    this.$("#mem-freeswap").html(humanize.filesize(currentData["swap_free"]*1024));
  },

  // Creates series to be used by flot
  modifyData: function(dataBuffer) {
    var _this = this;
    var new_data = [];
    var free = [];
    var used = [];
    if (dataBuffer.length > 0) {
      this.totalMem = dataBuffer[dataBuffer.length-1].total;
      this.currentTs = dataBuffer[dataBuffer.length-1].ts;

      //this.graphOptions.yaxis = {
      // min: 0,
      //max: 100,
      //tickFormatter: this.memValueTickFormatter,
      //}
      _.each(dataBuffer, function(d,i) {
        free.push([(new Date(d.ts)).getTime(), (d["free"]/_this.totalMem)*100]);
        used.push([(new Date(d.ts)).getTime(), ((d["total"] - d["free"])/_this.totalMem)*100]);
      });
    }
  
    //new_data.push({"label": "free", "data": free, "color": this.colors[0]});
    new_data.push({"label": "used", "data": used, "color": this.colors[1]});
    return new_data;
  },

  download: function(event) {
    if (!_.isUndefined(event) && !_.isNull(event)) {
      event.preventDefault();
    }
    // calculate date 24hrs ago
    var t2Date = new Date(this.currentTs);
    var t1Date =  new Date(t2Date - 1000 * 60 * 60 * 24); // one day ago
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
    if (this.jqXhr) this.jqXhr.abort(); 
    if (this.timeoutId) window.clearTimeout(this.timeoutId);
  }

});

RockStorWidgets.widgetDefs.push({ 
    name: 'memory_utilization', 
    displayName: 'Memory', 
    view: 'MemoryUtilizationWidget',
    description: 'Display memory utilization',
    defaultWidget: true,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Compute', 
    position: 4
});

