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

ReplicationView = RockstorLayoutView.extend({
    events: {
        'click a[data-action=delete]': 'deleteTask',
        'switchChange.bootstrapSwitch': 'switchStatus',
    },

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        // set template
        this.template = window.JST.replication_replication;
        // add dependencies
        this.collection = new ReplicaCollection();
        this.dependencies.push(this.collection);
        this.serviceName = 'replication';
        this.replicationService = new Service({
            name: this.serviceName
        });
        this.dependencies.push(this.replicationService);
        this.replicaTrails = new ReplicaTrailCollection();
        this.replicaTrails.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.replicaTrails);
        this.appliances = new ApplianceCollection();
        this.dependencies.push(this.appliances);
        this.shares = new ShareCollection();
        this.dependencies.push(this.shares);
        this.replicaShareMap = {};
        this.replicaTrailMap = {};
        this.collection.on('reset', this.renderReplicas, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.renderReplicas, this);
        RockStorSocket.services = io.connect('/services', {
            'secure': true,
            'force new connection': true
        });
        RockStorSocket.addListener(this.serviceStatusSync, this, 'services:get_services');
        return this;
    },

    renderReplicas: function() {
        var _this = this;
        this.otherAppliances = this.appliances.filter(function(appliance) {
            return appliance.get('current_appliance') == false;
        });
        this.freeShares = this.shares.reject(function(share) {
            return !_.isUndefined(_this.collection.find(function(replica) {
                return replica.get('share') == share.get('name');
            }));
        });
        // remove existing tooltips
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }
        var shares = this.collection.map(function(replica) {
            return replica.get('share');
        });
        _.each(shares, function(share) {
            _this.replicaShareMap[share] = _this.collection.filter(function(replica) {
                return replica.get('share') == share;
            });
        });
        this.collection.each(function(replica, index) {
            var tmp = _this.replicaTrails.filter(function(replicaTrail) {
                return replicaTrail.get('replica') == replica.id;
            });
            _this.replicaTrailMap[replica.id] = _.sortBy(tmp, function(replicaTrail) {
                return moment(replicaTrail.get('snapshot_created')).valueOf();
            }).reverse();
        });
        var noFreeShares,
            noOtherAppliances,
            otherAppliances_FreeShares = false;

        if (this.freeShares.length == 0) {
            noFreeShares = true;
        }
        if (this.otherAppliances.length == 0) {
            noOtherAppliances = true;
        }
        if (this.otherAppliances.length > 0 && this.freeShares.length > 0) {
            otherAppliances_FreeShares = true;
        }
        $(this.el).html(this.template({
            replicationService: this.replicationService,
            replicaColl: this.collection.toJSON(),
            collection: this.collection,
            collectionNotEmpty: !this.collection.isEmpty(),
            replicaShareMap: this.replicaShareMap,
            replicaTrailMap: this.replicaTrailMap,
            otherAppliances: this.otherAppliances,
            freeShares: this.freeShares,
            noFreeShares: noFreeShares,
            noOtherAppliances: noOtherAppliances,
            otherAppliances_FreeShares: otherAppliances_FreeShares,
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

        //added ext func to sort over Replication task Enable/Disable input checkboxes
        $.fn.dataTable.ext.order['dom-checkbox'] = function(settings, col) {
            return this.api().column(col, {
                order: 'index'
            }).nodes().map(function(td, i) {
                return $('input', td).prop('checked') ? '1' : '0';
            });
        };
        //Added columns definition for sorting purpose
        $('table.data-table').DataTable({
            'iDisplayLength': 15,
            'aLengthMenu': [
                [15, 30, 45, -1],
                [15, 30, 45, 'All']
            ],
            'columns': [
                null, null, null, null, null, null,
                {
                    'orderDataType': 'dom-checkbox'
                }
            ]
        });
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

    enable: function(replicaId) {
        var _this = this;
        $.ajax({
            url: '/api/sm/replicas/' + replicaId,
            type: 'PUT',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                enabled: true
            }),
            success: function() {
                _this.collection.fetch({
                    success: function() {
                        _this.renderReplicas();
                    }
                });
            },
            error: function(xhr, status, error) {}
        });
    },

    disable: function(replicaId) {
        var _this = this;
        $.ajax({
            url: '/api/sm/replicas/' + replicaId,
            type: 'PUT',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                enabled: false
            }),
            success: function() {
                _this.collection.fetch({
                    success: function() {
                        _this.renderReplicas();
                    }
                });
            },
            error: function(xhr, status, error) {
                enableButton(button);
            }
        });
    },

    deleteTask: function(event) {
        var _this = this;
        if (event) {
            event.preventDefault();
        }
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        var rTaskId = $(event.currentTarget).attr('data-task-id');
        var rTaskName = $(event.currentTarget).attr('data-task-name');
        if (confirm('Delete Replication task:  ' + rTaskName + '. Are you sure?')) {
            $.ajax({
                url: '/api/sm/replicas/' + rTaskId,
                type: 'DELETE',
                dataType: 'json',
                success: function() {
                    enableButton(button);
                    _this.collection.fetch({
                        success: function() {
                            _this.renderReplicas();
                        }
                    });
                },
                error: function(xhr, status, error) {
                    enableButton(button);
                }
            });
        }
    },

    startService: function() {
        var _this = this;
        this.setStatusLoading(this.serviceName, true);
        $.ajax({
            url: '/api/sm/services/replication/start',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(_this.serviceName, false);
                _this.current_status = true;
                //hide replication service warning
                _this.$('#replication-warning').hide();
            },
            error: function(xhr, status, error) {
                _this.$('input[name="replica-service-checkbox"]').bootstrapSwitch('state', _this.current_status, true);
            }
        });
    },

    stopService: function() {
        var _this = this;
        this.setStatusLoading(this.serviceName, true);
        $.ajax({
            url: '/api/sm/services/replication/stop',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(_this.serviceName, false);
                _this.current_status = false;
                //display replication service warning
                _this.$('#replication-warning').show();
            },
            error: function(xhr, status, error) {
                _this.$('input[name="replica-service-checkbox"]').bootstrapSwitch('state', _this.current_status, true);
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

    serviceStatusSync: function(data) {
        if (data.replication.running > 0) {
            this.current_status = false;
            this.$('#replication-warning').show();
        } else {
            this.current_status = true;
            this.$('#replication-warning').hide();
        }
        this.$('input[name="replica-service-checkbox"]').bootstrapSwitch('state', this.current_status, true);
    },

    cleanup: function() {
        RockStorSocket.removeOneListener('services');
    },

    initHandlebarHelpers: function() {
        var _this = this;
        Handlebars.registerHelper('getFrequency', function(cronTab) {
            return prettyCron.toString(cronTab);
        });

        Handlebars.registerHelper('lastBackup', function(replicaId) {
            var html = '';
            if (_this.replicaTrailMap[replicaId]) {
                if (_this.replicaTrailMap[replicaId].length > 0) {
                    var rt = _this.replicaTrailMap[replicaId][0];
                    if (rt.get('status') == 'failed') {
                        html += '<a href="#replication/' + replicaId + '/trails" class="replica-trail"><i class="fa fa-exclamation-circle"></i> ' + rt.get('status') + '</a>';
                    } else if (rt.get('status') == 'pending') {
                        html += '<a href="#replication/' + replicaId + '/trails" class="replica-trail">' + rt.get('status') + '</a>';
                    } else if (rt.get('status') == 'succeeded') {
                        html += '<a href="#replication/' + replicaId + '/trails" class="replica-trail">' + moment(rt.get('end_ts')).fromNow() + '</a>';
                    }
                }
            }
            return new Handlebars.SafeString(html);
        });
    }

});
