/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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
    url: function() {
        return '/api/disks/' + this.get('diskId');
    },
    available: function () {
        return _.isNull(this.get('pool')) && !this.get('offline') &&
            _.isNull(this.get('btrfs_uuid'));
    },
    isSerialUsable: function() {
        // Simple disk serial validator to return true unless the given disk
        // serial number looks fake or untrustworthy.
        // In the case of a repeat or missing serial scan_disks() will use a
        // placeholder of fake-serial-<uuid4> so look for this signature text.
        var diskSerial = this.get('serial');
        if (diskSerial.substring(0, 12) == 'fake-serial-') {
            return false;
        }
        // Observed in a 4 bay ORICO USB 3.0 enclosure that obfuscated all it's
        // disk serial numbers and replaced them with '000000000000'.
        if (diskSerial == '000000000000') {
            return false;
        }
        return true;
    },
    // Using the disk.role system we can filter drives on their usability.
    // Roles for inclusion: openLUKS containers
    // Roles to dismiss: LUKS containers, mdraid members, the 'root' role,
    // and partitioned (if not accompanied by a redirect role).
    // Defaults to reject (return false)
    isRoleUsable: function () {
        // check if our role is null = db default
        // A drive with no role shouldn't present a problem for use.
        var role = this.get('role');
        if (role == null) {
            return true;
        }
        // try json conversion and return false if it fails
        // @todo not sure if this is redundant?
        try {
            var roleAsJson = JSON.parse(role);
        } catch (e) {
            // as we can't read this drives role we play save and exclude
            // it's isRoleUsable status by false
            return false;
        }
        // We have a json object, look for acceptable roles in the keys
        //
        // Accept use of 'openLUKS' device
        if (roleAsJson.hasOwnProperty('openLUKS')) {
            return true;
        }
        // Accept use of 'partitions' device but only if it is accompanied
        // by a 'redirect' role, ie so there is info to 'redirect' to the
        // by-id name held as the value to the 'redirect' role key.
        if (roleAsJson.hasOwnProperty('partitions') && roleAsJson.hasOwnProperty('redirect')) {
            // then we need to confirm if the fstype of the redirected
            // partition is "" else we can't use it
            if (roleAsJson.partitions.hasOwnProperty(roleAsJson.redirect)) {
                if (roleAsJson.partitions[roleAsJson.redirect] == '') {
                    return true;
                }
            }
        }
        // In all other cases return false, ie:
        // reject roles of for example root, mdraid, LUKS,
        // partitioned (when not accompanied by a valid redirect role) etc
        return false;
    }
});

var DiskCollection = RockStorPaginatedCollection.extend({
    model: Disk,
    baseUrl: '/api/disks'
});

var Pool = Backbone.Model.extend({
    url: function() {
        return '/api/pools/' + this.get('pid') + '/';
    },
    sizeGB: function() {
        return this.get('size') / (1024 * 1024);
    },
    freeGB: function() {
        return this.get('free') / (1024 * 1024);
    },
    usedGB: function() {
        return (this.get('size') - this.get('free')) / (1024 * 1024);
    }
});

var SmartInfo = Backbone.Model.extend({
    url: function() {
        return '/api/disks/smart/info/' + this.get('diskId');
    }
});

var PoolCollection = RockStorPaginatedCollection.extend({
    model: Pool,
    baseUrl: '/api/pools'
});

var Share = Backbone.Model.extend({
    url: function() {
        return '/api/shares/' + this.get('sid');
    }
});


var PoolShare = Backbone.Model.extend({
    url: function() {
        return '/api/pools/' + this.get('pid');
    }
});

var PoolShareCollection = Backbone.Collection.extend({
    model: PoolShare,
    initialize: function(model, options) {
        this.options = options;
    },
    url: function() {
        return '/api/pools/' + this.options.pid + '/shares';
    }
});

