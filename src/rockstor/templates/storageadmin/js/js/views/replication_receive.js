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

ReplicationReceiveView = RockstoreLayoutView.extend({
  events: {
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.replication_replication_receive;
    this.paginationTemplate = window.JST.common_pagination;
    this.replicationService = new Service({name: 'replication'});
    this.dependencies.push(this.replicationService);
    this.collection = new ReplicaShareCollection();
    this.dependencies.push(this.collection);
    this.replicaReceiveTrails = new ReceiveTrailCollection();
    this.dependencies.push(this.replicaReceiveTrails);
    this.replicaReceiveTrailMap = {};
  },

  render: function() {
    var _this = this;
    // TODO fetch from backend when api is ready
    /*
    this.collection  = new ReplicaReceiveCollection([
      { source_task_name: 'task1',  source_appliance: '192.168.1.111', source_share: 'share1', destination_pool: 'reptarget', destination_share: 'share1_replica', last_run: ''},
      { id: 1, source_task_name: 'task2',  source_appliance: '192.168.1.111', source_share: 'share2', destination_pool: 'reptarget', destination_share: 'share2_replica', last_run: ''},
    ]);
    this.replicaReceiveTrails = new ReplicaReceiveTrailCollection([
      {id: 1, "replicaReceive": 1, "snap_name": "share2_replica_snap_8", "kb_sent": 133, "snapshot_created": "2014-01-30T19:53:33.094Z", "snapshot_failed": null, "send_pending": null, "send_succeeded": null, "send_failed": null, "end_ts": "2014-01-30T19:53:35.150Z", "status": "succeeded", "error": null}
    ]);
   */
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
      _this.replicaReceiveTrailMap[replicaShare.id] = _.sortBy(tmp, function(replicaReceiveTrail) {
        return moment(replicaReceiveTrail.get('end_ts')).valueOf();
      }).reverse();
    });
    $(this.el).html(this.template({
      replicationService: this.replicationService,
      replicaShares: this.collection,
      replicaReceiveTrailMap: this.replicaReceiveTrailMap
    }));
    this.$(".ph-pagination").html(this.paginationTemplate({
      collection: this.collection
    }));
    this.$('#replica-receives-table').tablesorter();
  },

});

// Add pagination
Cocktail.mixin(ReplicationReceiveView, PaginationMixin);


