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
        RockStorSocket.networkWidget = io.connect('/network_widget', {
            'secure': true,
            'force new connection': true
        });
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.dashboard_widgets_network_utilization;
        this.valuesTemplate = window.JST.dashboard_widgets_network_util_values;
        this.InterfacesBuffers = {};
        this.networkInterfaces = new NetworkDeviceCollection();
        this.networkInterfaces.on('reset', this.getInitialData, this);
        this.selectedInterface = null;
        this.numSamples = 180;
        this.colors = ['18, 36, 227', '242, 88, 5', '4, 214, 214', '245, 204, 115'];
        this.netDataFields = ['kb_rx', 'kb_tx', 'packets_rx', 'packets_tx'];
        this.netDataLabels = ['Data rec', 'Data sent', 'Packets rec', 'Packets sent'];

        //Chart.js Network Widget default options
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

        //Ddefine NetworkChart object with options and data structure
        this.NetworkChart = null;

        this.NetworkChartOptions = {
            showLines: true,
            animation: false,
            responsive: true,
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
                        fontSize: 11,
                        labelString: 'Data'
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
                }, {
                    id: 'Packets',
                    position: 'right',
                    scaleLabel: {
                        display: true,
                        fontSize: 11,
                        labelString: 'Packets'
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

        this.NetworkChartData = {
            labels: [],
            datasets: [{
                label: this.netDataLabels[0],
                yAxisID: 'Data',
                backgroundColor: 'rgba(' + this.colors[0] + ', 0.4)',
                borderColor: 'rgba(' + this.colors[0] + ', 1)',
                data: []
            }, {
                label: this.netDataLabels[1],
                yAxisID: 'Data',
                backgroundColor: 'rgba(' + this.colors[1] + ', 0.4)',
                borderColor: 'rgba(' + this.colors[1] + ', 1)',
                data: []
            }, {
                label: this.netDataLabels[2],
                yAxisID: 'Packets',
                backgroundColor: 'rgba(' + this.colors[2] + ', 0.4)',
                borderColor: 'rgba(' + this.colors[2] + ', 1)',
                data: []
            }, {
                label: this.netDataLabels[3],
                yAxisID: 'Packets',
                backgroundColor: 'rgba(' + this.colors[3] + ', 0.4)',
                borderColor: 'rgba(' + this.colors[3] + ', 1)',
                data: []
            }]
        };

    },

    getInitialData: function() {

        var _this = this;
        var niselect = this.$('#interface-select');
        this.networkInterfaces.each(function(ni, i) {
            var opt = $('<option/>');
            opt.val(ni.get('name'));
            opt.text(ni.get('name'));
            if (i == 0) {
                opt.attr({
                    selected: 'selected'
                });
            }
            niselect.append(opt);
        });
        _this.genEmptyNetworkChartData(this.numSamples);
        this.selectedInterface = this.networkInterfaces.at(0).get('name');
        //Create Interfaces Buffers and set initial data to empty vals
        _this.networkInterfaces.each(function(ni) {
            _this.InterfacesBuffers[ni.get('name')] = [];
        });
        _.each(_.keys(_this.InterfacesBuffers), function(d) {
            for (var k = 0; k < _this.numSamples; k++) {
                _this.InterfacesBuffers[d].push(_this.genEmptyDataBuffer());
            }
        });
        _this.InterfacesBuffers.labels = _this.NetworkChartData.labels;
        RockStorSocket.addListener(_this.getData, _this, 'networkWidget:network');
    },

    render: function() {

        var _this = this;
        this.constructor.__super__.render.apply(this, arguments);
        $(this.el).html(this.template({
            module_name: this.module_name,
            displayName: this.displayName,
            maximized: this.maximized
        }));
        if (this.maximized) {
            this.$('#network-util-values-ph').html(this.valuesTemplate());
        }
        this.$('#interface-select').change(function(event) {
            _this.selectedInterface = $(event.currentTarget).val();
        });
        _this.networkInterfaces.fetch();
        return this;
    },

    getData: function(data) {

        var _this = this;
        if (!_this.graphRendered) {
            _this.initGraphs();
            _this.graphRendered = true;
        }

        _.each(data.results, function(d, index) {
            _this.InterfacesBuffers[d.device].shift();
            _this.InterfacesBuffers[d.device].push(d);
        });

        var interfaceBuffer = _this.InterfacesBuffers[_this.selectedInterface];
        _this.updateNetworkChart(interfaceBuffer);

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

    updateNetworkChart: function(interfaceBuffer) {

        var _this = this;
        var newData = _this.clearInterfaceData(interfaceBuffer);
        _.each(newData, function(val, i) {
            _this.NetworkChartData.datasets[i].data = newData[i];
        });

        var currentData = null;
        if (interfaceBuffer.length > 0) {
            currentData = interfaceBuffer[interfaceBuffer.length - 1];
        }

        _this.InterfacesBuffers.labels.shift();
        var csecs = moment(currentData.ts).format('s');
        var label = '';
        if (csecs % 60 === 0) {
            label = csecs == '0' ? moment(currentData.ts).format('HH:mm') : moment(currentData.ts).format(':ss');
        }
        _this.InterfacesBuffers.labels.push(label);
        _this.NetworkChartData.labels = _this.InterfacesBuffers.labels;
        _this.NetworkChart.update();

        if (this.maximized) {
            this.$('#data-rec').html(humanize.filesize(currentData['kb_rx']));
            this.$('#packets-rec').html(currentData['packets_rx']);
            this.$('#errors-rec').html(currentData['errs_rx']);
            this.$('#drop-rec').html(currentData['drop_rx']);
            this.$('#data-sent').html(humanize.filesize(currentData['kb_tx']));
            this.$('#packets-sent').html(currentData['packets_tx']);
            this.$('#errors-sent').html(currentData['errs_tx']);
            this.$('#drop-sent').html(currentData['drop_tx']);
        }
    },

    clearInterfaceData: function(interfaceBuffer) {
        var _this = this;
        var new_data = [];
        var kb_rx = [];
        var kb_tx = [];
        var packets_rx = [];
        var packets_tx = [];
        _.each(interfaceBuffer, function(d, i) {
            kb_rx.push(d['kb_rx']);
            kb_tx.push(d['kb_tx']);
            packets_rx.push(d['packets_rx']);
            packets_tx.push(d['packets_tx']);
        });

        new_data.push(kb_rx);
        new_data.push(kb_tx);
        new_data.push(packets_rx);
        new_data.push(packets_tx);

        return new_data;
    },

    genEmptyNetworkChartData: function(numSamples) {

        var _this = this;
        //Create initial empty data required to have line chart right alligned
        for (var i = 0; i < numSamples; i++) {
            _this.NetworkChartData.labels.push('');
            for (var x = 0; x < _this.NetworkChartData.datasets.length; x++) {
                _this.NetworkChartData.datasets[x].data.push(null);
            }
        }
    },

    genNetworkChartLegend: function() {

        var _this = this;
        var legend = '<ul style="list-style-type: none; display: inline;">';
        _.each(_this.NetworkChartData.datasets, function(dataset, index) {
            legend += '<li style="float: left;"><span style="background-color: ' + dataset.backgroundColor + '; ';
            legend += 'border-style: solid; border-color: ' + dataset.borderColor + '; ';
            legend += 'border-width: 1px; display: inline; width: 10px; height: 10px; float: left; margin: 2px;"></span>';
            legend += dataset.label + '</li>';
            if (index == 1) {
                legend += '<br/>';
            }
        });
        legend += '</ul>';
        return legend;
    },

    genEmptyDataBuffer: function() {

        return {
            'id': 0,
            'kb_rx': null,
            'packets_rx': null,
            'errs_rx': 0,
            'drop_rx': 0,
            'fifo_rx': 0,
            'frame': 0,
            'compressed_rx': 0,
            'multicast_rx': 0,
            'kb_tx': null,
            'packets_tx': null,
            'errs_tx': 0,
            'drop_tx': 0,
            'fifo_tx': 0,
            'colls': 0,
            'carrier': 0,
            'compressed_tx': 0,
            'ts': ''
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