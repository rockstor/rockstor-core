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
  url: '/api/dashboardconfig/',
  setConfig: function(wConfigs) {
    var tmp = [];
    _.each(wConfigs, function(wConfig) {
      tmp.push({
        name: wConfig.name, 
        displayName: wConfig.displayName,
        view: wConfig.view,
        rows: wConfig.rows, 
        cols: wConfig.cols,
        position: wConfig.position, 
      });
    });
    this.set({ widgets: JSON.stringify(tmp) });
  },
  getConfig: function() {
    if (!_.isUndefined(this.get('widgets')) && 
    !_.isNull(this.get('widgets'))) {
      return JSON.parse(this.get('widgets')); 
    } else {
      return null;
    }
  }

});

var Probe = Backbone.Model.extend({
  urlRoot: function() {
      return '/api/sm/sprobes/' + this.get('name') + '/';
  },
  dataUrl: function() {
    return '/api/sm/sprobes/' + this.get('name') + '/' + this.id + '/data/';
  },
  parse: function(response) {
    if (response.results && response.results.length > 0) {
      return response.results[0];
    } else {
      return {};
    }
  }
});

var ProbeCollection = Backbone.Collection.extend({
  model: Probe,
  initialize: function(models, options) {
    if (!_.isUndefined(options) && !_.isNull(options)) {
      this.name = options.name;
    }
  },
  url: function() {
    return '/api/sm/sprobes/' + this.name + '/';
  },
  parse: function(response) {
    return response.results;
  }
});

var NetworkInterface = Backbone.Model.extend({
  url: function() {
    return '/api/network/' + this.get('name') + '/';
  }
});
var NetworkInterfaceCollection = Backbone.Collection.extend({
  model: NetworkInterface,
  url: '/api/network/'
});

