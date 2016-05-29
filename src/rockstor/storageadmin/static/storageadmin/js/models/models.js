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
var Setup = Backbone.Model.extend({});

var Disk = Backbone.Model.extend({
    url: function () {
        return '/api/disks/' + this.get('diskName');
    },
    available: function () {
        return _.isNull(this.get('pool')) && !this.get('parted') && !this.get('offline') && _.isNull(this.get('btrfs_uuid'));
    },
    isSerialUsable: function () {
        // Simple disk serial validator to return true unless the given disk
        // serial number looks fake or untrustworthy.
        // In the case of a repeat or missing serial scan_disks() will use a
        // placeholder of fake-serial-<uuid4> so look for this signature text.
        var diskSerial = this.get('serial')
        if (diskSerial.substring(0, 12) == 'fake-serial-') {
            return false;
        }
        // Observed in a 4 bay ORICO USB 3.0 enclosure that obfuscated all it's
        // disk serial numbers and replaced them with '000000000000'.
        if (diskSerial == '000000000000') {
            return false;
        }
        return true;
    }
});

var DiskCollection = RockStorPaginatedCollection.extend({
    model: Disk,
    baseUrl: '/api/disks',
});

var Pool = Backbone.Model.extend({
    url: function () {
        return '/api/pools/' + this.get('poolName') + '/';
    },
    sizeGB: function () {
        return this.get('size') / (1024 * 1024);
    },
    freeGB: function () {
        return this.get('free') / (1024 * 1024);
    },
    usedGB: function () {
        return (this.get('size') - this.get('free')) / (1024 * 1024);
    }
});

var SmartInfo = Backbone.Model.extend({
    url: function () {
        return '/api/disks/smart/info/' + this.get('diskName');
    }
});

var PoolCollection = RockStorPaginatedCollection.extend({
    model: Pool,
    baseUrl: '/api/pools'
});

var SupportCase = Backbone.Model.extend({
    url: function () {
        return '/api/support/' + this.get('supportCaseId') + '/';
    }
});

var SupportCaseCollection = Backbone.Collection.extend({
    model: SupportCase,
    url: '/api/support'
});

var Share = Backbone.Model.extend({
    url: function () {
        return '/api/shares/' + this.get('shareName');
    }
});

var ShareCollection = RockStorPaginatedCollection.extend({
    model: Share,
    baseUrl: '/api/shares',
    extraParams: function () {
        var p = this.constructor.__super__.extraParams.apply(this, arguments);
        p['sortby'] = 'name';
        return p;
    }
});

var Image = Backbone.Model.extend({
    url: function () {
        return '/api/rockons/';
    }
});

var ImageCollection = RockStorPaginatedCollection.extend({
    model: Image,
    baseUrl: '/api/rockons/docker/images'
});

var Container = Backbone.Model.extend({
    url: function () {
        return '/api/rockons/';
    }
});

var ContainerCollection = RockStorPaginatedCollection.extend({
    model: Image,
    baseUrl: '/api/rockons/docker/containers'
});

var Snapshot = Backbone.Model.extend({
    url: function () {
        return '/api/shares/' + this.get('shareName') + '/' + this.get('snapName');
    }
});

var SnapshotCollection = RockStorPaginatedCollection.extend({
    model: Snapshot,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.snapType = options.snapType;
        }
    },
    setUrl: function (shareName) {
        this.baseUrl = '/api/shares/' + shareName + '/snapshots'
    },
    extraParams: function () {
        var p = this.constructor.__super__.extraParams.apply(this, arguments);
        p['snap_type'] = this.snapType;
        return p;
    }
});

var Snapshots = Backbone.Model.extend({
    urlRoot: '/api/snapshots'
});

var SnapshotsCollection = RockStorPaginatedCollection.extend({
    model: Snapshots,
    baseUrl: '/api/snapshots'
});


var Poolscrub = Backbone.Model.extend({
    url: function () {
        return '/api/pools/' + this.get('poolName') + '/scrub';
    }
});

