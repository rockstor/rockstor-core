/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
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
    RockStorSocket.networkWidget = io.connect('/network-widget', {'secure': true, 'force new connection': true});
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_network_utilization;
    this.valuesTemplate = window.JST.dashboard_widgets_network_util_values;
    this.updateFreq = 1000;
    this.dataBuffers = {};
    this.dataLength = 300;
    this.currentTs = null;
    this.networkInterfaces = new NetworkDeviceCollection();
    this.networkInterfaces.on("reset", this.getInitialData, this);
    this.selectedInterface = null;
	this.numSamples = 60;
    this.colors = ["#1224E3", "#F25805", "#04D6D6", "#F5CC73", "#750413"];
	this.netdatatype = ['Data rec', 'Data sent', 'Packets rec', 'Packets sent'];
	this.colors2 = ['18, 36, 227', '242, 88, 5', '4, 214, 214', '245, 204, 115'];
    this.totalMem = 0;
	Chart.defaults.global.tooltips.enabled = false;
	Chart.defaults.global.elements.line.tension = 0.2;
	Chart.defaults.global.elements.line.borderCapStyle = 'butt';
	Chart.defaults.global.elements.line.borderDash = [];
	Chart.defaults.global.elements.line.borderDashOffset = 0.0;
	Chart.defaults.global.elements.line.borderWidth = 1;
	Chart.defaults.global.elements.line.borderJoinStyle = 'miter';
	Chart.defaults.global.elements.line.fill = false;
	Chart.defaults.global.elements.point.radius = 0;
	Chart.defaults.global.elements.point.hoverRadius = 0;

	this.NetworkChart = null;
	this.NetworkChartOptions = {
		showLines: true,
            legend: {
                display: false,
                position: 'bottom',
                labels: {
                    boxWidth: 8,
                    padding: 2,
					fontSize: 10
                }
            },
			scales: {
                yAxes: [{
					id: 'Data',
					position: 'left',
					                    scaleLabel: {
                        display: true,
                        fontSize: 10,
                        labelString: 'Data'
                    },
                    ticks: {
                        fontSize: 9,
						beginAtZero: 0,
						min: 0,
                        callback: function(value) {
                            return humanize.filesize(value);
                        }
                    },
                    gridLines: {
                        drawTicks: false
                    }
				},
					{
					id: 'Packets',
					position: 'right',
					                    scaleLabel: {
                        display: true,
                        fontSize: 10,
                        labelString: 'Packets'
                    },
					ticks: {
						fontSize: 9,
						beginAtZero: 0,
						min: 0
					},
					gridLines: {
						drawTicks: false
					}
                }],
                xAxes: [{
                    scaleLabel: {
                        display: true,
                        fontSize: 10,
                        labelString: 'Time'
                    },
                    gridLines: {
                        display: false,
                        drawTicks: false
                    },
                    ticks: {
                        fontSize: 9,
                        maxRotation: 0,
                        autoSkip: false,
                        callback: function(value) {
                            return (value.toString().length > 0 ? value : null);
                    }
					}
                }]
            }
	};
	
	this.NetworkChartData = {
		labels: [],
		datasets: []
	};
	this.NetData = {};
	
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
          axisLabelPadding: 0
        },
        {
          position: "right",
          min: 0,
          axisLabel: "Packets",
          axisLabelColour: "#000",
          axisLabelPadding: 0
        }
      ],
			series: {
        lines: { show: true, fill: false },
        shadowSize: 0	// Drawing is faster without shadows
			},
      /*legend : {
        container: "#network-util-legend",
        noColumns: 2,
        margin: [30,0],
        labelBoxBorderColor: "#fff"

      }*/
    };

    // Start and end timestamps for api call
    this.windowLength = 300000;

    //this.t2 = new Date('2013-12-03T17:18:06.312Z').getTime();
    this.t1 = this.t2 - this.windowLength;
	//Chart.js Network Widget default options

	this.genEmptyNetworkChartData(this.numSamples);
  },
  
    genEmptyNetworkChartData: function(numSamples) {
        var _this = this;
		//Create initial empty data required to have line chart right alligned
        for (var i = 0; i < numSamples; i++) {
            _this.NetworkChartData.labels.push('');	
        }
		_.each(_this.netdatatype, function(value, index) {
			var YaxisID = value.indexOf('Data') > -1 ? 'Data' : 'Packets';
			var dataset = {
				label: value,
				yAxisID: YaxisID,
				backgroundColor: 'rgba(' + _this.colors2[index] + ', 0.4)',
				borderColor: 'rgba(' + _this.colors2[index] + ', 1)',
				data: []
			};
			_this.NetworkChartData.datasets.push(dataset);
			for (var i = 0; i < numSamples; i++) {
				_this.NetworkChartData.datasets[index].data.push(null);
			}
		});
    },
	genNetworkChartLegend: function() {
		var _this = this;
		var legend = '<ul style="list-style-type: none; display: inline;">';
		_.each(_this.NetworkChartData.datasets, function(dataset, index) {
			legend += '<li><span style="background-color: ' + dataset.backgroundColor + '; ';
			legend += 'border-style: solid; border-color: ' + dataset.borderColor + '; ';
			legend += 'border-width: 1px; display: inline; width: 10px; height: 10px; float: left; margin: 2px;"></span>';
			legend += dataset.label + '</li>';
		});
		legend += '</ul>';
		return legend;
	},

    initGraphs: function() {
        var _this = this;

        _this.NetworkChart = new Chart(this.$('#network-chart'), {
            type: 'line',
            data: _this.NetworkChartData,
            options: _this.NetworkChartOptions
        });
		this.$('#network-util-legend').html(_this.genNetworkChartLegend());
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
    var pageSizeStr = '&page_size=' + RockStorGlobals.maxPageSize;
    this.jqXhr = $.ajax({
      url: '/api/sm/sprobes/netstat/?format=json&page_size=1',
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        // fill dataBuffers
        _this.networkInterfaces.each(function(ni) {
          var tmp = [];
          _this.dataBuffers[ni.get("name")] = tmp;
		  _this.NetData[ni.get("name")] = tmp;
        });
		console.log(_this.networkInterfaces);
		console.log(_this.NetData);
        _.each(data.results, function(d) {
          _this.dataBuffers[d.device].push(d);
		  //_this.NetData[d.device]
        });
        _.each(_.keys(_this.dataBuffers), function(device) {
          var dataBuffer = _this.dataBuffers[device];
          if (dataBuffer.length > 0) {
            while (new Date(dataBuffer[0].ts).getTime() < _this.t2-(_this.windowLength )) {
              dataBuffer.shift();
            }
          }
        });
        RockStorSocket.addListener(_this.getData, _this, 'networkWidget:network');

      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }

    });

  },

  getData: function(data) {
    var _this = this;
    this.t2 = new Date(data.results[0].ts);
	        if (!_this.graphRendered) {
            _this.initGraphs();
            _this.graphRendered = true;
        }
    //var data = {"id": 7120, "total": 2055148, "free": 1524904, "buffers": 140224, "cached": 139152, "swap_total": 4128764, "swap_free": 4128764, "active": 324000, "inactive": 123260, "dirty": 56, "ts": "2013-07-17T00:00:16.109Z"};
    _this.startTime = new Date().getTime();
    _.each(data.results, function(d) {
      _this.dataBuffers[d.device].push(d);
	  _this.NetData[d.device].push(d);
    });
    _.each(_.keys(_this.dataBuffers), function(device) {
      var dataBuffer = _this.dataBuffers[device];
      if (dataBuffer.length > 0) {
        while (new Date(dataBuffer[0].ts).getTime() < _this.t2-(_this.windowLength )) {
          dataBuffer.shift();
        }
      }
    });
	//console.log(_this.NetData);
    var dataBuffer = _this.dataBuffers[_this.selectedInterface];
    _this.update(dataBuffer);
    // Check time interval from beginning of last call
    // and call getData or setTimeout accordingly
    var diff = currentTime - _this.startTime;
    var currentTime = new Date().getTime();
    if (diff > _this.updateFreq) {
      if (dataBuffer.length > 0) {
        _this.t1 = new Date(dataBuffer[dataBuffer.length-1].ts).getTime();
      } else {
        _this.t1 = _this.t1 + diff;
      }
      _this.t2 = _this.t2 + diff;
    } else {
      if (dataBuffer.length > 0) {
        _this.t1 = new Date(dataBuffer[dataBuffer.length-1].ts).getTime();
      } else {
        _this.t1 = _this.t1 + _this.updateFreq;
      }
      _this.t2 = _this.t2 + _this.updateFreq;
    }
  },

  update: function(dataBuffer) {
    var newData = this.modifyData(dataBuffer);
    this.graphOptions.xaxis = {
      mode: 'time',
      min: this.t2 - this.windowLength,
      max: this.t2,
      timezone: 'browser'
    };
    $.plot(this.$("#network-util-chart"), newData, this.graphOptions);
    var currentData = this.genEmptyData();
    if (dataBuffer.length > 0) {
      currentData = dataBuffer[dataBuffer.length-1];
    }

    if (this.maximized) {
      this.$("#data-rec").html(humanize.filesize(currentData["kb_rx"]));
      this.$("#packets-rec").html(currentData["packets_rx"]);
      this.$("#errors-rec").html(currentData["errs_rx"]);
      this.$("#drop-rec").html(currentData["drop_rx"]);
      this.$("#data-sent").html(humanize.filesize(currentData["kb_tx"]));
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

    if (dataBuffer.length > 0) {
      this.currentTs = dataBuffer[dataBuffer.length-1].ts;

      //this.graphOptions.yaxis = {
      // min: 0,
      //max: 100,
      //tickFormatter: this.memValueTickFormatter,
      //}
      _.each(dataBuffer, function(d,i) {
        kb_rx.push([(new Date(d.ts)).getTime(), d["kb_rx"]]);
        kb_tx.push([(new Date(d.ts)).getTime(), d["kb_tx"]]);
        packets_rx.push([(new Date(d.ts)).getTime(), d["packets_rx"]]);
        packets_tx.push([(new Date(d.ts)).getTime(), d["packets_tx"]]);
      });
    }
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
    return humanize.filesize(val, 1024, 2);
  },

  timeTickFormatter: function(dataLength) {
    return function(val, axis) {
      return (dataLength/60) - (parseInt(val/60)).toString() + ' m';
    };
  },

  tooltipFormatter: function(label, xval, yval) {
    return "%s (%p.2%)";
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
      this.$('#network-util-values-ph').html(this.valuesTemplate());
    } else {
      this.$('#network-util-values-ph').empty();
    }
	this.NetworkChart.resize();
  },

  cleanup: function() {
    RockStorSocket.removeOneListener('networkWidget');
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
    position: 5
});
