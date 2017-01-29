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

ReplicationReceiveView = RockstorLayoutView.extend({
    events: {
        'switchChange.bootstrapSwitch': 'switchStatus',
        'click a[data-action=delete]': 'deleteReceivedTask'
    },

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        // set template
        this.template = window.JST.replication_replication_receive;
        this.serviceName = 'replication';
        this.replicationService = new Service({
            name: this.serviceName
        });
        this.dependencies.push(this.replicationService);
        this.collection = new ReplicaShareCollection();
        this.dependencies.push(this.collection);
        this.replicaReceiveTrails = new ReceiveTrailCollection();
        this.replicaReceiveTrails.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.replicaReceiveTrails);
        this.updateFreq = 5000;
        this.replicaReceiveTrailMap = {};
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.renderReceives, this);
        return this;
    },

    renderReceives: function() {
        var _this = this;
        // Construct map for receive -> trail
        this.collection.each(function(replicaShare, index) {
            var tmp = _this.replicaReceiveTrails.filter(function(replicaReceiveTrail) {
                return replicaReceiveTrail.get('rshare') == replicaShare.id;
            });
            tmp = tmp.filter(function(replicaReceiveTrail) {
                return replicaReceiveTrail.get('end_ts') != null;
            });
            _this.replicaReceiveTrailMap[replicaShare.id] = _.sortBy(tmp, function(replicaReceiveTrail) {
                return moment(replicaReceiveTrail.get('end_ts')).valueOf();
            }).reverse();
        });
        $(this.el).html(this.template({
            replicationService: this.replicationService,
            replicaColl: this.collection.toJSON(),
            collection: this.collection,
            collectionNotEmpty: !this.collection.isEmpty(),
            replicaReceiveTrailMap: this.replicaReceiveTrailMap
        }));

        //initalize Bootstrap Switch
        this.$('[type=\'checkbox\']').bootstrapSwitch();
        if (typeof this.current_status == 'undefined') {
            this.current_status = this.replicationService.get('status');
        }
        this.$('input[name="replica-service-checkbox"]').bootstrapSwitch('state', this.current_status, true);
        this.$('[type=\'checkbox\']').bootstrapSwitch('onColor', 'success'); //left side text color
        this.$('[type=\'checkbox\']').bootstrapSwitch('offColor', 'danger'); //right side text color

        // Display Service Warning
        if (!this.current_status) {
            this.$('#replication-warning').show();
        } else {
            this.$('#replication-warning').hide();
        }

        this.$('[rel=tooltip]').tooltip({
            placement: 'bottom'
        });
        this.renderDataTables();
    },

    switchStatus: function(event, state) {
        //the bootsrap switch can either be Service or Status Switch
        var replicaSwitchName = $(event.target).attr('name');
        if (replicaSwitchName == 'replica-service-checkbox') {
            if (state) {
                this.startService();
            } else {
                this.stopService();
            }
        } else if (replicaSwitchName == 'replica-task-checkbox') {
            var replicaId = $(event.target).attr('data-replica-id');
            if (state) {
                this.enable(replicaId);
            } else {
                this.disable(replicaId);
            }
        }
    },

    deleteReceivedTask: function(event) {
        var _this = this;
        if (event) {
            event.preventDefault();
        }
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        var rId = $(event.currentTarget).attr('data-rshare-id');
        var rShare = $(event.currentTarget).attr('data-rshare-name');
        if (confirm('Delete Received Replication task:  ' + rShare + '. Are you sure?')) {
            $.ajax({
                url: '/api/sm/replicas/rshare/' + rId,
                type: 'DELETE',
                dataType: 'json',
                success: function() {
                    enableButton(button);
                    _this.collection.fetch({
                        success: function() {
                            _this.renderReceives();
                        }
                    });
                },
                error: function(xhr, status, error) {
                    enableButton(button);
                }
            });
        }
    },

    startService: function(event) {
        var _this = this;
        var serviceName = this.serviceName;
        this.setStatusLoading(serviceName, true);
        $.ajax({
            url: '/api/sm/services/replication/start',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(serviceName, false);
                _this.current_status = true;
                _this.$('#replication-warning').hide();
            },
            error: function(xhr, status, error) {
                _this.setStatusError(serviceName, xhr);
            }
        });
    },

    stopService: function(event) {
        var _this = this;
        var serviceName = this.serviceName;
        this.setStatusLoading(serviceName, true);
        $.ajax({
            url: '/api/sm/services/replication/stop',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(serviceName, false);
                _this.current_status = false;
                _this.$('#replication-warning').show();
            },
            error: function(xhr, status, error) {
                _this.setStatusError(serviceName, xhr);
            }
        });
    },

    setStatusLoading: function(serviceName, show) {
        var statusEl = this.$('div.command-status[data-service-name="' + serviceName + '"]');
        if (show) {
            statusEl.html('<img src="/static/storageadmin/img/ajax-loader.gif"></img>');
        } else {
            statusEl.empty();
        }
    },

    setStatusError: function(serviceName, xhr) {
        var statusEl = this.$('div.command-status[data-service-name="' + serviceName + '"]');
        var msg = parseXhrError(xhr);
        // remove any existing error popups
        $('body').find('#' + serviceName + 'err-popup').remove();
        // add icon and popup
        statusEl.empty();
        var icon = $('<i>').addClass('icon-exclamation-sign').attr('rel', '#' + serviceName + '-err-popup');
        statusEl.append(icon);
        var errPopup = this.$('#' + serviceName + '-err-popup');
        var errPopupContent = this.$('#' + serviceName + '-err-popup > div');
        errPopupContent.html(msg);
        statusEl.click(function() {
            errPopup.overlay().load();
        });
    },

    initHandlebarHelpers: function() {
        var _this = this;

        Handlebars.registerHelper('lastReceived', function(replicaId) {
            var html = '';
            if (_this.replicaReceiveTrailMap[replicaId]) {
                if (_this.replicaReceiveTrailMap[replicaId].length > 0) {
                    var rrt = _this.replicaReceiveTrailMap[replicaId][0];
                    if (rrt.get('status') == 'failed') {
                        html += '<a href="#replication-receive/' + replicaId + '/trails" class="replica-trail"><i class="glyphicon glyphicon-warning-sign"></i> ' + rrt.get('status') + '</a>';
                    } else if (rrt.get('status') == 'pending') {
                        html += '<a href="#replication-receive/' + replicaId + '/trails" class="replica-trail">' + rrt.get('status') + '</a>';

                    } else if (rrt.get('status') == 'succeeded') {
                        html += '<a href="#replication-receive/' + replicaId + '/trails" class="replica-trail">' + moment(rrt.get('end_ts')).fromNow() + '</a>';
                    }
                }
            }
            return new Handlebars.SafeString(html);
        });
    }

});

//Add pagination
Cocktail.mixin(ReplicationReceiveView, PaginationMixin);