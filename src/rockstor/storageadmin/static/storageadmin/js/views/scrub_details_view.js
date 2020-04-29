/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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

ScrubDetailsView = RockstorLayoutView.extend({
    events: {},

    initialize: function () {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        this.pid = this.options.pid;
        this.scrubId = this.options.scrubId;
        this.template = window.JST.pool_poolscrub_details_template;
        this.pool = new Pool({
            pid: this.pid
        });
        // create poolscrub models
        this.poolscrubs = new PoolScrubCollection([], {
            snapType: 'admin'
        });
        // If we experience problems with retrieving the entire scrub history
        // then we should limit the pageSize as follows:
        // this.poolscrubs.pageSize = 50;
        this.poolscrubs.setUrl(this.pid);
        // ensure dependencies
        this.dependencies.push(this.pool);
        this.dependencies.push(this.poolscrubs);
        this.initHandlebarHelpers();
    },

    render: function () {
        this.fetch(this.renderScrubForm, this);
        return this;
    },

    renderScrubForm: function () {
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }
        var pid = this.pid;
        var pool = this.pool;
        // extract the specified scrub via id
        var _this = this;
        var scrub_details = this.poolscrubs.find(function(scrub) {
            return (scrub.get('id') == _this.scrubId)
        });

        $(this.el).html(this.template({
            pool: pool,
            poolName: pool.get('name'),
            scrubStatus: scrub_details.get('status'),
            scrubDetails: scrub_details
        }));
    },

    initHandlebarHelpers: function () {
        var _this = this;

        Handlebars.registerHelper('display_pool_scrub_details_table', function () {
            // Build a table body <tbody> containing the end scrub state
            // PoolScrub model has kb_scrubbed for data_bytes_scrubbed.
            var elements = {"id": "ID",
                "start_time": "Start Time",
                "end_time": "End Time",
                "eta": "ETA",
                "rate": "Scrub Rate",
                "kb_scrubbed": "Data Scrubbed",
                "data_extents_scrubbed": "Data Extents Scrubbed",
                "tree_extents_scrubbed": "Tree Extents Scrubbed",
                "tree_bytes_scrubbed": "Tree Bytes Scrubbed",
                "read_errors": "Read Errors",
                "csum_errors": "Csum Errors",
                "verify_errors": "Verify Errors",
                "no_csum": "No Csum",
                "csum_discards": "Csum Discards",
                "super_errors": "Super Errors",
                "malloc_errors": "Malloc Errors",
                "uncorrectable_errors": "Uncorrectable Errors",
                "unverified_errors": "Unverified Errors",
                "corrected_errors": "Corrected Errors",
                "last_physical": "Last Physical"
            };
            var html = '<tbody>';
            for (var item in elements) {
                html += '<tr>';
                // fill out index column
                html += '<td>' + elements[item] + '</td>';
                // fill out value column
                if (item == 'kb_scrubbed') {
                    html += '<td>';
                    if (this.scrubDetails.get(item)) {
                        html += humanize.filesize(this.scrubDetails.get(item) * 1024);
                    } else {
                        html += 'Not available'
                    }
                    html += '</td>';
                } else if (item == 'start_time' || item == 'end_time' || item == 'eta') {
                    html += '<td>';
                    if (this.scrubDetails.get(item)) {
                        html += moment(this.scrubDetails.get(item)).format(RS_DATE_FORMAT);
                    } else {
                        html += 'Not available'
                    }
                    html += '</td>';
                } else if (item.indexOf('errors') !== -1 && this.scrubDetails.get(item) !== 0) {
                    // item has errors substing and != 0 value so mark as red
                    html += '<td><span style="color:darkred"><strong>';
                    html += this.scrubDetails.get(item);
                    html += '</strong></span></td>';
                } else {
                    html += '<td>' + this.scrubDetails.get(item) + '</td>';
                }
            }
            html += '</tbody>';
            return new Handlebars.SafeString(html);
        });
    }
});
