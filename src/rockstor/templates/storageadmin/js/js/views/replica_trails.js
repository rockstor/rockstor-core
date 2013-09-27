
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

ReplicaTrailsView = RockstoreLayoutView.extend({
  events: {
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.replication_replica_trails;
    // add dependencies
    this.replicaId = this.options.replicaId;
    this.replica = new Replica({id: this.replicaId});
    this.dependencies.push(this.replica);
    this.replicaTrails = new ReplicaTrailCollection(null, {
      replicaId: this.replicaId
    });
    this.dependencies.push(this.replicaTrails);
  },

  render: function() {
    this.fetch(this.renderReplicaTrails, this);
    return this;
  },

  renderReplicaTrails: function() {
    var _this = this;
    $(this.el).html(this.template({
      replica: this.replica,
      replicaTrails: this.replicaTrails
    }));
    this.$('[rel=tooltip]').tooltip({ placement: 'bottom'});
  },

});

// Add pagination
Cocktail.mixin(ReplicaTrailsView, PaginationMixin);

