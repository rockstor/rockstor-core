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
 
var BackupPolicy = Backbone.Model.extend({
  urlRoot: "/api/plugin/backup" 
}); 

var BackupPolicyCollection = RockStorPaginatedCollection.extend({
  model: BackupPolicy,
  baseUrl: '/api/plugin/backup'
});

var BackupPolicyTrail = Backbone.Model.extend({
  urlRoot: "/api/plugin/backup/trail" 
}); 

var BackupPolicyTrailCollection = RockStorPaginatedCollection.extend({
  model: BackupPolicyTrail,
  initialize: function(models, options) {
    this.constructor.__super__.initialize.apply(this, arguments);
    if (options) {
      this.trailId = options.trailId;
    }
  },
  baseUrl: function() {
    if (this.trailId) {
      return '/api/plugin/backup/trail/' + this.trailId;
    } else {
      return '/api/plugin/backup/trail';
    }
  }
});
