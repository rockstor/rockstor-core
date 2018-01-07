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

ReplicaTrailsView = RockstorLayoutView.extend({
    events: {},

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        // set template
        this.template = window.JST.replication_replica_trails;
        // add dependencies
        this.replicaId = this.options.replicaId;
        this.replica = new Replica({
            id: this.replicaId
        });
        this.dependencies.push(this.replica);
        this.collection = new ReplicaTrailCollection(null, {
            replicaId: this.replicaId
        });
        this.dependencies.push(this.collection);
        this.collection.on('reset', this.renderReplicaTrails, this);
        // has the replica been fetched? prevents renderReplicaTrails executing
        // (because of collection reset) before replica has been fetched
        this.replicaFetched = false;
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.firstFetch, this);
        return this;
    },

    firstFetch: function() {
        this.replicaFetched = true;
        this.renderReplicaTrails();
    },

    renderReplicaTrails: function() {
        if (!this.replicaFetched) return false;
        var _this = this;
        $(this.el).html(this.template({
            replica: _this.replica.toJSON(),
            replicaColl: _this.collection.toJSON(),
            collection: _this.collection,
            collectionNotEmpty: !this.collection.isEmpty()
        }));
        // remove existing tooltips
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }
        this.$('[rel=tooltip]').tooltip({
            placement: 'bottom'
        });
        //Added columns definition for sorting purpose
        var customs = {
            'iDisplayLength': 15,
            'aLengthMenu': [
                [15, 30, 45, -1],
                [15, 30, 45, 'All']
            ],
            'order': [[0, 'desc']],
            'columns': [
                null, null, null, null, null, null,
                {
                    'orderDataType': 'dom-checkbox'
                }
            ]
        };
        this.renderDataTables(customs);
    },

    initHandlebarHelpers: function() {

        Handlebars.registerHelper('getDateFormat', function(date) {
            return moment(date).format(RS_DATE_FORMAT);
        });

        Handlebars.registerHelper('ifStatusSuccess', function(status, opts) {
            if (status != 'failed') {
                return opts.fn(this);
            }
            return opts.inverse(this);
        });

        Handlebars.registerHelper('getDuration', function(endTime, startTime) {
            return moment(endTime).from(moment(startTime));
        });

        Handlebars.registerHelper('humanReadableSize', function(size) {
            if (size === 0){
                return '0 or < 1KB'
            } else {
                return humanize.filesize(size * 1024);
            }
        });

        Handlebars.registerHelper('getRate', function(endTime, startTime, kbSent) {
            if (kbSent === 0) return 'N/A'
            var d;
            if (endTime != null) {
                d = moment(endTime).diff(moment(startTime)) / 1000;
            } else {
                d = moment().diff(moment(startTime)) / 1000;
            }
            return humanize.filesize((kbSent / d).toFixed(2) * 1024);
        });
    }


});