var ShareCollection = RockStorPaginatedCollection.extend({
    model: Share,
    baseUrl: '/api/shares',
    extraParams: function() {
        var p = this.constructor.__super__.extraParams.apply(this, arguments);
        p['sortby'] = 'name';
        return p;
    }
});

var Image = Backbone.Model.extend({
    url: function() {
        return '/api/rockons/';
    }
});

var ImageCollection = RockStorPaginatedCollection.extend({
    model: Image,
    baseUrl: '/api/rockons/docker/images'
});

var Container = Backbone.Model.extend({
    urlRoot: '/api/rockons/docker/containers/' + this.rid
});

var ContainerCollection = RockStorPaginatedCollection.extend({
    model: Container,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function() {
        if (this.rid) {
            return '/api/rockons/docker/containers/' + this.rid;
        }
        return '/api/rockons/docker/containers';
    }
});

var Snapshot = Backbone.Model.extend({
    url: function() {
        return '/api/shares/' + this.get('shareId') + '/' + this.get('snapName');
    }
});

var SnapshotCollection = RockStorPaginatedCollection.extend({
    model: Snapshot,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.snapType = options.snapType;
        }
    },
    setUrl: function(shareId) {
        this.baseUrl = '/api/shares/' + shareId + '/snapshots';
    },
    extraParams: function() {
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


var PoolScrub = Backbone.Model.extend({
    url: function() {
        // retrieve pool specific scrubs by pool id.
        return '/api/pools/' + this.get('pid') + '/scrub';
    }
});

var PoolScrubCollection = RockStorPaginatedCollection.extend({
    model: PoolScrub,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.snapType = options.snapType;
        }
    },
    // pid = Pool database id
    setUrl: function(pid) {
        this.baseUrl = '/api/pools/' + pid + '/scrub';
    },
    extraParams: function() {
        var p = this.constructor.__super__.extraParams.apply(this, arguments);
        p['snap_type'] = this.snapType;
        return p;
    }
});

var PoolRebalance = Backbone.Model.extend({
    url: function() {
        return '/api/pools/' + this.get('pid') + '/balance';
    }
});

var PoolRebalanceCollection = RockStorPaginatedCollection.extend({
    model: PoolRebalance,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.snapType = options.snapType;
        }
    },
    setUrl: function(pid) {
        this.baseUrl = '/api/pools/' + pid + '/balance';
    },
    extraParams: function() {
        var p = this.constructor.__super__.extraParams.apply(this, arguments);
        p['snap_type'] = this.snapType;
        return p;
    }
});

var SysInfo = Backbone.Model.extend({
    url: '/api/tools/sysinfo'
});

var NFSExport = Backbone.Model.extend();

var NFSExportCollection = RockStorPaginatedCollection.extend({
    model: NFSExport,
    setUrl: function(shareName) {
        this.baseUrl = '/api/shares/' + shareName + '/nfs';
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
    url: function() {
        return '/api/shares/' + this.get('shareName') + '/samba';
    }
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
    idAttribute: 'name',
    urlRoot: '/api/sm/services'
});

var ServiceCollection = RockStorPaginatedCollection.extend({
    model: Service,
    baseUrl: '/api/sm/services/'
});

var Appliance = Backbone.Model.extend({
    urlRoot: '/api/appliances'
});
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
    url: function() {
        return '/api/shares/' + this.get('shareName') + '/iscsi/';
    }
});