var PoolscrubCollection = RockStorPaginatedCollection.extend({
    model: Poolscrub,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.snapType = options.snapType;
        }
    },
    setUrl: function (poolName) {
        this.baseUrl = '/api/pools/' + poolName + '/scrub';
    },
    extraParams: function () {
        var p = this.constructor.__super__.extraParams.apply(this, arguments);
        p['snap_type'] = this.snapType;
        return p;
    }
});

var PoolRebalance = Backbone.Model.extend({
    url: function () {
        return '/api/pools/' + this.get('poolName') + '/balance';
    }
});

var PoolRebalanceCollection = RockStorPaginatedCollection.extend({
    model: PoolRebalance,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.snapType = options.snapType;
        }
    },
    setUrl: function (poolName) {
        this.baseUrl = '/api/pools/' + poolName + '/balance';
    },
    extraParams: function () {
        var p = this.constructor.__super__.extraParams.apply(this, arguments);
        p['snap_type'] = this.snapType;
        return p;
    }
});

var SysInfo = Backbone.Model.extend({
    url: "/api/tools/sysinfo"
});

var NFSExport = Backbone.Model.extend();

var NFSExportCollection = RockStorPaginatedCollection.extend({
    model: NFSExport,
    setUrl: function (shareName) {
        this.baseUrl = '/api/shares/' + shareName + '/nfs'
    }
});

var NFSExportGroup = Backbone.Model.extend({
    urlRoot: '/api/nfs-exports'
});

var NFSExportGroupCollection = RockStorPaginatedCollection.extend({
    model: NFSExportGroup,
    baseUrl: '/api/nfs-exports'
});

var SMBShare = Backbone.Model.extend({
    url: function () {
        return '/api/shares/' + this.get('shareName') + '/samba'
    },

});

var SMBShareCollection = Backbone.Collection.extend({

    model: SMBShare

});


var SambaCollection = RockStorPaginatedCollection.extend({
    model: SMBShare,
    baseUrl: '/api/samba',
    idAttribute: 'sambaShareId'
});


var Service = Backbone.Model.extend({
    idAttribute: "name",
    urlRoot: "/api/sm/services"
});

var ServiceCollection = RockStorPaginatedCollection.extend({
    model: Service,
    baseUrl: "/api/sm/services/"
});

var Appliance = Backbone.Model.extend({urlRoot: '/api/appliances'});
var ApplianceCollection = RockStorPaginatedCollection.extend({
    model: Appliance,
    baseUrl: '/api/appliances'
});

var User = Backbone.Model.extend({
    urlRoot: '/api/users',
    idAttribute: 'username'
});

var UserCollection = RockStorPaginatedCollection.extend({
    model: User,
    baseUrl: '/api/users'
});

var Group = Backbone.Model.extend({
    urlRoot: '/api/groups',
    idAttribute: 'groupname'
});

var GroupCollection = RockStorPaginatedCollection.extend({
    model: Group,
    baseUrl: '/api/groups'
});

var ISCSITarget = Backbone.Model.extend({
    url: function () {
        return '/api/shares/' + this.get('shareName') + '/iscsi/'
    }
});

var DashboardConfig = Backbone.Model.extend({
    url: '/api/dashboardconfig',
    setConfig: function (wConfigs) {
        var tmp = [];
        _.each(wConfigs, function (wConfig) {
            tmp.push({
                name: wConfig.name,
                position: wConfig.position,
                maximized: wConfig.maximized
            });
        });
        this.set({widgets: JSON.stringify(tmp)});
    },

    getConfig: function () {
        if (!_.isUndefined(this.get('widgets')) && !_.isNull(this.get('widgets'))) {
            return JSON.parse(this.get('widgets'));
        } else {
            this.setConfig(RockStorWidgets.defaultWidgets());
            return JSON.parse(this.get("widgets"));
        }
    }

});

var Probe = Backbone.Model.extend({
    urlRoot: function () {
        return '/api/sm/sprobes/' + this.get('name') + '/';
    },
    dataUrl: function () {
        return '/api/sm/sprobes/' + this.get('name') + '/' + this.id + '/data';
    },
    parse: function (response) {
        if (response.results && response.results.length > 0) {
            return response.results[0];
        } else {
            return {};
        }
    }
});

