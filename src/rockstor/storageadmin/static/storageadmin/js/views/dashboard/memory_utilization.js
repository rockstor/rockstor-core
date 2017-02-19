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

MemoryUtilizationWidget = RockStorWidgetView.extend({

    initialize: function() {
        RockStorSocket.memoryWidget = io.connect('/memory_widget', {
            'secure': true,
            'force new connection': true
        });
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.dashboard_widgets_memory_utilization;
        this.numSamples = 60;
        this.modes = ['used', 'cached', 'buffers', 'free'];
        this.colors = ['251, 106, 74', '252, 187, 61', '123, 204, 196', '204, 235, 197', '4, 214, 214'];

        //Chart.js Network Widget default options
        Chart.defaults.global.tooltips.enabled = false;
        Chart.defaults.global.elements.line.tension = 0.2;
        Chart.defaults.global.elements.line.borderCapStyle = 'butt';
        Chart.defaults.global.elements.line.borderDash = [];
        Chart.defaults.global.elements.line.borderDashOffset = 0.0;
        Chart.defaults.global.elements.line.borderWidth = 1;
        Chart.defaults.global.elements.rectangle.borderWidth = 1;
        Chart.defaults.global.elements.line.borderJoinStyle = 'miter';
        Chart.defaults.global.elements.point.radius = 0;
        Chart.defaults.global.elements.point.hoverRadius = 0;

        //Define MemoryChart object with options and data structure
        this.MemoryChart = null;

        this.MemoryChartOptions = {
            showLines: true,
            animation: {
                duration: 1250,
                easing: 'linear'
            },
            responsive: true,
            title: {
                display: true,
                text: 'Memory Usage (%)',
                padding: 5,
            },
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    boxWidth: 10,
                    padding: 5,
                    fontSize: 10
                }
            },
            scales: {
                yAxes: [{
                    id: 'memory',
                    position: 'left',
                    stacked: true,
                    ticks: {
                        fontSize: 10,
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        stepSize: 50,
                        callback: function(value) {
                            return value + ' %';
                        }
                    },
                    gridLines: {
                        drawTicks: false
                    }
                }, {
                    id: 'empty',
                    position: 'right',
                    ticks: {
                        fontSize: 9,
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        stepSize: 50,
                        callback: function(value) {
                            return null;
                        }
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
                        display: false,
                        drawTicks: false,
                        tickMarkLength: 2
                    },
                    ticks: {
                        fontSize: 10,
                        maxRotation: 0,
                        autoSkip: false,
                        callback: function(value) {
                            return (value.toString().length > 0 ? value : null);
                        }
                    }
                }]
            }
        };

        this.MemoryChartData = {
            labels: [],
            datasets: [{
                label: this.modes[0],
                yAxisID: 'memory',
                fill: true,
                backgroundColor: 'rgba(' + this.colors[0] + ', 1)',
                borderColor: 'rgba(' + this.colors[0] + ', 1)',
                data: []
            }, {
                label: this.modes[1],
                yAxisID: 'memory',
                fill: true,
                backgroundColor: 'rgba(' + this.colors[1] + ', 1)',
                borderColor: 'rgba(' + this.colors[1] + ', 1)',
                data: []
            }, {
                label: this.modes[2],
                yAxisID: 'memory',
                fill: true,
                backgroundColor: 'rgba(' + this.colors[2] + ', 1)',
                borderColor: 'rgba(' + this.colors[2] + ', 1)',
                data: []
            }, {
                label: this.modes[3],
                yAxisID: 'memory',
                fill: true,
                backgroundColor: 'rgba(' + this.colors[3] + ', 1)',
                borderColor: 'rgba(' + this.colors[3] + ', 1)',
                data: []
            }]
        };

        this.SwapChart = null;

        this.SwapChartOptions = {
            title: {
                display: true,
                text: 'Swap Usage',
                padding: 5,
            },
            showLines: true,
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    boxWidth: 10,
                    padding: 5,
                    fontSize: 10
                }
            },
            tooltips: {
                enabled: false
            },
            scales: {
                yAxes: [{
                    ticks: {
                        fontSize: 10,
                        callback: function(value) {
                            return null;
                        }
                    },
                    gridLines: {
                        display: false,
                        zeroLineWidth: 0,
                        drawTicks: false,
                        padding: 0
                    }
                }],
                xAxes: [{
                    scaleLabel: {
                        display: false,
                        fontSize: 1,
                        labelString: ''
                    },
                    gridLines: {
                        display: false,
                        drawTicks: false,
                        tickMarkLength: 0
                    },
                    ticks: {
                        fontSize: 10,
                        min: 0,
                        maxTicksLimit: 2,
                        autoSkip: false,
                        padding: 0,
                        callback: function(value) {
                            return (value > 0 ? humanize.filesize(value) : null);
                        }
                    }
                }]
            },
        };

        this.SwapChartData = {
            labels: [''],
            datasets: [{
                label: '',
                backgroundColor: 'rgba(' + this.colors[4] + ', 0.2)',
                borderColor: 'rgba(' + this.colors[4] + ', 1)',
                data: [0]
            }]
        };

        this.margin = {
            top: 20,
            right: 20,
            bottom: 20,
            left: 30
        };
        this.padding = {
            top: 0,
            right: 0,
            bottom: 20,
            left: 0
        };

        if (this.maximized) {
            this.width = 500 - this.margin.left - this.margin.right;
            this.height = 200 - this.margin.top - this.margin.bottom;
        } else {
            this.width = 250 - this.margin.left - this.margin.right;
            this.height = 100 - this.margin.top - this.margin.bottom;
        }
    },

    render: function() {

        this.constructor.__super__.render.apply(this, arguments);
        $(this.el).html(this.template({
            module_name: this.module_name,
            displayName: this.displayName,
            maximized: this.maximized
        }));
        RockStorSocket.addListener(this.getData, this, 'memoryWidget:memory');
        return this;
    },

    getData: function(data) {

        var _this = this;
        data = data.results[0];
        if (!_this.graphRendered) {
            _this.genMemoryInitData(data);
            _this.initGraph();
            _this.graphRendered = true;
        } else {
            _this.updateMemoryChart(data);
            _this.updateSwapChart(data);
        }

    },

    genMemoryInitData: function(data) {
        var _this = this;
        for (var i = 0; i < _this.numSamples; i++) {
            _.each(_this.MemoryChartData.datasets, function(d) {
                d.data.push(null);
            });
            _this.MemoryChartData.labels.push('');
        }
    },

    initGraph: function() {

        var _this = this;

        _this.MemoryChart = new Chart(this.$('#memory-chart'), {
            type: 'line',
            data: _this.MemoryChartData,
            options: _this.MemoryChartOptions
        });

        _this.SwapChart = new Chart(this.$('#swap-chart'), {
            type: 'horizontalBar',
            data: _this.SwapChartData,
            options: _this.SwapChartOptions
        });
    },

    dataToPercent: function(data) {

        var _this = this;
        var newdata = [];
        _.each(_this.modes, function(d) {
            newdata.push(data[d] * 100 / data.total);
        });
        newdata[0] = 100 - newdata[1] - newdata[2] - newdata[3];
        return newdata;
    },

    updateMemoryChart: function(data) {

        var _this = this;
        var newMemoryvalues = _this.dataToPercent(data);
        _.each(_this.modes, function(d, i) {
            _this.MemoryChartData.datasets[i].data.shift();
            _this.MemoryChartData.datasets[i].data.push(newMemoryvalues[i]);
            _this.MemoryChartData.datasets[i].label = d + ' ' + newMemoryvalues[i].toFixed(2) + ' %';
        });
        var csecs = moment(data.ts).format('s');
        var label = '';
        if (csecs % 15 === 0) {
            label = csecs == '0' ? moment(data.ts).format('HH:mm') : moment(data.ts).format(':ss');
        }
        _this.MemoryChartData.labels.shift();
        _this.MemoryChartData.labels.push(label);
        _this.MemoryChart.update();
    },

    updateSwapChart: function(data) {

        var _this = this;
        var swap_free = data.swap_free * 1024;
        var swap_total = data.swap_total * 1024;
        var swap_used = swap_total - swap_free;
        var swap_used_per = (swap_used * 100 / swap_total).toFixed(2);
        var swap_label = 'Used ' + swap_used_per + ' % (' + humanize.filesize(swap_used) + ' / ' + humanize.filesize(swap_total) + ')';

        _this.SwapChartData.datasets[0].data = [swap_used];
        _this.SwapChartData.datasets[0].label = swap_label;
        _this.SwapChart.config.options.scales.xAxes[0].ticks.max = swap_total;
        _this.SwapChart.update();

    },

    cleanup: function() {

        RockStorSocket.removeOneListener('memoryWidget');
    },

    resize: function() {

        this.constructor.__super__.resize.apply(this, arguments);
        if (this.maximized) {
            this.width = 500 - this.margin.left - this.margin.right;
            this.height = 240 - this.margin.top - this.margin.bottom;
        } else {
            this.width = 250 - this.margin.left - this.margin.right;
            this.height = 120 - this.margin.top - this.margin.bottom;
        }

        this.MemoryChart.resize();
        this.SwapChart.resize();

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