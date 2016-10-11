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

		this.numTop = this.maximized ? 5 : 3;
        this.dataLength = 300;
        this.Disksfields = ['ms_ios', 'sectors_written', 'writes_completed', 'ms_writing', 'ms_reading', 'reads_completed', 'sectors_read'];
        this.Diskslabels = ['ms on I/Os', 'kB written', 'Writes', 'ms writing', 'ms reading', 'Reads', 'kB read'];
        this.TopDiskscolors = ['242, 0, 0', '36, 229, 84', '41, 108, 232', '232, 200, 41', '146, 41, 232']
        this.SingleDiskcolors = ['7, 233, 7', '21, 124, 217', '255, 184, 7', '255, 25, 7']
		
        // disks data is a map of diskname to array of values of length
        // dataLength
        // each value is of the format of the data returned by the api
        // see genEmptyDiskData for an example of this format
        this.disksData = {};
        this.disks = new DiskCollection();
        this.disks.pageSize = RockStorGlobals.maxPageSize;

        this.topDisks = [];
        this.selectedDisk = null;

        this.sortAttrs = ['reads_completed']; // attrs to sort by

		this.SingleDiskChart = null;	
        this.SingleDiskChartOptions = {
            animation: false,
            responsive: true,
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
                    id: 'IOs',
                    position: 'left',
                    scaleLabel: {
                        display: false
                    },
                    ticks: {
                        fontSize: 9,
                        beginAtZero: true,
                        min: 0
                    },
                    gridLines: {
                        drawTicks: true
                    }
                }, {
                    id: 'Data',
                    position: 'right',
                    scaleLabel: {
                        display: false
                    },
                    ticks: {
                        fontSize: 9,
                        beginAtZero: true,
                        min: 0,
                        callback: function(value) {
                            return humanize.filesize(value);
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
		this.SingleDiskChartData = {
			labels: [],
			datasets: [{
                label: this.Diskslabels[5],
				yAxisID: 'IOs',
                backgroundColor: 'rgba(' + this.SingleDiskcolors[0] + ', 0.4)',
                borderColor: 'rgba(' + this.SingleDiskcolors[0] + ', 1)',
                data: []
            }, {
                label: this.Diskslabels[2],
				yAxisID: 'IOs',
                backgroundColor: 'rgba(' + this.SingleDiskcolors[1] + ', 0.4)',
                borderColor: 'rgba(' + this.SingleDiskcolors[1] + ', 1)',
                data: []
            }, {
                label: this.Diskslabels[6],
				yAxisID: 'Data',
                backgroundColor: 'rgba(' + this.SingleDiskcolors[2] + ', 0.4)',
                borderColor: 'rgba(' + this.SingleDiskcolors[2] + ', 1)',
                data: []
            }, {
                label: this.Diskslabels[1],
				yAxisID: 'Data',
                backgroundColor: 'rgba(' + this.SingleDiskcolors[3] + ', 0.4)',
                borderColor: 'rgba(' + this.SingleDiskcolors[3] + ', 1)',
                data: []
            }]
		}

        this.TopDisksChart = null;
        this.TopDisksChartOptions = {
            animation: {
                duration: 1500,
                easing: 'linear'
            },
            responsive: true,
                        legend: {
                display: true,
                position: 'bottom',
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

		this.initHandlebarHelpers();
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
                _this.initTopDisksData();
				_this.initSingleDiskData();
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

    initTopDisksData: function() {

        var _this = this;
		var num_disks = Object.keys(_this.disksData).length < _this.numTop ? Object.keys(_this.disksData).length : _this.numTop;
        for (var i = 0; i < num_disks; i++) {
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
	
	initSingleDiskData: function() {

		var _this = this;
		for (var i= 0; i < _this.dataLength; i++) {
			_.each(_this.SingleDiskChartData.datasets, function(dataset) {
				dataset.data.push(null);
			});
			_this.SingleDiskChartData.labels.push('');
		}
	},

    getData: function(data) {

        var _this = this;
        _this.update(data);
    },

    update: function(data) {

		var _this = this;
        _this.updateDisksData(data);
        _this.sortDisks();

        if (!_this.TopDisksgraphRendered) {
            _this.initTopDisksGraph();
            _this.TopDisksgraphRendered = true;
        }
        _this.updateTopDisksChart();

        if (_this.maximized) {
			if (!_this.SingleDiskgraphRendered) {
				_this.initSingleDiskGraph();
				_this.SingleDiskgraphRendered = true;
			}
			_this.updateSingleDiskChart();
		}
    },

    initTopDisksGraph: function() {

        var _this = this;
        _this.TopDisksChart = new Chart(this.$('#top-disks-chart'), {
            type: 'radar',
            data: _this.TopDisksChartData,
            options: _this.TopDisksChartOptions
        });
    },
	
	initSingleDiskGraph: function() {

        var _this = this;
        _this.SingleDiskChart = new Chart(this.$('#single-disk-chart'), {
            type: 'line',
            data: _this.SingleDiskChartData,
            options: _this.SingleDiskChartOptions
        });
	},
    
    updateTopDisksChart: function() {

        var _this = this;
        //If avail disks < numTop, use only avail disks
        var num_disks = Object.keys(_this.disksData).length < _this.numTop ? Object.keys(_this.disksData).length : _this.numTop;
        for (var i=0; i < num_disks; i++) {
            var data = [];
            _.each(_this.Disksfields, function(field) {
                data.push(_this.normalizeData(field, _this.topDisks[i][field]));
            });
            _this.TopDisksChartData.datasets[i].data = data;
            _this.TopDisksChartData.datasets[i].label = _this.topDisks[i].name;
        }
        _this.TopDisksChart.update();
    },
	
	updateSingleDiskChart: function() {

		var _this = this;
        if (!_this.selectedDisk) {
            if (_this.topDisks.length > 0) {
                _this.selectedDisk = _this.topDisks[0].name;
            } else {
                _this.selectedDisk = _this.disks.at(0).get('name');
            }
            this.$('#disk-select').val(_this.selectedDisk);
        }
		var current_disk = _this.disksData[_this.selectedDisk];
		var singlediskdata = {
			reads_completed: [],
			writes_completed: [],
			sectors_read: [],
			sectors_written: [],
		};
		var singledisklabels = [];
		
        for (var i = 0; i < _this.dataLength; i++) {
			_.each(singlediskdata, function(dataval, datakey) {
				var multiplier = datakey.indexOf('sectors') > -1 ? 512 : 1;
				singlediskdata[datakey].push(current_disk[i][datakey] * multiplier);
			});
			var csecs = moment(current_disk[i].ts).format('s');
			var label = '';
			if (csecs % 30 === 0) {
				label = csecs == '0' ? moment(current_disk[i].ts).format('HH:mm') : moment(current_disk[i].ts).format(':ss');
			}
			singledisklabels.push(label);
        }
		_.each(_.values(singlediskdata), function(val, index) {
			_this.SingleDiskChartData.datasets[index].data = val;
		});
		_this.SingleDiskChartData.labels = singledisklabels;
		_this.SingleDiskChart.update();
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
            "ts": ''
        };
    },

    resize: function(event) {

        var _this = this;
        this.constructor.__super__.resize.apply(this, arguments);
        // maximum number of top disks to display
        this.numTop = this.maximized ? 5 : 3;
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
        _this.TopDisksChart.resize();
    },

    cleanup: function() {
        RockStorSocket.removeOneListener('diskWidget');
    },

	initHandlebarHelpers: function(){
		Handlebars.registerHelper('getAdminUsers', function(adminUsers){
			var html = '';
			var userNames = _.reduce(adminUsers, function(s, user, i, list) {
				if (i < (list.length-1)) {
					return s + user.username + ',';
				} else{
					return s + user.username;
				}
			}, '');
			if(userNames.length != 0){
				html += userNames;
			}else {
				html += '&nbsp;--';
			}
			return new Handlebars.SafeString(html);
		});
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
