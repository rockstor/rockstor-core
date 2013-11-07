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


NetworkUtilizationWidget = RockStorWidgetView.extend({

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_network_utilization;
    this.valuesTemplate = window.JST.dashboard_widgets_network_util_values;
    this.updateFreq = 1000;
    this.dataBuffers = {};
    this.dataLength = 300;
    this.currentTs = null;
    this.networkInterfaces = new NetworkInterfaceCollection();
    this.networkInterfaces.on("reset", this.getInitialData, this);
    this.selectedInterface = null;
    this.colors = ["#1224E3", "#F25805", "#04D6D6", "#F5CC73", "#750413"];
    this.totalMem = 0;
    this.graphOptions = { 
      grid : { 
        //hoverable : true,
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
        tickFormatter: this.timeTickFormatter(this.dataLength),
        axisLabel: "Time (minutes)",
        axisLabelColour: "#000"
      },
      yaxes: [ 
        { 
          min: 0, 
          tickFormatter: this.valueTickFormatter,
          axisLabel: "Data",
          axisLabelColour: "#000",
          axisLabelPadding: 0,
        }, 
        { 
          position: "right", 
          min: 0,
          axisLabel: "Packets",
          axisLabelColour: "#000",
          axisLabelPadding: 0,
        } 
      ],
			series: {
        lines: { show: true, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
      legend : { 
        container: "#network-util-legend", 
        noColumns: 2,
        margin: [30,0],
        labelBoxBorderColor: "#fff"

      },
    };
    
    // Start and end timestamps for api call
    this.windowLength = 10000;
    this.t2 = RockStorGlobals.currentTimeOnServer.getTime()-30000;
    this.t1 = this.t2 - this.windowLength;
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
    if (this.maximized) {
      this.$('#network-util-values-ph').html(this.valuesTemplate());
    }
    this.$("#interface-select").change(function(event) {
      _this.selectedInterface = $(event.currentTarget).val();
    });
    this.networkInterfaces.fetch();
    return this;
  },

  getInitialData: function() {
    var _this = this;
    var niselect = this.$("#interface-select");
    this.networkInterfaces.each(function(ni,i) {
      var opt = $("<option/>");
      opt.val(ni.get("name"));
      opt.text(ni.get("name"));
      if (i==0) {
        opt.attr({selected:"selected"});
      }
      niselect.append(opt);
    });
    this.selectedInterface = this.networkInterfaces.at(0).get("name");
    var t1Str = moment(_this.t1).toISOString();
    var t2Str = moment(_this.t2).toISOString();
    this.jqXhr = $.ajax({
      url: "/api/sm/sprobes/netstat/?format=json&t1=" +
        t1Str + "&t2=" + t2Str, 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        // fill dataBuffers
        console.log(data.results); 
        _this.networkInterfaces.each(function(ni) {
          var tmp = [];
          for (var i=0; i<_this.dataLength; i++) {
            tmp.push(_this.genEmptyData());
          }
          _this.dataBuffers[ni.get("name")] = tmp;
        });
        _.each(data.results, function(d) {
          _this.dataBuffers[d.device].push(d);
        });
        _.each(_.keys(_this.dataBuffers), function(device) {
          var dataBuffer = _this.dataBuffers[device];
          if (dataBuffer.length > _this.dataLength) {
            dataBuffer.splice(0, dataBuffer.length - _this.dataLength);
          }
        });
        console.log(_this.dataBuffers); 
        _this.getData(_this); 
         
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }

    });

  },

  getData: function(context, t1, t2) {
    var _this = context;
    //var data = {"id": 7120, "total": 2055148, "free": 1524904, "buffers": 140224, "cached": 139152, "swap_total": 4128764, "swap_free": 4128764, "active": 324000, "inactive": 123260, "dirty": 56, "ts": "2013-07-17T00:00:16.109Z"};
    _this.startTime = new Date().getTime(); 
    var t1Str = moment(_this.t1).toISOString();
    var t2Str = moment(_this.t2).toISOString();
    _this.jqXhr = $.ajax({
      url: "/api/sm/sprobes/netstat/?format=json&t1=" +
        t1Str + "&t2=" + t2Str, 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        _.each(data.results, function(d) {
          _this.dataBuffers[d.device].push(d);
        });
        _.each(_.keys(_this.dataBuffers), function(device) {
          var dataBuffer = _this.dataBuffers[device];
          if (dataBuffer.length > _this.dataLength) {
            dataBuffer.splice(0, dataBuffer.length - _this.dataLength);
          }
        });
        var dataBuffer = _this.dataBuffers[_this.selectedInterface];
        _this.update(dataBuffer);
        // Check time interval from beginning of last call
        // and call getData or setTimeout accordingly
        var currentTime = new Date().getTime();
        var diff = currentTime - _this.startTime;
        if (diff > _this.updateFreq) {
          _this.t1 = _this.t2; 
          _this.t2 = _this.t2 + diff;
          _this.getData(_this); 
        } else {
          _this.timeoutId = window.setTimeout( function() { 
            _this.t1 = _this.t2; 
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
    $.plot(this.$("#network-util-chart"), newData, this.graphOptions);
    var currentData = dataBuffer[dataBuffer.length-1];
    
    if (this.maximized) { 
      this.$("#data-rec").html(humanize.filesize(currentData["kb_rx"]*1024));
      this.$("#packets-rec").html(currentData["packets_rx"]);  
      this.$("#errors-rec").html(currentData["errs_rx"]);
      this.$("#drop-rec").html(currentData["drop_rx"]);
      this.$("#data-sent").html(humanize.filesize(currentData["kb_tx"]*1024));
      this.$("#packets-sent").html(currentData["packets_tx"]);  
      this.$("#errors-sent").html(currentData["errs_tx"]);
      this.$("#drop-sent").html(currentData["drop_tx"]);
    }
    
  },

  // Creates series to be used by flot
  modifyData: function(dataBuffer) {
    var _this = this;
    var new_data = [];
    var kb_rx = [];
    var kb_tx = [];
    var packets_rx = [];
    var packets_tx = [];
    this.currentTs = dataBuffer[dataBuffer.length-1].ts;

    //this.graphOptions.yaxis = {
     // min: 0,
      //max: 100,
      //tickFormatter: this.memValueTickFormatter,
    //}
    _.each(dataBuffer, function(d,i) {
      kb_rx.push([i, d["kb_rx"]]);
      kb_tx.push([i, d["kb_tx"]]);
      packets_rx.push([i, d["packets_rx"]]);
      packets_tx.push([i, d["packets_tx"]]);
    });
  
    new_data.push({"label": "Data rec", "data": kb_rx, "color": this.colors[0]});
    new_data.push({"label": "Data sent", "data": kb_tx, "color": this.colors[1]});
    new_data.push({"label": "Packets rec", "data": packets_rx, "color": this.colors[2], yaxis: 2, lines: { show: true, lineWidth: 0.5}});
    new_data.push({"label": "Packets sent", "data": packets_tx, "color": this.colors[3], yaxis: 2, lines: {show: true, lineWidth: 0.5}});
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
    document.location.href = "/api/sm/sprobes/netstat/?t1="+t1+"&t2="+t2+"&download=true";
  },

  valueTickFormatter: function(val, axis) {
    return humanize.filesize(val*1024, 1024, 2);
  },

  timeTickFormatter: function(dataLength) {
    return function(val, axis) {
      return (dataLength/60) - (parseInt(val/60)).toString() + ' m';
    };
  },

  tooltipFormatter: function(label, xval, yval) {
    return "%s (%p.2%)"
    //return "%s (" + humanize.filesize(xval, 1024, 1) + ")"; 
  },

  genEmptyData: function() {
    return {
      "id": 0, 
      "kb_rx": 0, 
      "packets_rx": 0, 
      "errs_rx": 0, 
      "drop_rx": 0, 
      "fifo_rx": 0, 
      "frame": 0, 
      "compressed_rx": 0, 
      "multicast_rx": 0, 
      "kb_tx": 0, 
      "packets_tx": 0, 
      "errs_tx": 0, 
      "drop_tx": 0, 
      "fifo_tx": 0, 
      "colls": 0, 
      "carrier": 0, 
      "compressed_tx": 0, 
      "ts": ""
    }; 
  },

  resize: function(event) {
    this.constructor.__super__.resize.apply(this, arguments);
    if (this.maximized) {
      console.log('maximizing');
      this.$('#network-util-values-ph').html(this.valuesTemplate());
    } else {
      console.log('minimizing');
      this.$('#network-util-values-ph').empty();
    }
  },

  cleanup: function() {
    console.log('in network widget - clearing timeout');
    if (this.jqXhr) this.jqXhr.abort(); 
    if (this.timeoutId) window.clearTimeout(this.timeoutId);
  }

});

RockStorWidgets.widgetDefs.push({ 
    name: 'network', 
    displayName: 'Network', 
    view: 'NetworkUtilizationWidget',
    description: 'Display network utilization',
    defaultWidget: true,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Network', 
    position: 3
});


