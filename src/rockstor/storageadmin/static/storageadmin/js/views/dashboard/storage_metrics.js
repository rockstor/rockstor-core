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
        // svg
        this.svgEl = '#ph-metrics-viz';
        this.svgLegendEl = '#ph-metrics-legend';
        // Metrics
        this.raw = 0; // raw storage capacity in GB
        this.allocated = 0;
        this.free = 0;
        this.poolCapacity = 0;
        this.usage = 0;
        this.margin = {top: 0, right: 40, bottom: 20, left: 30};
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

		this.StorageMetricsChart = null;
        this.StorageMetricsChartOptions = {
            title: {
                display: false,
            },
            showLines: false,
            legend: {
                display: false,
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
					stacked: true,
                    ticks: {
                        fontSize: 9,
						minRotation: 60
                        },
                    gridLines: {
                        display: false,
                        zeroLineWidth: 0,
                        drawTicks: true,
                        padding: 0
                    }
                }],
                xAxes: [{
					stacked: true,
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

		this.StorageMetricsChartData = {
			labels: ['Shares', 'Pools', 'Disks'],
			datasets:[{
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
		_.each(_this.colors[index], function(val){
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
        // call render of base
        this.constructor.__super__.render.apply(this, arguments);
        $(this.el).html(this.template({
            module_name: this.module_name,
            displayName: this.displayName,
            maximized: this.maximized
        }));
        this.fetch(function() {
            _this.setData();
            _this.setDimensions();
            _this.setupSvg();
            _this.renderMetrics();
        }, this);
        return this;
    },

    setData: function() {

		var _this = this;
		console.log(_this.StorageMetricsChartData);
        var gb = 1024*1024;
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
        _this.pctUsed = parseFloat(((_this.usage/_this.raw).toFixed(0)) * 100);

        _this.data = [
            {name: 'used', label: 'Usage', value: _this.usage},
            {name: 'pool', label: 'Pool Capacity', value: _this.poolCapacity},
            {name: 'raw', label: 'Raw Capacity', value: _this.raw}
        ];

        _this.data1 = [
            { name: 'share', label: 'Share Capacity', value: _this.share },
            { name: 'pool-provisioned', label: 'Provisioned', value: _this.provisioned },
            { name: 'raw', label: 'Raw Capacity', value: _this.raw },
        ];

        _this.data2 = [
            { name: 'usage', label: 'Usage', value: _this.usage},
            { name: 'pool', label: 'Pool Capacity', value: _this.pool },
            { name: 'provisioned', label: 'Provisioned', value: _this.provisioned },
        ];
		_this.updateStorageMetricsChart();
		_this.initGraph();

    },

	updateStorageMetricsChart: function() {
		var _this = this;
		_this.StorageMetricsChartData.datasets[0].data.push(_this.usage*1024, _this.pool*1024, _this.provisioned*1024);
		_this.StorageMetricsChartData.datasets[1].data.push(_this.sharesfree*1024, _this.raidOverhead*1024, _this.free*1024);
		_this.StorageMetricsChartOptions.scales.xAxes[0].ticks.max = _.max(_.union(_this.StorageMetricsChartData.datasets[0].data, _this.StorageMetricsChartData.datasets[1].data));
	},
	
    setDimensions: function() {

		var _this = this;
        //this.graphWidth = this.maximized ? 500 : 250;
        //this.graphHeight = this.maximized ? 300 : 150;
        _this.barPadding = _this.maximized ? 40 : 20;
        _this.barWidth = _this.maximized ? 400 : 200;
        if (_this.maximized) {
            _this.width = 500 - _this.margin.left - _this.margin.right;
            _this.height = 500 - _this.margin.top - _this.margin.bottom;
        } else {
            _this.width = 250 - _this.margin.left - _this.margin.right;
            _this.height = 190 - _this.margin.top - _this.margin.bottom;
        }
        _this.x = d3.scale.linear().domain([0,_this.raw]).range([0, _this.width]);
        _this.y = d3.scale.linear().domain([0, _this.data1.length]).range([0, _this.height]);
        _this.barHeight = (_this.height / _this.data1.length );
    },

    setupSvg: function() {
        // svg for viz
        this.$(this.svgEl).empty();
        this.svg = d3.select(this.el).select(this.svgEl)
            .append('svg')
            .attr('class', 'metrics')
            .attr('width', this.width + this.margin.left + this.margin.right)
            .attr('height', this.height + this.margin.top + this.margin.bottom);
        this.svgG = this.svg.append("g")
            .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");

        // svg for legend
        this.$(this.svgLegendEl).empty();
        this.svgLegend = d3.select(this.el).select(this.svgLegendEl)
            .append('svg')
            .attr('class', 'metrics-legend')
            .attr('width', this.width + this.margin.left + this.margin.right)
            .attr('height', 80);
    },

    renderMetrics: function() {
        var _this = this;

        // tickValues(this.x.domain()) sets tick values at beginning and end of the scale
        this.xAxis = d3.svg.axis().scale(this.x).orient('bottom').tickValues(_this.x.domain()).tickFormat(function(d) {
            return humanize.filesize(d*1024);
        });
        this.yAxis = d3.svg.axis().scale(this.y).orient('left').tickValues([0,1,2]).tickFormat(function(d) {
            if (d==0) {
                return 'Shares';
            } else if (d==1) {
                return 'Pools';
            } else if (d==2) {
                return 'Disks';
            }
        });

        this.svgG.append("g")
            .attr("class", "metrics-axis")
            .attr("transform", "translate(0," + _this.height + ")")
            .call(this.xAxis);

        // render data1
        this.svgG.selectAll('metrics-rect1')
            .data(this.data1)
            .enter()
            .append('rect')
            .attr('class', function(d) {
                return d.name;
            })
            .attr('x',0)
            .attr('y', function(d,i) {
                //return _this.y(i) + _this.barHeight/2 + _this.barPadding;
                return _this.y(i);
            })
            .attr('width', function(d) { return _this.x(d.value); })
            .attr('height', function() { return _this.barHeight-4; });

        // render data2
        this.svgG.selectAll('metrics-rect2')
            .data(this.data2)
            .enter()
            .append('rect')
            .attr('class', function(d) {
                return d.name;
            })
            .attr('x',0)
            .attr('y', function(d,i) {
                return _this.y(i);
            })
            .attr('width', function(d) { return _this.x(d.value); })
            .attr('height', function() { return _this.barHeight-4; });

        // text labels
        this.svgG.selectAll('metrics-text-data1')
            .data(this.data1)
            .enter()
            .append('text')
            .attr("class", "metrics-text-data1")
            .attr('x', function(d){
                var xOff = _this.x(d.value) - 4;
                return (xOff > 0 ? xOff : 0);
            })
            .attr('y', function(d,i) {
                return _this.y(i) + 12;
            })
            .style('text-anchor', function(d) {
                var xOff = _this.x(d.value) - 4;
                return (xOff > 30 ?  'end' : 'start');
            })
            .text(function(d,i) {
                //return humanize.filesize(d.value*1024);
                var tmp = d.value - _this.data2[i].value;
                var pct = (tmp/d.value) * 100;
                return humanize.filesize(tmp*1024);
            });

        // text labels
        this.svgG.selectAll('metrics-text-data2')
            .data(this.data2)
            .enter()
            .append('text')
            .attr("class", "metrics-text-data1")
            .attr('x', function(d){
                return 4;
            })
            .attr('y', function(d,i) {
                return _this.y(i) + _this.barHeight - 12;
            })
            .style('text-anchor', function(d) {
                return 'start';
            })
            .text(function(d,i) {
                var pct = (d.value/_this.data1[i].value)*100;
                return humanize.filesize(d.value*1024) + ' (' + pct.toFixed() + '%)';
            });

        this.gDisk = this.svgLegend.append('g')
            .attr('class', 'metrics-disk-legend');

        var diskLabelData = [
            {label: 'Provisioned', fill: '#91BFF2'},
            {label: 'Free', fill: '#E4EDF7'},
        ];

        var poolLabelData = [
            {label: 'Capacity', fill: '#0BD6E3'},
            {label: 'Raid overhead', fill: '#B0F1F5'},
        ];

        var shareLabelData = [
            {label: 'Capacity', fill: '#FAE8CA'},
            {label: 'Used', fill: '#FAC670'},
        ];

        var diskLabels = this.gDisk.selectAll('legend-disk')
            .data(diskLabelData)
            .enter();

        var diskLabelG = diskLabels.append('g')
            .attr("transform", function(d,i) {
                return "translate(0, " + (i*14) + ")";
            });

        diskLabelG.append("rect")
            .attr("width", 13)
            .attr("height", 13)
            .attr("fill", function(d) { return d.fill;});

        diskLabelG.append("text")
            .attr("text-anchor", "left")
            .attr("class", "metrics-legend-text")
            .attr("transform", function(d,i) {
                return "translate(16,12)";
            })
            .text(function(d) { return d.label;});

        var poolLabels = this.gDisk.selectAll('legend-pool')
            .data(poolLabelData)
            .enter();

        var poolLabelG = poolLabels.append('g')
            .attr("transform", function(d,i) {
                return "translate(75, " + (i*14) + ")";
            });

        poolLabelG.append("rect")
            .attr("width", 13)
            .attr("height", 13)
            .attr("fill", function(d) { return d.fill;});

        poolLabelG.append("text")
            .attr("text-anchor", "left")
            .attr("class", "metrics-legend-text")
            .attr("transform", function(d,i) {
                return "translate(16,12)";
            })
            .text(function(d) { return d.label;});

        var shareLabels = this.gDisk.selectAll('legend-share')
            .data(shareLabelData)
            .enter();

        var shareLabelG = shareLabels.append('g')
            .attr("transform", function(d,i) {
                return "translate(160, " + (i*14) + ")";
            });

        shareLabelG.append("rect")
            .attr("width", 13)
            .attr("height", 13)
            .attr("fill", function(d) { return d.fill;});

        shareLabelG.append("text")
            .attr("text-anchor", "left")
            .attr("class", "metrics-legend-text")
            .attr("transform", function(d,i) {
                return "translate(16,12)"
            })
            .text(function(d) { return d.label;});

        // draw y axis last so that it is above all rects
        this.svgG.append("g")
            .attr("class", "metrics-axis")
            .call(this.yAxis)
            .selectAll("text")
            .style("text-anchor", "end")
            .attr("transform", function(d) {
                return "rotate(-90)";
            })
            .attr("dx", "-.4em")
            .attr("dy", "-.30em");

    },

    resize: function(event) {
        this.constructor.__super__.resize.apply(this, arguments);
        this.setDimensions();
        this.setupSvg();
        this.renderMetrics();
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
