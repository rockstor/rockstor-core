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

/*
 * Shares View
 */

SharesView = RockstorLayoutView.extend({
    events: {
        'click a[data-action=delete]': 'deleteShare',
        'click #js-cancel': 'cancel',
        'click #js-confirm-share-delete': 'confirmShareDelete'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);

        this.template = window.JST.share_shares;
        this.shares_table_template = window.JST.share_shares_table;
        this.pools = new PoolCollection();
        this.collection = new ShareCollection();
        this.dependencies.push(this.pools);
        this.dependencies.push(this.collection);
        this.pools.on('reset', this.renderShares, this);
        this.collection.on('reset', this.renderShares, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.renderShares, this);
        return this;
    },

    renderShares: function() {
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }
        if (!this.pools.fetched || !this.collection.fetched) {
            return false;
        }
        $(this.el).html(this.template({
            collection: this.collection,
            pools: this.pools
        }));
        this.$('#shares-table-ph').html(this.shares_table_template({
            collection: this.collection,
            shares: this.collection.toJSON(),
            collectionNotEmpty: !this.collection.isEmpty(),
            pools: this.pools,
            poolsNotEmpty: !this.pools.isEmpty()
        }));

        this.$('[rel=tooltip]').tooltip({placement: 'bottom'});

        var customs = {
            columnDefs: [
                { type: 'file-size', targets: 1 },
                { type: 'file-size', targets: 2 },
                { type: 'file-size', targets: 3 }
            ]
        };

        this.renderDataTables(customs);
    },

//	delete button handler
    deleteShare: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        shareName = button.attr('data-name');
        sid = button.attr('data-id');
        shareUsage = button.attr('data-usage');
		// set share name in confirm dialog
        _this.$('.pass-share-name').html(shareName);
        _this.$('#pass-share-usage').html(shareUsage);
		//show the dialog
        _this.$('#delete-share-modal').modal();
        return false;
    },

    confirmShareDelete: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var url = '/api/shares/' + sid;
        if($('#force-delete').prop('checked')){
            url += '/force';
        }
        $.ajax({
            url: url,
            type: 'DELETE',
            dataType: 'json',
            success: function() {
                _this.collection.fetch({reset: true});
                enableButton(button);
                _this.$('#delete-share-modal').modal('hide');
                $('.modal-backdrop').remove();
                app_router.navigate('shares', {trigger: true});
            },
            error: function(xhr, status, error) {
                enableButton(button);
            }
        });
    },
    cancel: function(event) {
        if (event) event.preventDefault();
        app_router.navigate('shares', {trigger: true});
    },

    initHandlebarHelpers: function(){

        Handlebars.registerHelper('humanize_size', function(num) {
            return humanize.filesize(num * 1024);
        });

        Handlebars.registerHelper('displayCompressionAlgo', function(shareCompression,shareId) {
            var html = '';
            if (shareCompression && shareCompression != 'no') {
                html += shareCompression + ' ';
            } else {
                html += 'Same as Pool ';
            }
            html += '<a href="#shares/' + shareId + '/?cView=edit"' +
                'title="Edit share compression setting" rel="tooltip">' +
                '<i class="glyphicon glyphicon-pencil"></i></a>';
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('isSystemShare', function(id, pool_role) {

            //During Rockstor installation we create first pool with pool_id == 1
            //and root and home shares with id 1 and 2; this let us filter on ids
            //instead of share names
            if (pool_role == 'root' && parseInt(id) < 3) {
                return true;
            }
            return false;
        });

        Handlebars.registerHelper('checkUsage', function(size, btrfs_usage) {

            // We don't have share size enforcement with btrfs qgroup limit
            // but with this we help users to start gettting used to it.
            // Current warning levels are btrfs usage > 70% warning
            // btrfs usage > 80% alert
            var html, warning = '';
            var usage = (btrfs_usage / size).toFixed(4);
            if (usage >= 0.8) {
                warning = 'text-danger';
            } else if (usage >= 0.7){
                warning = 'text-warning';
            }
            if (warning !=='') {
                html = '<i class="fa fa-warning fa-lg ' + warning;
                html += '" title="Usage is ' + usage * 100 + '% of share size">';
                return new Handlebars.SafeString(html);
            }
        });
    }
});
