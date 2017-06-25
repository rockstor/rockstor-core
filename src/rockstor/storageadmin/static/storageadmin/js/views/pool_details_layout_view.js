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

PoolDetailsLayoutView = RockstorLayoutView.extend({

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        this.pid = this.options.pid;
        this.cView = this.options.cView;
        this.template = window.JST.pool_pool_details_layout;
        this.resize_pool_info_template = window.JST.pool_resize_pool_info;
        this.compression_info_template = window.JST.pool_compression_info;
        this.pool = new Pool({
            pid: this.pid
        });
        // create poolscrub models
        this.poolscrubs = new PoolScrubCollection([], {
            snapType: 'admin'
        });
        this.poolscrubs.pageSize = 5;
        this.poolscrubs.setUrl(this.pid);
        // create pool re-balance models
        this.poolrebalances = new PoolRebalanceCollection([], {
            snapType: 'admin'
        });
        this.poolrebalances.pageSize = 5;
        this.poolrebalances.setUrl(this.pid);

        this.dependencies.push(this.pool);
        this.dependencies.push(this.poolscrubs);
        this.dependencies.push(this.poolrebalances);
        this.disks = new DiskCollection();
        this.disks.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.disks);
        this.cOpts = {
            'no': 'Dont enable compression',
            'zlib': 'zlib',
            'lzo': 'lzo'
        };
        this.initHandlebarHelpers();
        this.poolShares = new PoolShareCollection([], {
            pid: this.pid
        });
    },

    events: {
        'click #delete-pool': 'deletePool',
        'click #js-confirm-pool-delete': 'confirmPoolDelete',
        'click #js-resize-pool': 'resizePool',
        'click #js-submit-resize': 'resizePoolSubmit',
        'click #js-resize-cancel': 'resizePoolCancel'
    },

    render: function() {
        this.poolShares.fetch();
        this.fetch(this.renderSubViews, this);
        return this;
    },

    renderSubViews: function() {
        var poolRoleIsRoot = false;
        if (this.pool.get('role') == 'root') {
            poolRoleIsRoot = true;
        }
        $(this.el).html(this.template({
            share: this.poolShares.models[0].attributes.results,
            poolName: this.pool.get('name'),
            isPoolRoleRoot: poolRoleIsRoot
        }));

        this.subviews['pool-info'] = new PoolInfoModule({
            model: this.pool.toJSON()
        });
        this.subviews['pool-usage'] = new PoolUsageModule({
            model: this.pool
        });
        this.subviews['pool-scrubs'] = new PoolScrubTableModule({
            poolscrubs: this.poolscrubs,
            pool: this.pool,
            parentView: this
        });
        this.subviews['pool-rebalances'] = new PoolRebalanceTableModule({
            poolrebalances: this.poolrebalances,
            pool: this.pool,
            parentView: this
        });
        this.pool.on('change', this.subviews['pool-info'].render, this.subviews['pool-info']);
        this.pool.on('change', this.subviews['pool-usage'].render, this.subviews['pool-usage']);
        this.poolscrubs.on('change', this.subviews['pool-scrubs'].render, this.subviews['pool-scrubs']);
        this.$('#ph-pool-info').html(this.subviews['pool-info'].render().el);
        this.$('#ph-pool-usage').html(this.subviews['pool-usage'].render().el);
        this.$('#ph-pool-scrubs').html(this.subviews['pool-scrubs'].render().el);
        this.$('#ph-pool-rebalances').html(this.subviews['pool-rebalances'].render().el);
        this.renderDataTables();


        this.$('#ph-compression-info').html(this.compression_info_template({
            pool: this.pool.toJSON()
        }));

        this.$('#ph-resize-pool-info').html(
            this.resize_pool_info_template({
                pool: this.pool.toJSON()
            })
        );
        this.$('ul.nav.nav-tabs').tabs('div.css-panes > div');
        if (!_.isUndefined(this.cView) && this.cView == 'resize') {
            // scroll to resize section
            $('#content').scrollTop($('#ph-resize-pool-info').offset().top);
        }

        //$('#pool-resize-raid-modal').modal({show: false});
        $('#pool-resize-raid-overlay').overlay({
            load: false
        });

        //Bootstrap Inline Edit
        $.fn.editable.defaults.mode = 'inline';
        var compr = this.pool.get('compression');
        var mntOptn = this.pool.get('mnt_options');
        var url = '/api/pools/' + this.pool.get('id') + '/remount';
        $('#comprOptn').editable({
            value: compr,
            source: [{
                value: 'no',
                text: 'no'
            },
            {
                value: 'zlib',
                text: 'zlib'
            },
            {
                value: 'lzo',
                text: 'lzo'
            }
            ],
            success: function(response, newCompr) {
                $.ajax({
                    url: url,
                    type: 'PUT',
                    dataType: 'json',
                    data: {
                        'compression': newCompr,
                        'mnt_options': mntOptn
                    }
                });
            }
        });

        $('#mntOptions').editable({
            title: 'Edit Mount Options',
            emptytext: 'None',
            success: function(response, newMntOptns) {
                $.ajax({
                    url: url,
                    type: 'PUT',
                    dataType: 'json',
                    data: {
                        'compression': compr,
                        'mnt_options': newMntOptns
                    },
                });
            }
        });

        $('#comp-mnt-optns-table').tooltip({
            selector: '[data-title]',
            html: true,
            placement: 'right'
        });

    },

    deletePool: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        _this.$('#delete-pool-modal').modal();
    },

    confirmPoolDelete: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var url = '/api/pools/' + this.pool.get('id') + '/force';
        $.ajax({
            url: url,
            type: 'DELETE',
            dataType: 'json',
            success: function() {
                enableButton(button);
                _this.$('#delete-pool-modal').modal('hide');
                $('.modal-backdrop').remove();
                app_router.navigate('pools', {
                    trigger: true
                });
            },
            error: function(xhr, status, error) {
                enableButton(button);
            }
        });
    },

    resizePool: function(event) {
        event.preventDefault();
        var wizardView = new PoolResizeWizardView({
            model: new Backbone.Model({
                pool: this.pool
            }),
            title: 'Resize Pool / Change RAID level for ' + this.pool.get('name'),
            parent: this
        });
        $('.overlay-content', '#pool-resize-raid-overlay').html(wizardView.render().el);
        $('#pool-resize-raid-overlay').overlay().load();
    },

    resizePoolSubmit: function(event) {
        event.preventDefault();
        var button = this.$('#js-submit-resize');
        if (buttonDisabled(button)) return false;
        if (confirm(' Are you sure about Resizing this pool?')) {
            disableButton(button);
            var _this = this;
            var raid_level = $('#raid_level').val();
            var disk_names = [];
            var err_msg = 'Please select atleast one disk';
            var n = _this.$('.disknew:checked').length;
            var m = _this.$('.diskadded:unchecked').length;
            var resize_msg = ('Resize is initiated. A balance process is kicked off to redistribute data. It could take a while. You can check the status in the Balances tab. Its finish marks the success of resize.');
            if (n >= 0) {
                $('#pool-resize-raid-modal').modal('show');
            } else if (m > 0) {
                _this.$('.diskadded:unchecked').each(function(i) {
                    if (i < m) {
                        disk_names.push($(this).val());
                    }
                });
                $.ajax({
                    url: '/api/pools/' + _this.pool.get('id') + '/remove',
                    type: 'PUT',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        'disks': disk_names,
                        'raid_level': raid_level
                    }),
                    success: function() {
                        _this.hideResizeTooltips();
                        alert(resize_msg);
                        _this.pool.fetch({
                            success: function(collection, response, options) {
                                _this.cView = 'view';
                                _this.render();
                            }
                        });

                    },
                    error: function(request, status, error) {
                        enableButton(button);
                    }
                });
            }
        }
    },

    resizePoolCancel: function(event) {
        event.preventDefault();
        this.hideResizeTooltips();
        this.$('#ph-resize-pool-info').html(this.resize_pool_info_template({
            pool: this.pool
        }));
    },

    resizePoolModalSubmit: function(event) {
        var _this = this;
        var raid_level = $('#raid_level').val();
        var disk_names = [];
        var err_msg = 'Please select atleast one disk';
        var n = _this.$('.disknew:checked').length;
        var m = _this.$('.diskadded:unchecked').length;
        var resize_msg = ('Resize is initiated. A balance process is kicked off to redistribute data. It could take a while. You can check the status in the Balances tab. Its finish marks the success of resize.');
        _this.$('.disknew:checked').each(function(i) {
            if (i < n) {
                disk_names.push($(this).val());
            }
        });
        $.ajax({
            url: '/api/pools/' + _this.pool.get('id') + '/add',
            type: 'PUT',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                'disks': disk_names,
                'raid_level': raid_level
            }),
            success: function() {
                _this.hideResizeTooltips();
                alert(resize_msg);
                _this.pool.fetch({
                    success: function(collection, response, options) {
                        _this.cView = 'view';
                        _this.render();
                    }
                });
            },
            error: function(request, status, error) {
                enableButton(button);
            }
        });

    },

    showResizeTooltips: function() {
        this.$('#ph-resize-pool-info #raid_level').tooltip({
            html: true,
            placement: 'top',
            title: 'You can transition raid level of this pool to change it\'s redundancy profile.',
        });
    },

    hideResizeTooltips: function() {
        this.$('#ph-resize-pool-info #raid_level').tooltip('hide');
    },

    attachModalActions: function() {

    },

    cleanup: function() {
        if (!_.isUndefined(this.statusIntervalId)) {
            window.clearInterval(this.statusIntervalId);
        }
    },

    initHandlebarHelpers: function() {

        asJSON = function (role) {
            // Simple wrapper to test for not null and JSON compatibility,
            // returns the json object if both tests pass, else returns false.
            if (role == null) { // db default
                return false;
            }
            // try json conversion and return false if it fails
            // @todo not sure if this is redundant?
            try {
                return JSON.parse(role);
            } catch (e) {
                return false;
            }
        };

        // Identify Open LUKS container by return of true / false.
        // Works by examining the Disk.role field.
        Handlebars.registerHelper('isOpenLuks', function (role) {
            var roleAsJson = asJSON(role);
            if (roleAsJson == false) return false;
            // We have a json string ie non legacy role info so we can examine:
            if (roleAsJson.hasOwnProperty('openLUKS')) {
                // Once a LUKS container is open it has a type of crypt
                // and we attribute it the role of 'openLUKS' as a result.
                return true;
            }
            // In all other cases return false.
            return false;
        });

        Handlebars.registerHelper('getPoolCreationDate', function(date) {
            return moment(date).format(RS_DATE_FORMAT);
        });

        Handlebars.registerHelper('humanReadableSize', function(size) {
            return humanize.filesize(size * 1024);
        });

        Handlebars.registerHelper('isRoot', function(role){
            if (role == 'root') {
                return true;
            }
            return false;
        });
    }
});