var DashboardConfig = Backbone.Model.extend({
    url: '/api/dashboardconfig',
    setConfig: function(wConfigs) {
        var tmp = [];
        _.each(wConfigs, function(wConfig) {
            tmp.push({
                name: wConfig.name,
                position: wConfig.position,
                maximized: wConfig.maximized
            });
        });
        this.set({
            widgets: JSON.stringify(tmp)
        });
    },

    getConfig: function() {
        if (!_.isUndefined(this.get('widgets')) && !_.isNull(this.get('widgets'))) {
            return JSON.parse(this.get('widgets'));
        }
        this.setConfig(RockStorWidgets.defaultWidgets());
        return JSON.parse(this.get('widgets'));
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
        }
        return {};
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
    dataUrl: function() {
        return '/api/sm/sprobes/' + this.get('name') + '/' + this.id + '/data?format=json';
    },
    downloadUrl: function() {
        return '/api/sm/sprobes/' + this.get('name') + '/' + this.id +
            '/data' + '?' +
            't1=' + this.get('start') + '&t2=' + this.get('end') +
            '&download=true';
    }
});

var ProbeRunCollection = RockStorPaginatedCollection.extend({
    model: ProbeRun,
    baseUrl: '/api/sm/sprobes/metadata'
});

var ProbeTemplate = Backbone.Model.extend({
    idAttribute: 'uuid'
});
var ProbeTemplateCollection = Backbone.Collection.extend({
    model: ProbeTemplate,
    url: '/api/sm/sprobes/?format=json'
});

var Replica = Backbone.Model.extend({
    urlRoot: '/api/sm/replicas'
});
var ReplicaCollection = RockStorPaginatedCollection.extend({
    model: Replica,
    baseUrl: '/api/sm/replicas/'
});

var ReplicaTrail = Backbone.Model.extend({
    urlRoot: '/api/sm/replicas/trail/replica/' + this.replicaId
});

var ReplicaTrailCollection = RockStorPaginatedCollection.extend({
    model: ReplicaTrail,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.replicaId = options.replicaId;
        }
    },
    baseUrl: function() {
        if (this.replicaId) {
            return '/api/sm/replicas/trail/replica/' + this.replicaId;
        }
        return '/api/sm/replicas/trail';
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
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.replicaShareId = options.replicaShareId;
        }
    },
    baseUrl: function() {
        if (this.replicaShareId) {
            return '/api/sm/replicas/rtrail/rshare/' + this.replicaShareId;
        }
        return '/api/sm/replicas/rtrail';
    }
});

var TaskDef = Backbone.Model.extend({
    urlRoot: '/api/sm/tasks/',
    max_count: function() {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).max_count;
        }
        return 0;
    },
    share: function() {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).share;
        }
        return '';
    },
    share_name: function() {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).share_name;
        }
        return '';
    },
    prefix: function() {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).prefix;
        }
        return '';
    },
    pool: function() {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).pool;
        }
        return '';
    },
    pool_name: function() {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).pool_name;
        }
        return '';
    },
    visible: function() {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).visible;
        }
        return false;
    },
    writable: function() {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).writable;
        }
        return false;
    },
    wakeup: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).wakeup;
        }
        return false;
    },
    rtc_hour: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).rtc_hour;
        }
        return 0;
    },
    rtc_minute: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).rtc_minute;
        }
        return 0;
    },
    ping_scan: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).ping_scan;
        }
        return false;
    },
    ping_scan_addresses: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).ping_scan_addresses;
        }
        return '';
    },
    ping_scan_interval: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).ping_scan_interval;
        }
        return 0;
    },
    ping_scan_iterations: function () {
        if (this.get('json_meta') != null) {
            return JSON.parse(this.get('json_meta')).ping_scan_iterations;
        }
        return 0;
    }

});

var TaskDefCollection = RockStorPaginatedCollection.extend({
    model: TaskDef,
    baseUrl: '/api/sm/tasks/'
});

var Task = Backbone.Model.extend({
    urlRoot: '/api/sm/tasks/log'
});

var TaskCollection = RockStorPaginatedCollection.extend({
    model: Task,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.taskDefId = options.taskDefId;
        }
    },
    baseUrl: function() {
        if (this.taskDefId) {
            return '/api/sm/tasks/log/taskdef/' + this.taskDefId;
        }
        return '/api/sm/tasks/log';
    }
});

