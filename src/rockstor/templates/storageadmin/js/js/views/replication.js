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

ReplicationView = RockstoreLayoutView.extend({
  events: {
    'click .enable': 'enable',
    'click .disable': 'disable'
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.replication_replication;
    this.paginationTemplate = window.JST.common_pagination;
    // add dependencies
    this.collection = new ReplicaCollection();
    this.dependencies.push(this.collection);
    this.replicationService = new Service({name: 'replication'});
    this.dependencies.push(this.replicationService);
    this.replicaTrails = new ReplicaTrailCollection();
    this.replicaTrails.pageSize = RockStorGlobals.maxPageSize;
    this.dependencies.push(this.replicaTrails);
    this.replicaShareMap = {};
    this.replicaTrailMap = {};
    this.collection.on('reset', this.renderReplicas, this);
  },

  render: function() {
    this.fetch(this.renderReplicas, this);
    return this;
  },

  renderReplicas: function() {

    var _this = this;
    
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
      }) 
    });
    this.collection.each(function(replica, index) {
      var tmp = _this.replicaTrails.filter(function(replicaTrail) {
        return replicaTrail.get('replica') == replica.id;
      });
      _this.replicaTrailMap[replica.id] = _.sortBy(tmp, function(replicaTrail) {
        return moment(replicaTrail.get('snapshot_created')).valueOf();
      }).reverse();
    });
    $(this.el).html(this.template({
      replicationService: this.replicationService,
      replicas: this.collection,
      replicaShareMap: this.replicaShareMap,
      replicaTrailMap: this.replicaTrailMap
    }));
    this.$('[rel=tooltip]').tooltip({ placement: 'bottom'});
    this.$(".ph-pagination").html(this.paginationTemplate({
      collection: this.collection
    }));
   
  },

  enable: function(event) {
    var _this = this;
    if (event) { event.preventDefault(); }
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    disableButton(button); 
    var replicaId = $(event.currentTarget).attr("data-replica-id");
    $.ajax({
      url: '/api/sm/replicas/' + replicaId,
      type: 'PUT',
      dataType: 'json',
      data: {enabled: 'True'},
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
  },

  disable: function(event) {
    var _this = this;
    if (event) { event.preventDefault(); }
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    disableButton(button); 
    var replicaId = $(event.currentTarget).attr("data-replica-id");
    $.ajax({
      url: '/api/sm/replicas/' + replicaId,
      type: 'PUT',
      dataType: 'json',
      data: {enabled: 'False'},
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

});

// Add pagination
Cocktail.mixin(ReplicationView, PaginationMixin);

