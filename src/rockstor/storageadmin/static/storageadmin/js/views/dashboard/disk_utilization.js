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


DiskUtilizationWidget = RockStorWidgetView.extend({

    initialize: function() {

        RockStorSocket.diskWidget = io.connect('/disk-widget', {
            'secure': true,
            'force new connection': true
        });
        var _this = this;
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.dashboard_widgets_disk_utilization;
        this.diskUtilSelect = window.JST.dashboard_widgets_disk_util_select;
        this.dataLength = 300;
        this.topDiskColors = [];
        // calculate colors from dark to light for top disks
        var startColor = d3.rgb('#CC6104');
        for (var i = 0; i < 5; i++) {
            this.topDiskColors.push(startColor.toString());
            startColor = startColor.brighter(2);
        }
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
        this.Disksfields = ['ms_ios', 'sectors_written', 'writes_completed', 'ms_writing', 'ms_reading', 'reads_completed', 'sectors_read'];
        this.Diskslabels = ['ms on I/Os', 'kB written', 'Writes', 'ms writing', 'ms reading', 'Reads', 'kB read'];
        this.TopDiskscolors = ['242, 0, 0', '36, 229, 84', '41, 108, 232', '232, 200, 41', '146, 41, 232']
        this.colors2 = ['77, 175, 74', '55, 126, 184']
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
        // maximum number of top disks to display
        this.numTop = this.maximized ? 5 : 3;
        this.partition = d3.layout.partition()
            .value(function(d) {
                return _.reduce(_this.sortAttrs, function(s, a) {
                    return s + d[a];
                }, 0);
            });
        this.graphOptions = {
            grid: {
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
                max: this.dataLength - 1,
                tickFormatter: this.timeTickFormatter(this.dataLength),
                axisLabel: "Time (minutes)",
                axisLabelColour: "#000"
            },
            yaxis: {
                min: 0
            },
            series: {
                lines: {
                    show: true,
                    fill: false
                },
                shadowSize: 0 // Drawing is faster without shadows
            }
        };
        this.dataGraphOptions = {
            grid: {
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
                max: this.dataLength - 1,
                tickFormatter: this.timeTickFormatter(this.dataLength),
                axisLabel: "Time (minutes)",
                axisLabelColour: "#000"
            },
            yaxis: {
                min: 0,
                tickFormatter: this.valueTickFormatter
            },
            series: {
                lines: {
                    show: true,
                    fill: false
                },
                shadowSize: 0 // Drawing is faster without shadows
            }
        };
        this.LineGraphsDefaultOptions = {
            showLines: true,
            animation: {
                duration: 1000,
                easing: 'linear'
            },
            responsive: true,
            legend: {
                display: false
            },
            scales: {
                yAxes: [{
                    position: 'left',
                    scaleLabel: {
                        display: true,
                        fontSize: 11,
                        labelString: 'Data'
                    },
                    ticks: {
                        fontSize: 9,
                        beginAtZero: true,
                        min: 0
                    },
                    gridLines: {
                        drawTicks: false
                    }
                }],
                xAxes: [{
                    scaleLabel: {
                        display: true,
                        fontSize: 11,
                        labelString: 'Time'
                    },
                    gridLines: {
                        display: true,
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

        this.TopDisksChart = null;
        this.TopDisksChartOptions = {
            animation: {
                duration: 1500,
                easing: 'linear'
            },
            responsive: true,
                        legend: {
                display: true,
                position: 'top',
                labels: {
                    boxWidth: 10,
                    padding: 5,
                    fontSize: 10
                }
            },
            scale: {
                ticks: {
                    display: false,
                    min: 0,
                    max: 100,
                    stepSize: 20
                }
            }
        };
        this.TopDisksChartData = {
            labels: this.Diskslabels,
            datasets: []
        };

        this.DiskReadWriteChart = null;
        this.DiskReadWriteChartOptions = this.LineGraphsDefaultOptions;
        this.DiskReadWriteChartData = {
            datasets: [{
                label: this.Diskslabels[0],
                backgroundColor: 'rgba(' + this.colors2[0] + ', 0.4)',
                borderColor: 'rgba(' + this.colors2[0] + ', 1)',
                data: []
            }, {
                label: this.Diskslabels[1],
                backgroundColor: 'rgba(' + this.colors2[1] + ', 0.4)',
                borderColor: 'rgba(' + this.colors2[1] + ', 1)',
                data: []
            }]
        };

        this.DiskkBChart = null;
        this.DiskkBChartOptions = this.LineGraphsDefaultOptions;
        this.DiskkBChartOptions.scales.yAxes[0].ticks.callback = function(value) {
            return humanize.filesize(value);
        }
        this.DiskkBChartData = {
            datasets: [{
                label: this.Diskslabels[2],
                backgroundColor: 'rgba(' + this.colors2[0] + ', 0.4)',
                borderColor: 'rgba(' + this.colors2[0] + ', 1)',
                data: []
            }, {
                label: this.Diskslabels[3],
                backgroundColor: 'rgba(' + this.colors2[1] + ', 0.4)',
                borderColor: 'rgba(' + this.colors2[1] + ', 1)',
                data: []
            }]
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
                if (_.indexOf(_this.sortAttrs, v) == -1) {
                    _this.sortAttrs.push(v);
                }
            } else {
                if (_.indexOf(_this.sortAttrs, v) != -1) {
                    if (_this.sortAttrs.length > 1) {
                        _this.sortAttrs = _.without(_this.sortAttrs, v);
                    } else {
                        // dont allow the last attr to be unchecked
                        cbox.prop('checked', true);
                    }
                }
            }
        });

        this.disks.fetch({
            success: function(collection, response, options) {
                _this.initializeDisksData();
                _this.initTopDisksChart();
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
            _this.disksData[name] = [];
            for (var i = 0; i < _this.dataLength; i++) {
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

    initTopDisksChart: function() {

        var _this = this;
        for (var i = 0; i < this.numTop; i++) {
            var dataset = {
                label: '',
                borderWidth: 1,
                fill: true,
                borderColor: 'rgba(' + _this.TopDiskscolors[i] + ', 1)',
                backgroundColor: 'rgba(' + _this.TopDiskscolors[i] + ', 0.1)',
                pointBackgroundColor: 'rgba(' + _this.TopDiskscolors[i] + ', 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(' + _this.TopDiskscolors[i] + ', 1)',
                data: [0, 0, 0, 0, 0, 0, 0]
            };
            _this.TopDisksChartData.datasets.push(dataset);
        }
    },

    getData: function(data) {

        var _this = this;
        if (!_this.graphRendered) {
            _this.initGraphs();
            _this.graphRendered = true;
        }
        _this.startTime = new Date().getTime();
        _this.update(data);
    },

    update: function(data) {

        this.updateDisksData(data);
        this.sortDisks();
        this.updateTopDisksChart();
        if (this.maximized) this.renderDiskGraph();
    },

    initGraphs: function() {

        var _this = this;
        _this.TopDisksChart = new Chart(this.$('#top-disks-chart'), {
            type: 'radar',
            data: _this.TopDisksChartData,
            options: _this.TopDisksChartOptions
        });
    },
    
    updateTopDisksChart: function() {

        var _this = this;
        for (var i=0; i < _this.numTop; i++) {
            var data = [];
            _.each(_this.Disksfields, function(field) {
                data.push(_this.normalizeData(field, _this.topDisks[i][field]));
            });
            _this.TopDisksChartData.datasets[i].data = data;
            _this.TopDisksChartData.datasets[i].label = _this.topDisks[i].name;
        }
        _this.TopDisksChart.update();
    },

    //Chart.js radar chart don't have multiple scales
    //so we have to normalize our data
    //data normalization has new_x = (x - x_min) / (x_max -x_min) and returns x [0..1]
    //we assume our x_min = 0, so new_x = x /x_max
    normalizeData: function(field, val) {

        var _this = this;
        var val_max = _.max(_.pluck(_this.topDisks, field));
        var new_val = val == 0 ? 0 : (val * 100 / val_max).toFixed(2); //we use a 0..100 range with 2 decimals
        return new_val;
    },
    
    sortDisks: function() {

        var _this = this;
        var tmp = _.map(_.keys(_this.disksData), function(k) {
            return _this.disksData[k][_this.dataLength - 1];
        });
        var sorter = _this.sortAttrs[0];
        _this.topDisks = _.sortBy(tmp, function(d) {
            return d[sorter];
        }).reverse();
    },

    updateDisksData: function(data) {

        var _this = this;
        _.each(data, function(d) {
            _this.disksData[d.name].push(d);
            _this.disksData[d.name].shift();
        });
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
        for (var i = 0; i < this.dataLength; i++) {
            tmpReads.push([i, vals[i].reads_completed]);
        }
        var tmpWrites = [];
        for (var i = 0; i < this.dataLength; i++) {
            tmpWrites.push([i, vals[i].writes_completed]);
        }
        var series1 = [{
            label: 'Reads',
            data: tmpReads,
            color: this.colors[0]
        }, {
            label: 'Writes',
            data: tmpWrites,
            color: this.colors[1]
        }];
        $.plot(this.$('#disk-graph-reads-ph'), series1, this.graphOptions);

        var tmpReadData = [];
        for (var i = 0; i < this.dataLength; i++) {
            tmpReadData.push([i, vals[i].sectors_read * 512]);
        }
        var tmpWriteData = [];
        for (var i = 0; i < this.dataLength; i++) {
            tmpWriteData.push([i, vals[i].sectors_written * 512]);
        }
        var series2 = [{
            label: 'KB read',
            data: tmpReadData,
            color: this.colors[0]
        }, {
            label: 'KB written',
            data: tmpWriteData,
            color: this.colors[1]
        }];
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
        // maximum number of top disks to display
        this.numTop = this.maximized ? 5 : 3;
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
            return ((dataLength / 60) - (parseInt(val / 60))).toString() + ' m';
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
