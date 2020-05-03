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

PoolScrubTableModule = RockstorModuleView.extend({
    events: {
        'click #js-poolscrub-start': 'start',
        'click #js-poolscrub-cancel': 'cancel'
    },

    initialize: function() {
        this.template = window.JST.pool_poolscrub_table_template;
        this.startScrubTemplate = window.JST.pool_poolscrub_start_template;
        this.module_name = 'poolscrubs';
        this.pool = this.options.pool;
        this.poolscrubs = this.options.poolscrubs;
        this.collection = this.options.poolscrubs;
        this.collection.on('reset', this.render, this);
        this.parentView = this.options.parentView;
        this.initHandlebarHelpers();
    },

    render: function() {
        var _this = this;
        $(this.el).empty();
        $(this.el).append(this.template({
            collection: this.collection,
            collectionNotEmpty: !this.collection.isEmpty(),
            pool: this.pool
        }));
        this.$('[rel=tooltip]').tooltip({
            placement: 'bottom'
        });
        return this;
    },

    setPoolName: function(poolName) {
        this.collection.setUrl(poolName);
    },

    start: function(event) {
        var _this = this;
        event.preventDefault();
        $(this.el).html(this.startScrubTemplate({
            pool: this.pool
        }));

        this.validator = this.$('#pool-scrub-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {},
            submitHandler: function() {
                var button = _this.$('#start_scrub');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var n = _this.$('#forcescrub:checked').val();
                var postdata = '';
                if (n == 'on') {
                    postdata = '{"force": "true"}';
                }
                $.ajax({
                    url: '/api/pools/' + _this.pool.get('id') + '/scrub',
                    type: 'POST',
                    contentType: 'application/json',
                    data: postdata,
                    success: function() {
                        _this.$('#pool-scrub-form :input').tooltip('hide');
                        enableButton(button);
                        _this.collection.fetch({
                            success: function(collection, response, options) {}
                        });
                    },
                    error: function(jqXHR) {
                        _this.$('#pool-scrub-form :input').tooltip('hide');
                        enableButton(button);
                    }
                });
                return false;
            }
        });
    },

    cancel: function(event) {
        event.preventDefault();
        this.render();
    },

    initHandlebarHelpers: function () {
        Handlebars.registerHelper('display_poolScrub_table', function () {
            var _this = this;
            var html = '';
            var errorStats = ['read_errors', 'csum_errors', 'verify_errors',
                'super_errors', 'malloc_errors', 'uncorrectable_errors',
                'unverified_errors', 'corrected_errors'];
            var errorStatsLen = errorStats.length;
            this.collection.each(function (poolscrub, index) {
                var errorMarks = '';
                // Tally number of non zero error stats
                // (no forEach available in Handlebars helper context.)
                for (var i = 0; i < errorStatsLen; i++) {
                    if (poolscrub.get(errorStats[i]) !== 0) {
                        errorMarks += '!';
                    }
                }
                html += '<tr>';
                html += '<td>' + poolscrub.get('id') + '</td>';
                // construct our href as pools/pid/scrubId for Scrub Details.
                html += '<td><a href="#pools/' + _this.pool.get('id') + '/';
                html += poolscrub.get('id') + '">';
                html += poolscrub.get('status') + '</a>';
                if (errorMarks !== '') {
                    html += '<span style="color:darkred"><strong>';
                    html += ' ' + 'ERRORS FOUND' + errorMarks;
                    html += '</strong></span>';
                }
                html += '</td>';
                html += '<td>';
                if (poolscrub.get('start_time')) {
                    html += moment(poolscrub.get('start_time')).format(RS_DATE_FORMAT);
                }
                html += '</td>';
                html += '<td>';
                if (poolscrub.get('end_time')) {
                    html += moment(poolscrub.get('end_time')).format(RS_DATE_FORMAT);
                } else if (poolscrub.get('eta')) {
                    html += 'ETA: ' + moment(poolscrub.get('eta')).format(RS_DATE_FORMAT);
                }
                html += '</td>';
                html += '<td>' + humanize.filesize(poolscrub.get('kb_scrubbed') * 1024) + '</td>';
                html += '<td>';
                if (poolscrub.get('rate')) {
                    html += poolscrub.get('rate');
                } else {
                    html += 'N/A';
                }
                html += '</td>';
                html += '</tr>';
            });

            return new Handlebars.SafeString(html);
        });
    }

});
