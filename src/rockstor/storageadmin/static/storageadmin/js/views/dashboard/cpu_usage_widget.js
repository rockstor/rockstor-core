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


CpuUsageWidget = RockStorWidgetView.extend({

    initialize: function() {
        RockStorSocket.cpuWidget = io.connect('/cpu_widget', {
            'secure': true,
            'force new connection': true
        });
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.dashboard_widgets_cpuusage;
        // maximized size for shapeshift
        this.maxCols = 10;
        this.maxRows = 2;
        this.numSamples = 60;
        this.maxCpus = 8;
        this.modes = ['smode', 'umode', 'umode_nice', 'idle'];
        this.colors = ['255, 140, 0', '152, 171, 197', '138, 137, 166', '255, 255, 255'];

        this.AllCpuChart = null;
        this.AllCpuChartOptions = {
            title: {
                display: true,
                text: 'Individual CPU Usage (%)',
                padding: 5,
            },
            showLines: true,
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    boxWidth: 10,
                    padding: 10
                }
            },
            tooltips: {
                enabled: false
            },
            scales: {
                yAxes: [{
                    stacked: true,
                    ticks: {
                        fontSize: 10,
                        max: 100,
                        min: 0,
                        stepSize: 25,
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    gridLines: {
                        drawTicks: false
                    }
                }],
                xAxes: [{
                    stacked: true,
                    gridLines: {
                        display: false,
                        drawTicks: false
                    },
                    ticks: {
                        fontSize: 10,
                        maxRotation: 0,
                        autoSkip: false
                    }
                }]
            },
        };
        this.AllCpuChartData = {
            labels: [],
            datasets: [{
                label: 'smode',
                backgroundColor: [],
                borderColor: [],
                borderWidth: 1,
                data: []
            }, {
                label: 'umode',
                backgroundColor: [],
                borderColor: [],
                borderWidth: 1,
                data: []
            }, {
                label: 'umode_nice',
                backgroundColor: [],
                borderColor: [],
                borderWidth: 1,
                data: []
            }]
        };

        this.AvgCpuChart = null;
        this.AvgCpuChartOptions = {
            showLines: true,
            animation: {
                duration: 1250,
                easing: 'linear'
            },
            responsive: true,
            title: {
                display: true,
                text: 'Average CPU Usage (%)',
                padding: 5
            },
            legend: {
                display: false,
                position: 'top',
                labels: {
                    boxWidth: 10,
                    padding: 2
                }
            },
            tooltips: {
                enabled: false
            },
            scales: {
                yAxes: [{
                    id: 'cpu',
                    position: 'left',
                    gridLines: {
                        drawTicks: false
                    },
                    ticks: {
                        fontSize: 10,
                        max: 100,
                        min: 0,
                        stepSize: 25,
                        callback: function(value) {
                            return value + '%';
                        }
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
                        display: true,
                        drawTicks: false
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
        this.AvgCpuChartData = {
            labels: [],
            datasets: [{
                label: '',
                yAxisID: 'cpu',
                fill: false,
                lineTension: 0.2,
                backgroundColor: 'rgba(75,192,192,0.4)',
                borderColor: 'rgba(75,192,192,1)',
                borderCapStyle: 'butt',
                borderDash: [],
                borderDashOffset: 0.0,
                borderWidth: 1,
                borderJoinStyle: 'miter',
                pointBorderColor: 'rgba(75,192,192,1)',
                pointBackgroundColor: '#fff',
                pointBorderWidth: 1,
                pointHoverRadius: 0,
                pointHoverBackgroundColor: 'rgba(75,192,192,1)',
                pointHoverBorderColor: 'rgba(220,220,220,1)',
                pointHoverBorderWidth: 0,
                pointRadius: 0,
                pointHitRadius: 10,
                data: [],
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

        //Generate empty data/labels on avg cpu and all charts
        this.genAvgCpuInitData(this.numSamples);
        this.genAllCpuInitData(this.maxCpus);

    },

    genAvgCpuInitData: function(numSamples) {
        var _this = this;
        for (var i = 0; i < numSamples; i++) {
            //Create initial empty data required to have line chart right alligned
            _this.AvgCpuChartData.labels.push('');
            _this.AvgCpuChartData.datasets[0].data.push(null);
        }
    },

    genAllCpuInitData: function(maxCpus) {
        var _this = this;
        for (var i = 0; i < maxCpus; i++) {
            _this.AllCpuChartData.labels.push('');
            var current_color = '';
            _.each(_this.AllCpuChartData.datasets, function(dataset, i) {
                //define each barchar rectangle with relative modes colors
                current_color = 'rgba(' + _this.colors[_.indexOf(_this.modes, dataset.label)] + ', 0.3)';
                dataset.backgroundColor.push(current_color);
                dataset.borderColor.push(current_color);
                dataset.data.push(null);
            });

        }
    },

    render: function() {
        this.constructor.__super__.render.apply(this, arguments);
        var _this = this;
        $(this.el).html(this.template({
            modes: this.modes,
            colors: this.colors,
            height: this.defaultHeight,
            width: this.defaultWidth,
            displayName: this.displayName,
            maximized: this.maximized
        }));
        RockStorSocket.addListener(this.getData, this, 'cpuWidget:cpudata');
        return this;
    },

    getData: function(data) {
        var _this = this;
        data = data.results;

        //If our charts on first load render them on page with empty data
        if (!_this.graphRendered) {
            _this.initGraphs();
            _this.graphRendered = true;
        }

        _this.updateAvgCpuGraph(data);
        _this.updateAllCpuGraph(data);
    },

    initGraphs: function() {
        var _this = this;

        _this.AvgCpuChart = new Chart(this.$('#cpuusage-avg-chart'), {
            type: 'line',
            data: _this.AvgCpuChartData,
            options: _this.AvgCpuChartOptions
        });

        _this.AllCpuChart = new Chart(this.$('#cpuusage-all-chart'), {
            type: 'bar',
            data: _this.AllCpuChartData,
            options: _this.AllCpuChartOptions
        });
    },

    updateAvgCpuGraph: function(data) {
        var _this = this;
        //We use old getAvgCpuUsage function then
        //delete first line chart element and push new one
        //If current time is multiple of 15 secs render it
        var avgcpu = _this.getAvgCpuUsage(data);
        _this.AvgCpuChartData.datasets[0].data.shift();
        _this.AvgCpuChartData.labels.shift();
        var csecs = moment(avgcpu[0].ts).format('s');
        var label = '';
        if (csecs % 15 === 0) {
            label = csecs == '0' ? moment(avgcpu[0].ts).format('HH:mm') : moment(avgcpu[0].ts).format(':ss');
        }
        _this.AvgCpuChartData.datasets[0].data.push(100 - avgcpu[0].idle);
        _this.AvgCpuChartData.labels.push(label);
        _this.AvgCpuChart.update();
    },

    updateAllCpuGraph: function(data) {
        var _this = this;
        //If we don't have already cpu names, get it!
        if (_this.AllCpuChartData.labels[0] === '') {
            _.each(data, function(cpu, k) {
                _this.AllCpuChartData.labels[k] = cpu.name;
            });
        }
        //Loop on the bar chart dataset and update every cpu mode val for every cpu found
        _.each(_this.AllCpuChartData.datasets, function(dataset, i) {
            _.each(data, function(cpu, k) {
                dataset.data[k] = cpu[dataset.label];
            });

        });
        _this.AllCpuChart.update();
    },

    getAvgCpuUsage: function(data) {
        var _this = this;
        var tmp = _.groupBy(data, function(d) {
            return d.ts;
        });
        return _.map(_.keys(tmp), function(key) {
            var ds = tmp[key];
            if (ds.length > 0) {
                var s = _.reduce(ds, function(sum, d) {
                    return d.idle + sum;
                }, 0);
                var avg = s / ds.length;
                return {
                    idle: avg,
                    ts: key
                };
            } else {
                return {
                    idle: 0,
                    ts: key
                };
            }
        });
    },

    resize: function(event) {
        this.constructor.__super__.resize.apply(this, arguments);
        if (this.maximized) {
            this.width = 500 - this.margin.left - this.margin.right;
            this.height = 200 - this.margin.top - this.margin.bottom;

        } else {
            this.width = 250 - this.margin.left - this.margin.right;
            this.height = 100 - this.margin.top - this.margin.bottom;
        }
        this.AvgCpuChart.resize();
        this.AllCpuChart.resize();
    },

    cleanup: function() {
        if (!_.isUndefined(this.timeoutId)) {
            window.clearTimeout(this.timeoutId);
        }
        RockStorSocket.removeOneListener('cpuWidget');
    }

});

// Default configuration for cpu widget
RockStorWidgets.widgetDefs.push({
    name: 'cpuusage',
    displayName: 'CPU',
    view: 'CpuUsageWidget',
    description: 'CPU Utilization',
    defaultWidget: true,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Compute',
    position: 3
});