
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

ReplicaReceiveTrailsView = RockstoreLayoutView.extend({
  events: {
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.replication_receive_trails;
    this.paginationTemplate = window.JST.common_pagination;
    // add dependencies
    this.replicaShareId = this.options.replicaShareId;
    this.replicaShare = new ReplicaShare({id: this.replicaShareId});
    this.dependencies.push(this.replicaShare);
    this.collection = new ReceiveTrailCollection(null, {
      replicaShareId: this.replicaShareId
    });
    this.dependencies.push(this.collection);
    this.collection.on("reset", this.renderReplicaReceiveTrails, this);
  },

  render: function() {
    this.fetch(this.renderReplicaReceiveTrails, this);
    return this;
  },
  
  renderReplicaReceiveTrails: function() {
    var _this = this;
    $(this.el).html(this.template({
      replicaShare: this.replicaShare,
      receiveTrails: this.collection
    }));
    this.$(".pagination-ph").html(this.paginationTemplate({
      collection: this.collection
    }));
    this.$('[rel=tooltip]').tooltip({ placement: 'bottom'});
    this.$('#receive-trails-table').tablesorter();
  },

});

// Add pagination
Cocktail.mixin(ReplicaReceiveTrailsView, PaginationMixin);