var ProbeCollection = Backbone.Collection.extend({
    model: Probe,
    initialize: function (models, options) {
        if (!_.isUndefined(options) && !_.isNull(options)) {
            this.name = options.name;
        }
    },
    url: function () {
        return '/api/sm/sprobes/' + this.name + '/';
    },
    parse: function (response) {
        return response.results;
    }
});


var NetworkDevice = Backbone.Model.extend({
    urlRoot: '/api/network/devices'
});

var NetworkDeviceCollection = RockStorPaginatedCollection.extend({
    model: NetworkDevice,
    baseUrl: '/api/network/devices'
});

var NetworkConnection = Backbone.Model.extend({
    urlRoot: '/api/network/connections'
});

var NetworkConnectionCollection = RockStorPaginatedCollection.extend({
    model: NetworkConnection,
    baseUrl: '/api/network/connections'
});

var ProbeRun = Backbone.Model.extend({
    dataUrl: function () {
        return '/api/sm/sprobes/' + this.get('name') + '/' + this.id + '/data?format=json';
    },
    downloadUrl: function () {
        return "/api/sm/sprobes/" + this.get("name") + "/" + this.id
            + "/data" + "?"
            + "t1=" + this.get("start") + "&t2=" + this.get("end")
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

var ReplicaTrail = Backbone.Model.extend({
    urlRoot: '/api/sm/replicas/trail/replica/' + this.replicaId
});

var ReplicaTrailCollection = RockStorPaginatedCollection.extend({
    model: ReplicaTrail,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.replicaId = options.replicaId;
        }
    },
    baseUrl: function () {
        if (this.replicaId) {
            return '/api/sm/replicas/trail/replica/' + this.replicaId;
        } else {
            return '/api/sm/replicas/trail';
        }
    }
});

var ReplicaShare = Backbone.Model.extend({
    urlRoot: '/api/sm/replicas/rshare'
});

var ReplicaShareCollection = RockStorPaginatedCollection.extend({
    model: ReplicaShare,
    baseUrl: '/api/sm/replicas/rshare'
});

var ReceiveTrail = Backbone.Model.extend({
    urlRoot: '/api/sm/replicas/rtrail/' + this.replicaShareId
});

var ReceiveTrailCollection = RockStorPaginatedCollection.extend({
    model: ReceiveTrail,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.replicaShareId = options.replicaShareId;
        }
    },
    baseUrl: function () {
        if (this.replicaShareId) {
            return '/api/sm/replicas/rtrail/rshare/' + this.replicaShareId;
        } else {
            return '/api/sm/replicas/rtrail';
        }
    }
});

var TaskDef = Backbone.Model.extend({
    urlRoot: "/api/sm/tasks/",
    max_count: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).max_count;
        } else {
            return 0;
        }
    },
    share: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).share;
        } else {
            return '';
        }
    },
    prefix: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).prefix;
        } else {
            return '';
        }
    },
    pool: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).pool;
        } else {
            return '';
        }
    },
    visible: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).visible;
        } else {
            return false;
        }
    },


});

var TaskDefCollection = RockStorPaginatedCollection.extend({
    model: TaskDef,
    baseUrl: "/api/sm/tasks/"
});

var Task = Backbone.Model.extend({
    urlRoot: "/api/sm/tasks/log"
});

var TaskCollection = RockStorPaginatedCollection.extend({
    model: Task,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.taskDefId = options.taskDefId;
        }
    },
    baseUrl: function () {
        if (this.taskDefId) {
            return '/api/sm/tasks/log/taskdef/' + this.taskDefId;
        } else {
            return '/api/sm/tasks/log';
        }
    }
});

var SFTP = Backbone.Model.extend({
    urlRoot: '/api/sftp'
});

var SFTPCollection = RockStorPaginatedCollection.extend({
    model: SFTP,
    baseUrl: '/api/sftp'
});


