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

StorageMetricsWidget = RockStorWidgetView.extend({

    initialize: function() {

        var _this = this;
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.dashboard_widgets_storage_metrics;
        this.legendTemplate = window.JST.dashboard_widgets_storage_metrics_legend;
        // Dependencies
        this.disks = new DiskCollection();
        this.pools = new PoolCollection();
        this.shares = new ShareCollection();
        this.disks.pageSize = RockStorGlobals.maxPageSize;
        this.shares.pageSize = RockStorGlobals.maxPageSize;
        this.pools.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.disks);
        this.dependencies.push(this.pools);
        this.dependencies.push(this.shares);

        this.data = [];
        this.colors = [{
            Used: '250, 198, 112',
            Allocated: '11, 214, 227',
            Provisioned: '145, 191, 242'
        }, {
            Capacity: '250, 232, 202',
            'Raid Overhead': '176, 241, 245',
            Free: '228, 237, 247'
        }];

        //Chart.js Storage Metrics Widget default options
        Chart.defaults.global.tooltips.enabled = false;
        Chart.defaults.global.elements.rectangle.borderWidth = 1;

        this.StorageMetricsChart = null;
        this.StorageMetricsChartOptions = {
            title: {
                display: false,
            },
            showLines: false,
            legend: {
                display: false,
            },
            tooltips: {
                enabled: false
            },
            hover: {
                animationDuration: 0
            },
            animation: {
                duration: 1000,
                onComplete: function() {

                    var ctx = this.chart.ctx;
                    var font_size = 12;
                    var labels = ['Shares', 'Pools', 'Disks'];
                    ctx.font = Chart.helpers.fontString(font_size,
                        Chart.defaults.global.defaultFontStyle,
                        Chart.defaults.global.defaultFontFamily);
                    ctx.fillStyle = '#000000';
                    ctx.textBaseline = 'top';
                    _.each(this.data.datasets, function(dataset, index, datasets) {
                        ctx.textAlign = (index % 2 === 0) ? 'left' : 'right';

                        for (var i = 0; i < dataset.data.length; i++) {
                            var model = dataset._meta[Object.keys(dataset._meta)[0]].data[i]._model;
                            var x_pos = (index % 2 === 0) ? model.base + 1 : model.x - 1;
                            var y_pos = (index % 2 === 0) ? model.y + model.height / 2 - font_size - 2 : model.y - model.height / 2 + 2;
                            var label = humanize.filesize(dataset.data[i]);
                            if (index % 2 === 0) {
                                var pct = datasets[0].data[i] * 100 / (datasets[0].data[i] + datasets[1].data[i]);
                                label += ' (' + pct.toFixed(2) + '%)';
                                ctx.save();
                                ctx.textAlign = 'center';
                                ctx.translate(model.base - font_size, model.y);
                                ctx.rotate(-0.5 * Math.PI);
                                ctx.fillText(labels[i], 0, 0);
                                ctx.restore();
                            }
                            ctx.fillText(label, x_pos, y_pos);

                        }
                    });
                }
            },
            scales: {
                yAxes: [{
                    stacked: true,
                    ticks: {
                        fontSize: 9,
                        minRotation: 60,
                    },
                    gridLines: {
                        display: false,
                        zeroLineWidth: 0,
                        drawTicks: true,
                        offsetGridLines: true
                    }
                }],
                xAxes: [{
                    stacked: true,
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

        this.StorageMetricsChartData = {
            labels: ['', '', ''],
            datasets: [{
                fill: true,
                backgroundColor: this.setColors(0, 0.8),
                borderColor: this.setColors(0, 1),
                data: []
            }, {
                fill: true,
                backgroundColor: this.setColors(1, 0.8),
                borderColor: this.setColors(1, 1),
                data: []
            }]
        };
    },

    setColors: function(index, alpha) {

        var _this = this;
        var color_array = [];
        _.each(_this.colors[index], function(val) {
            color_array.push('rgba(' + val + ', ' + alpha + ')');
        });
        return color_array;
    },

    initGraph: function() {

        var _this = this;
        _this.StorageMetricsChart = new Chart(this.$('#metrics-chart'), {
            type: 'horizontalBar',
            data: _this.StorageMetricsChartData,
            options: _this.StorageMetricsChartOptions
        });
    },

    render: function() {

        var _this = this;
        this.constructor.__super__.render.apply(this, arguments);
        $(this.el).html(this.template({
            module_name: this.module_name,
            displayName: this.displayName,
            maximized: this.maximized
        }));
        this.fetch(function() {
            _this.setData();
            _this.updateStorageMetricsChart();
            _this.initGraph();
            this.$('#metrics-legend').html(this.legendTemplate());
            _this.genStorageMetricsChartLegend();
        }, this);
        return this;
    },

    setData: function() {

        var _this = this;
        _this.raw = this.disks.reduce(function(sum, disk) {
            sum += disk.get('size');
            return sum;
        }, 0);
        _this.provisioned = _this.disks.reduce(function(sum, disk) {
            sum = disk.get('pool') != null ? sum + disk.get('size') : sum;
            return sum;
        }, 0);
        _this.free = _this.raw - _this.provisioned;

        _this.pool = _this.pools.reduce(function(sum, pool) {
            sum += pool.get('size');
            return sum;
        }, 0);
        _this.raidOverhead = _this.provisioned - _this.pool;
        _this.share = _.map(_this.shares.groupBy(function(model) {
            return model.get('pool').name;
        }), function(val, key) {
            return {
                pool_name: key,
                pool_size: _.reduce(val, function(v, k) {
                    return k.get('pool').size;
                }, 0),
                shares_size: _.reduce(val, function(v, k) {
                    return v + k.get('size');
                }, 0)
            };
        }).reduce(function(sum, share) {
            sum += share.shares_size < share.pool_size ? share.shares_size : share.pool_size;
            return sum;
        }, 0);
        _this.usage = _this.shares.reduce(function(sum, share) {
            sum += share.get('rusage');
            return sum;
        }, 0);
        _this.sharesfree = _this.share - _this.usage;

        _this.data.push([_this.usage * 1024, _this.pool * 1024, _this.provisioned * 1024]);
        _this.data.push([_this.sharesfree * 1024, _this.raidOverhead * 1024, _this.free * 1024]);

    },

    updateStorageMetricsChart: function() {

        var _this = this;
        _.each(_this.data, function(dataset, index) {
            _this.StorageMetricsChartData.datasets[index].data = dataset;
        });
        _this.StorageMetricsChartOptions.scales.xAxes[0].ticks.max = _.max(_.union(_this.StorageMetricsChartData.datasets[0].data, _this.StorageMetricsChartData.datasets[1].data));
    },

    genStorageMetricsChartLegend: function() {

        var _this = this;
        var dataset = _this.StorageMetricsChartData.datasets;
        _.each(_this.colors, function(color, index) {
            _.each(_.keys(color), function(key, i) {
                var legend = '';
                legend += '<span style="background-color: ' + dataset[index].backgroundColor[i] + '; ';
                legend += 'border-style: solid; border-color: ' + dataset[index].borderColor[i] + '; ';
                legend += 'border-width: 1px; display: inline; width: 10px; height: 10px; float: left; margin: 2px;"></span> ';
                legend += key;
                this.$('#metrics-legend table tr:eq(' + index + ') td:eq(' + i + ')').html(legend);
            });
        });
    },

    resize: function(event) {

        this.constructor.__super__.resize.apply(this, arguments);
        this.StorageMetricsChart.resize();
    }

});

RockStorWidgets.widgetDefs.push({
    name: 'storage_metrics',
    displayName: 'Total Capacity, Allocation and Usage',
    view: 'StorageMetricsWidget',
    description: 'Display capacity and usage',
    defaultWidget: true,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage',
    position: 6
});