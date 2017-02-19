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


AddReplicationTaskView = RockstorLayoutView.extend({
    events: {
        'click #js-cancel': 'cancel',
        'change #appliance': 'fetchRemotePools'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.replication_add_replication_task;
        this.shares = new ShareCollection();
        this.shares.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.shares);
        this.appliances = new ApplianceCollection();
        this.dependencies.push(this.appliances);
        this.replicas = new ReplicaCollection();
        this.replica = null; // for new replica tasks.
        this.dependencies.push(this.replicas);
        this.remote_pools = [];

        this.replicaId = this.options.replicaId;

        if (!_.isUndefined(this.replicaId) && !_.isNull(this.replicaId)) {
            this.replica = new Replica({
                id: this.replicaId
            });
            this.dependencies.push(this.replica);
        }
    },

    render: function() {
        this.fetch(this.renderNewReplicationTask, this);
        return this;
    },

    renderNewReplicationTask: function() {
        var _this = this;
        this.freeShares = this.shares.reject(function(share) {
            return !_.isUndefined(_this.replicas.find(function(replica) {
                return replica.get('share') == share.get('name');
            }));
        });
        this.freeShares2 = this.freeShares.map(function(fs) {
            return fs.toJSON();
        });
        if (this.remote_pools.length == 0) {
            this.fetchRemotePools();
        }
        //ip and port of the remote replication service.
        var listener_ip = null;
        var listener_port = 10002;
        var replicaJSON = null;
        if (this.replica) {
            listener_ip = this.replica.get('replicaion_ip');
            listener_port = this.replica.get('remote_port');
            replicaJSON = this.replica.toJSON();
        }

        $(this.el).html(this.template({
            shares: this.freeShares2,
            appliances: this.appliances.toJSON(),
            replica: replicaJSON,
            listener_ip: listener_ip,
            listener_port: listener_port,
            replicaId: this.replicaId,
            remote_pools: this.remote_pools
        }));
        if (!_.isUndefined(this.replicaId) && !_.isNull(this.replica)) {
            var crontab = this.replica.get('crontab');
            $('#cron').cron('value', crontab);
        }

        $('#replication-task-create-form :input').tooltip({
            placement: 'right'
        });

        $('#replication-task-create-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                task_name: 'required',
                pool: 'required',
                frequency: {
                    required: true,
                    number: true
                }
            },
            submitHandler: function() {
                var button = $('#create_replication_task');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var data = _this.$('#replication-task-create-form').getJSON();
                var url, req_type;
                if (_this.replicaId == null) {
                    url = '/api/sm/replicas/';
                    req_type = 'POST';
                } else {
                    url = '/api/sm/replicas/' + _this.replicaId;
                    req_type = 'PUT';
                }
                data.crontab = $('#cron').cron('value');
                $.ajax({
                    url: url,
                    type: req_type,
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    success: function() {
                        enableButton(button);
                        app_router.navigate('replication', {
                            trigger: true
                        });
                    },
                    error: function(xhr, status, error) {
                        enableButton(button);
                    }
                });
                return false;
            }
        });
    },

    fetchRemotePools: function(event) {
        var _this = this;
        var target_appliance = null;
        var ip = $('#appliance').attr('value');
        if (!ip) {
            target_appliance = this.appliances.find(function(a) {
                return !a.get('current_appliance');
            });
        } else {
            target_appliance = this.appliances.find(function(a) {
                return (a.get(ip) == ip);
            });
        }
        var uuid = target_appliance.get('uuid');
        $.ajax({
            url: '/api/sm/replicas/rpool/' + uuid,
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.remote_pools = data;
                _this.renderNewReplicationTask();
            }
        });
    },

    cancel: function(event) {
        event.preventDefault();
        app_router.navigate('replication', {
            trigger: true
        });
    }

});