var SFTP = Backbone.Model.extend({
    urlRoot: '/api/sftp'
});

var SFTPCollection = RockStorPaginatedCollection.extend({
    model: SFTP,
    baseUrl: '/api/sftp'
});


var ReplicaReceive = Backbone.Model.extend({
    urlRoot: '/api/sm/replicareceives'
});

var ReplicaReceiveCollection = RockStorPaginatedCollection.extend({
    model: ReplicaReceive,
    baseUrl: '/api/sm/replicareceives'
});

var ReplicaReceiveTrail = Backbone.Model.extend({
    urlRoot: '/api/sm/replicareceivetrail'
});

var ReplicaReceiveTrailCollection = RockStorPaginatedCollection.extend({
    model: ReplicaReceiveTrail,
    baseUrl: '/api/sm/replicareceivetrai'
});

var AdvancedNFSExport = Backbone.Model.extend();

var AdvancedNFSExportCollection = RockStorPaginatedCollection.extend({
    model: AdvancedNFSExport,
    baseUrl: '/api/adv-nfs-exports'
});


var AccessKey = Backbone.Model.extend({
    url: function() {
        return '/api/oauth_app';
    }
});

var AccessKeyCollection = RockStorPaginatedCollection.extend({
    model: AccessKey,
    baseUrl: '/api/oauth_app'
});

var Certificate = Backbone.Model.extend({
    urlRoot: '/api/certificate'
});

var ConfigBackup = Backbone.Model.extend({
    urlRoot: '/api/config-backup'
});

var ConfigBackupCollection = RockStorPaginatedCollection.extend({
    model: ConfigBackup,
    baseUrl: '/api/config-backup'
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
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function() {
        if (this.rid) {
            return '/api/rockons/volumes/' + this.rid;
        }
        return '/api/rockons/volumes';
    }
});

var RockOnPort = Backbone.Model.extend({
    urlRoot: '/api/rockon/ports/' + this.rid
});

var RockOnPortCollection = RockStorPaginatedCollection.extend({
    model: RockOnPort,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function() {
        if (this.rid) {
            return '/api/rockons/ports/' + this.rid;
        }
        return '/api/rockons/ports';
    }
});

var RockOnDevice = Backbone.Model.extend({
    urlRoot: '/api/rockon/devices/' + this.rid
});

var RockOnDeviceCollection = RockStorPaginatedCollection.extend({
    model: RockOnDevice,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function() {
        if (this.rid) {
            return '/api/rockons/devices/' + this.rid;
        }
        return '/api/rockons/devices';
    }
});

var RockOnLabel = Backbone.Model.extend({
    urlRoot: '/api/rockon/labels/' + this.rid
});

var RockOnLabelCollection = RockStorPaginatedCollection.extend({
    model: RockOnLabel,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function() {
        if (this.rid) {
            return '/api/rockons/labels/' + this.rid;
        }
        return '/api/rockons/labels';
    }
});

var RockOnCustomConfig = Backbone.Model.extend({
    urlRoot: '/api/rockon/customconfig/' + this.rid
});

var RockOnCustomConfigCollection = RockStorPaginatedCollection.extend({
    model: RockOnCustomConfig,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function() {
        if (this.rid) {
            return '/api/rockons/customconfig/' + this.rid;
        }
        return '/api/rockons/customconfig';
    }
});

var RockOnEnvironment = Backbone.Model.extend({
    urlRoot: '/api/rockon/environment/' + this.rid
});

var RockOnEnvironmentCollection = RockStorPaginatedCollection.extend({
    model: RockOnEnvironment,
    initialize: function(models, options) {
        this.constructor.__super__.initialize.apply(this, arguments);
        if (options) {
            this.rid = options.rid;
        }
    },
    baseUrl: function() {
        if (this.rid) {
            return '/api/rockons/environment/' + this.rid;
        }
        return '/api/rockons/environment';
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
