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

ShareUsageModule = RockstorModuleView.extend({
    events: {
        'click #js-resize': 'edit',
        'click #js-resize-save': 'save',
        'click #js-resize-cancel': 'cancel'
    },

    initialize: function() {
        this.template = window.JST.share_share_usage_module;
        this.editTemplate = window.JST.share_share_usage_edit;
        this.module_name = 'share-usage';
        this.share = this.options.share;
        this.initHandlebarHelpers();
    },

    render: function() {
        $(this.el).html(this.template({
            collection: this.collection,
            module_name: this.module_name,
            share: this.share,
            poolName: this.share.get('pool').name,
            pool_is_mounted: this.share.get('pool').is_mounted,
            pool_mount_status: this.share.get('pool').mount_status,
            pool_quotas_enabled: this.share.get('pool').quotas_enabled,
            share_is_mounted: this.share.get('is_mounted'),
            share_mount_status: this.share.get('mount_status'),
            pid: this.share.get('pool').id,
            shareCreatedDate: moment(this.share.get('toc')).format(RS_DATE_FORMAT)
        }));
        this.renderGraph();
        return this;
    },

    renderBar: function() {
        var _this = this;
        var w = 300;
        var h = 100;
        var padding = [10, 10, 10, 1];
        var barHeight = 50;

        total = parseInt(this.share.get('size') * 1024);
        used = parseInt(this.share.get('rusage') * 1024);
        free = total - used;
        var dataSet = [used, free];
        var data = [Math.round((used / total) * 100), Math.round((free / total) * 100)];
        var dataLabels = ['used', 'free'];
        var colors = {
            used: {
                fill: 'rgb(128,128,128)',
                stroke: 'rgb(221,221,221)'
            },
            free: {
                fill: 'rgb(168,247,171)',
                stroke: 'rgb(221,221,221)'
            },
        };

        var svg = d3.select(this.el).select('#chart')
            .append('svg')
            .attr('width', w + padding[1] + padding[3])
            .attr('height', h + padding[0] + padding[2]);

        var xScale = d3.scale.linear().domain([0, 100]).range([0, w]);
        var xOffset = function(i) {
            return i == 0 ? 0 : xScale(data[i - 1]);
        };

        var gridContainer = svg.append('g')
            .attr('transform', function(d, i) {
                return 'translate(' + padding[3] + ',' + padding[0] + ')';
            });
        gridContainer.selectAll('rect')
            .data(data)
            .enter()
            .append('rect')
            .attr('y', 0)
            .attr('height', barHeight)
            .attr('x', function(d, i) {
                return xOffset(i);
            })
            .attr('width', function(d) {
                return xScale(d);
            })
            .attr('fill', function(d, i) {
                return colors[dataLabels[i]].fill;
            })
            .attr('stroke', function(d, i) {
                return colors[dataLabels[i]].stroke;
            });

        var labels = gridContainer.selectAll('g.labels')
            .data(dataLabels)
            .enter()
            .append('g')
            .attr('transform', function(d, i) {
                return 'translate(0,' + (barHeight + 5 + i * 30) + ')';
            });

        labels.append('rect')
            .attr('width', 13)
            .attr('height', 13)
            .attr('fill', function(d, i) {
                return colors[d].fill;
            })
            .attr('stroke', function(d, i) {
                return colors[d].stroke;
            });

        labels.append('text')
            .attr('text-anchor', 'left')
            .attr('class', 'legend')
            .attr('transform', function(d, i) {
                return 'translate(16,13)';
            })
            .text(function(d, i) {
                return data[i] + '% ' + d + ' - ' + humanize.filesize(dataSet[i]);
            });
    },

    renderGraph: function() {
        var w = 350; //width
        h = 100; //height
        var outerRadius = 20;
        var innerRadius = 0;

        total = parseInt(this.share.get('size') * 1024);
        used = parseInt(this.share.get('rusage') * 1024);
        free = total - used;
        var dataset = [free, used];
        var dataLabels = ['free', 'used'];

        var svg = d3.select(this.el).select('#chart')
            .append('svg')
            .attr('width', w)
            .attr('height', h);

        displayUsagePieChart(svg, outerRadius, innerRadius, w, h, dataset, dataLabels, total);

    },

    edit: function(event) {
        event.preventDefault();
        $(this.el).html(this.editTemplate({
            share: this.share,
            newSizeVal: humanize.filesize(this.share.get('size') * 1024).replace(/[^0-9\.]+/g, '')
        }));
    },

    save: function(event) {
        var _this = this;
        event.preventDefault();
        var button = _this.$('#js-resize-save');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var size = this.$('#new-size').val();

        var sizeFormat = $('#size_format').val();
        if (sizeFormat == 'KB') {
            size = size * 1;
        } else if (sizeFormat == 'MB') {
            size = size * 1024;
        } else if (sizeFormat == 'GB') {
            size = size * 1024 * 1024;
        } else if (sizeFormat == 'TB') {
            size = size * 1024 * 1024 * 1024;
        }
        $.ajax({
            url: '/api/shares/' + this.share.get('id'),
            type: 'PUT',
            dataType: 'json',
            data: {
                'size': size
            },
            success: function() {
                enableButton(button);
                _this.share.fetch({
                    success: function() {
                        _this.render();
                    }
                });
            },
            error: function(request, status, error) {
                enableButton(button);
            }
        });
    },

    cancel: function(event) {
        event.preventDefault();
        this.render();
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_shareResize_units', function() {
            var html = '';
            html += '<option';
            if (humanize.filesize(this.share.get('size') * 1024).match(/KB/g, '')) {
                html += ' selected="selected"';
            }
            html += '>KB</option>';
            html += '<option';
            if (humanize.filesize(this.share.get('size') * 1024).match(/MB/g, '')) {
                html += ' selected="selected"';
            }
            html += '>MB</option>';
            html += '<option ';
            if (humanize.filesize(this.share.get('size') * 1024).match(/GB/g, '')) {
                html += ' selected="selected"';
            }
            html += '>GB</option>';
            html += '<option ';
            if (humanize.filesize(this.share.get('size') * 1024).match(/TB/g, '')) {
                html += ' selected="selected"';
            }
            html += '>TB</option>';
            return new Handlebars.SafeString(html);
        });
    }


});
