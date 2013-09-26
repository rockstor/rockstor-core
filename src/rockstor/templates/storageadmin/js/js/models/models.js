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
var DiskCollection = RockStorPaginatedCollection.extend({
  model: Disk,
  baseUrl: '/api/disks/',
});

var Pool = Backbone.Model.extend({
  url: function() {
    return '/api/pools/' + this.get('poolName') + '/';
  }
});

var PoolCollection = RockStorPaginatedCollection.extend({
  model: Pool,
  baseUrl: '/api/pools/'
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
    return '/api/shares/' + this.get('shareName');
  }
});

var ShareCollection = RockStorPaginatedCollection.extend({
  model: Share,
  baseUrl: '/api/shares/'
});

var Snapshot = Backbone.Model.extend({
  url: function() {
    return '/api/shares/' + this.get('shareName') + '/' + this.get('snapName');			} 
});

var SnapshotCollection = RockStorPaginatedCollection.extend({
  model: Snapshot,
  setUrl: function(shareName) {
    this.baseUrl = '/api/shares/' + shareName + '/snapshots'    
  }
});

var SysInfo = Backbone.Model.extend({
  url: "/api/tools/sysinfo"
});

var NFSExport = Backbone.Model.extend();

var NFSExportCollection = RockStorPaginatedCollection.extend({
  model: NFSExport,
  setUrl: function(shareName) {
    this.baseUrl = '/api/shares/' + shareName + '/nfs'    
  }
});

var SMBShare = Backbone.Model.extend({ 
  url: function() {
      return '/api/shares/' + this.get('shareName') + '/samba'    
  }
});
var SMBShareCollection = Backbone.Collection.extend({model: SMBShare});

var Service = Backbone.Model.extend({
  idAttribute: "name",
});

var ServiceCollection = RockStorPaginatedCollection.extend({
  model: Service,
  baseUrl: "/api/sm/services"
});

var Appliance = Backbone.Model.extend({urlRoot: '/api/appliances/'});
var ApplianceCollection = Backbone.Collection.extend({
  model: Appliance,
  url: '/api/appliances/'
});

var User = Backbone.Model.extend({
  urlRoot: '/api/users/',
  idAttribute: 'username'
});

var UserCollection = RockStorPaginatedCollection.extend({
  model: User,
  baseUrl: '/api/users/'
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
      this.setConfig(RockStorWidgets.defaultWidgets());
      return JSON.parse(this.get("widgets"));
    }
  }

});

var Probe = Backbone.Model.extend({
  urlRoot: function() {
      return '/api/sm/sprobes/' + this.get('name') + '/';
  },
  dataUrl: function() {
    return '/api/sm/sprobes/' + this.get('name') + '/' + this.id + '/data';
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
var NetworkInterfaceCollection = RockStorPaginatedCollection.extend({
  model: NetworkInterface,
  baseUrl: '/api/network/'
});

var ProbeRun = Backbone.Model.extend({
  dataUrl: function() {
    return '/api/sm/sprobes/' + this.get('name') + '/' + this.id + '/data?format=json';
  },
  downloadUrl: function() {
    return "/api/sm/sprobes/" + this.get("name") + "/" + this.id 
    + "/data" + "?" 
    + "t1="+this.get("start") + "&t2=" + this.get("end") 
    + "&download=true";
  },
});

var ProbeRunCollection = RockStorPaginatedCollection.extend({
  model: ProbeRun,
  baseUrl: "/api/sm/sprobes/metadata"
})

var ProbeTemplate = Backbone.Model.extend({idAttribute: "uuid"});
var ProbeTemplateCollection = Backbone.Collection.extend({
  model: ProbeTemplate,
  url: "/api/sm/sprobes/?format=json"
});

var Replica = Backbone.Model.extend({
  urlRoot: "/api/sm/replicas"                                   
});
var ReplicaCollection = RockStorPaginatedCollection.extend({
  model: Replica,
  baseUrl: "/api/sm/replicas/"
});

