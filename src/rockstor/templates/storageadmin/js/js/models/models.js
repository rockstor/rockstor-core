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

// Models and Collections
var Setup = Backbone.Model.extend({

});

var Disk = Backbone.Model.extend({
  url: function() {
    return '/api/disks/' + this.get('diskName') + '/';
  }
});
var DiskCollection = Backbone.Collection.extend({
  model: Disk,
  url: '/api/disks/'
});

var Pool = Backbone.Model.extend({
  url: function() {
    return '/api/pools/' + this.get('poolName') + '/';
  }
});

var PoolCollection = Backbone.Collection.extend({
  model: Pool,
  url: '/api/pools/'
});


var SupportCase = Backbone.Model.extend({
	  url: function() {
	    return '/api/support/' + this.get('supportCaseId') + '/';
	  }
	});

var SupportCaseCollection = Backbone.Collection.extend({
	  model: SupportCase,
	  url: '/api/support/'
});
	
var Share = Backbone.Model.extend({
  url: function() {
    return '/api/shares/' + this.get('shareName') + '/';
  }
});

var ShareCollection = Backbone.Collection.extend({
  model: Share,
  url: '/api/shares/'
});

var Snapshot = Backbone.Model.extend({
  url: function() {
    return '/api/shares/' + this.get('shareName') + '/' + this.get('snapName') + '/';			} 
});


var SnapshotCollection = Backbone.Collection.extend({
  model: Snapshot,
  //url: function() {
   //return 
  //},

  setUrl: function(shareName) {
      this.url ='/api/shares/' + shareName + '/snapshots/'    
  }

});

var SysInfo = Backbone.Model.extend({
  url: "/api/tools/sysinfo"
});

var NFSExport = Backbone.Model.extend();
var NFSExportCollection = Backbone.Collection.extend({
  model: NFSExport,
  setUrl: function(shareName) {
      this.url = '/api/shares/' + shareName + '/nfs/'    
  }

});
var SMBShare = Backbone.Model.extend({ 
  url: function() {
      return '/api/shares/' + this.get('shareName') + '/samba/'    
  }
});
var SMBShareCollection = Backbone.Collection.extend({model: SMBShare});

var Service = Backbone.Model.extend({
  url: function() {
    return '/api/sm/services/' + this.get('name') + '/';
  }
});

var Appliance = Backbone.Model.extend({urlRoot: '/api/appliances/'});
var ApplianceCollection = Backbone.Collection.extend({
  model: Appliance,
  url: '/api/appliances/'
});

var User = Backbone.Model.extend({urlRoot: '/api/users/'});
var UserCollection = Backbone.Collection.extend({
  model: User,
  url: '/api/users/'
});

var ISCSITarget = Backbone.Model.extend({ 
  url: function() {
      return '/api/shares/' + this.get('shareName') + '/iscsi/'    
  }
});

var DashboardConfig = Backbone.Model.extend({ 
  url: '/api/dashboardconfig/'
});

