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

PoolRebalanceTableModule = RockstorModuleView.extend({
    events: {
        'click #js-poolrebalance-start': 'start',
        'click #js-poolrebalance-cancel': 'cancel'
    },

    initialize: function() {
        this.template = window.JST.pool_poolrebalance_table_template;
        this.startRebalanceTemplate = window.JST.pool_poolrebalance_start_template;
        this.module_name = 'poolrebalances';
        this.pool = this.options.pool;
        this.poolrebalances = this.options.poolrebalances;
        this.collection = this.options.poolrebalances;
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
        $(this.el).html(this.startRebalanceTemplate({
            pool: this.pool
        }));

        this.validator = this.$('#pool-rebalance-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {},
            submitHandler: function() {
                var button = _this.$('#start_rebalance');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var n = _this.$('#forcebalance:checked').val();
                var postdata = '';
                if (n == 'on') {
                    postdata = '{"force": "true"}';
                }
                $.ajax({
                    url: '/api/pools/' + _this.pool.get('id') + '/balance',
                    type: 'POST',
                    contentType: 'application/json',
                    data: postdata,
                    success: function() {
                        _this.$('#pool-rebalance-form :input').tooltip('hide');
                        enableButton(button);
                        _this.collection.fetch({
                            success: function(collection, response, options) {}
                        });
                    },
                    error: function(jqXHR) {
                        _this.$('#pool-rebalance-form :input').tooltip('hide');
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

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_poolRebalance_table', function() {
            var html = '';
            this.collection.each(function(poolrebalance, index) {
                html += '<tr>';
                html += '<td>' + poolrebalance.get('id') + '</td>';
                html += '<td>' + poolrebalance.get('status') + '</td>';
                html += '<td>';
                internal_balance = poolrebalance.get('internal');
                percent_done = poolrebalance.get('percent_done')
                if (internal_balance) {
                    html += 'Disk Removal'
                } else {
                    html += 'Regular'
                }
                html += '</td>';
                html += '<td>';
                if (poolrebalance.get('start_time')) {
                    html += moment(poolrebalance.get('start_time')).format(RS_DATE_FORMAT);
                }
                html += '</td>';
                // html += '<td>';
                // if (poolrebalance.get('end_time')) {
                //     html += moment(poolrebalance.get('end_time')).format(RS_DATE_FORMAT);
                // }
                // html += '</td>';
                html += '<td>';
                if (percent_done != 100 && internal_balance) {
                    html += 'unavailable';
                } else {
                    html += percent_done;
                }
                html + '</td>';
                html += '<td>';
                if (poolrebalance.get('message') != null) {
                    html += poolrebalance.get('message');
                }
                html += '</td>';
                html += '</tr>';
            });
            return new Handlebars.SafeString(html);
        });

    }

});