var AFP = Backbone.Model.extend({
    urlRoot: '/api/netatalk'
});

var AFPCollection = RockStorPaginatedCollection.extend({
    model: AFP,
    baseUrl: '/api/netatalk'
});


var ReplicaReceive = Backbone.Model.extend({
    urlRoot: "/api/sm/replicareceives"
});

var ReplicaReceiveCollection = RockStorPaginatedCollection.extend({
    model: ReplicaReceive,
    baseUrl: "/api/sm/replicareceives"
});

var ReplicaReceiveTrail = Backbone.Model.extend({
    urlRoot: "/api/sm/replicareceivetrail"
});

var ReplicaReceiveTrailCollection = RockStorPaginatedCollection.extend({
    model: ReplicaReceiveTrail,
    baseUrl: "/api/sm/replicareceivetrai"
});

var AdvancedNFSExport = Backbone.Model.extend();

var AdvancedNFSExportCollection = RockStorPaginatedCollection.extend({
    model: AdvancedNFSExport,
    baseUrl: "/api/adv-nfs-exports"
});


var AccessKey = Backbone.Model.extend({
    url: function () {
        return '/api/oauth_app';
    }
});

var AccessKeyCollection = RockStorPaginatedCollection.extend({
    model: AccessKey,
    baseUrl: '/api/oauth_app'
});

var Certificate = Backbone.Model.extend({
    urlRoot: '/api/certificate',
});

var ConfigBackup = Backbone.Model.extend({
    urlRoot: '/api/config-backup',
});

var ConfigBackupCollection = RockStorPaginatedCollection.extend({
    model: ConfigBackup,
    baseUrl: '/api/config-backup'
});

var EmailAccount = Backbone.Model.extend({
    urlRoot: '/api/email',
});

var RockOn = Backbone.Model.extend({
    urlRoot: '/api/rockons'
});

var RockOnCollection = RockStorPaginatedCollection.extend({
    model: RockOn,
    baseUrl: '/api/rockons'
});

var RockOnVolume = Backbone.Model.extend({
    urlRoot: '/api/rockons/volumes/' + this.rid
});

var RockOnVolumeCollection = RockStorPaginatedCollection.extend({
    model: RockOnVolume,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function () {
        if (this.rid) {
            return '/api/rockons/volumes/' + this.rid;
        } else {
            return '/api/rockons/volumes';
        }
    }
});

var RockOnPort = Backbone.Model.extend({
    urlRoot: '/api/rockon/ports/' + this.rid
});

var RockOnPortCollection = RockStorPaginatedCollection.extend({
    model: RockOnPort,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function () {
        if (this.rid) {
            return '/api/rockons/ports/' + this.rid;
        } else {
            return '/api/rockons/ports';
        }
    }
});

var RockOnCustomConfig = Backbone.Model.extend({
    urlRoot: '/api/rockon/customconfig/' + this.rid
});

var RockOnCustomConfigCollection = RockStorPaginatedCollection.extend({
    model: RockOnCustomConfig,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function () {
        if (this.rid) {
            return '/api/rockons/customconfig/' + this.rid;
        } else {
            return '/api/rockons/customconfig';
        }
    }
});

var RockOnEnvironment = Backbone.Model.extend({
    urlRoot: '/api/rockon/environment/' + this.rid
});

var RockOnEnvironmentCollection = RockStorPaginatedCollection.extend({
    model: RockOnEnvironment,
    initialize: function (models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function () {
        if (this.rid) {
            return '/api/rockons/environment/' + this.rid;
        } else {
            return '/api/rockons/environment';
        }
    }
});

var EmailAccount = Backbone.Model.extend({
    urlRoot: '/api/email'
});

var EmailAccountCollection = RockStorPaginatedCollection.extend({
    model: EmailAccount,
    baseUrl: '/api/email'
});

var UpdateSubscription = Backbone.Model.extend({
    urlRoot: '/api/update-subscriptions'
});

var UpdateSubscriptionCollection = RockStorPaginatedCollection.extend({
    model: UpdateSubscription,
    baseUrl: '/api/update-subscriptions'
});
