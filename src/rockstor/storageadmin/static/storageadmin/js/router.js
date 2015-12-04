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

// routes
var AppRouter = Backbone.Router.extend({
    initialize: function() {
	this.currentLayout = null;
    },

    routes: {
	"login": "loginPage",
	"setup": "doSetup",
	"home": "showHome",
	"disks": "showDisks",
	"disks/blink/:diskName": "blinkDrive",
	"disks/:diskName": "showDisk",
	"pools": "showPools",
	"pools/:poolName": "showPool",
	"pools/:poolName/?cView=:cView": "showPool",
	"add_pool": "addPool",
	"shares": "showShares",
	"add_share?poolName=:poolName": "addShare",
	"add_share": "addShare",
	"shares/:shareName": "showShare",
	"shares/:shareName/create-clone": "createCloneFromShare",
	"shares/:shareName/snapshots/:snapName/create-clone": "createCloneFromSnapshot",
	"shares/:shareName/rollback": "rollbackShare",
	"shares/:shareName/?cView=:cView": "showShare",
	"snapshots": "showSnapshots",
	"services": "showServices",
	"services/:serviceName/edit": "configureService",
	"support":"showSupport",
	"support/:supportCaseId": "showSupportCase",
	"add_support_case": "addSupportCase",
	"users": "showUsers",
	"users/:username/edit": "editUser",
	"add-user": "addUser",
	"groups": "showGroups",
	"groups/:groupname/edit": "editGroup",
	"add-group": "addGroup",
	"analytics": "showProbeRunList",
	"run_probe": "runProbe",
	"probeDetail/:probeName/:probeId": "showProbeDetail",
	"replication": "showReplication",
	"edit-replication-task/:replicaId": "editReplicationTask",
	"replication/:replicaId/trails": "showReplicaTrails",
	"replication-receive": "showReplicationReceives",
	"replication-receive/:replicaShareId/trails": "showReceiveTrails",
	"add_replication_task": "addReplicationTask",
	"nfs-exports": "showNFSExports",
	"nfs-advanced-edit": "nfsAdvancedEdit",
	"samba-exports": "showSambaExports",
	"add-samba-export": "addSambaExport",
	"samba/edit/:sambaShareId": "editSambaExport",
	"nfs-exports/edit/:nfsExportGroupId": "editNFSExport",
	"network": "showNetworks",
	"network/:name/edit": "editNetwork",
	"scheduled-tasks": "showScheduledTasks",
	"scheduled-tasks/:taskId/log": "showTasks",
	"add-scheduled-task": "addScheduledTask",
	"edit-scheduled-task/:taskDefId": "editScheduledTask",
	"update-certificate": "updateCertificate",
	"email": "showEmail",
	"email/:emailID/edit": "editEmail",
	"config-backup": "configBackup",
	"shutdown": "showShutdownView",
	"reboot": "showReboot",
	"version": "showVersion",
	"sftp": "showSFTP",
	"add-sftp-share": "addSFTPShare",
	"afp": "showAFP",
	"add-afp-share": "addAFPShare",
	"afp/edit/:afpShareId": "editAFPShare",
	"rockons": "showRockons",
	"images": "showImages",
	"containers": "showContainers",
	"appliances": "showAppliances",
	"add-appliance": "addAppliance",
	"access-keys": "showAccessKeys",
	"add-access-key": "addAccessKey",
	"404": "handle404",
	"500": "handle500",
	"*path": "showHome",
    },

    before: function (route, param) {
	if (!logged_in) {
	    if (route != "login") {
		app_router.navigate('login', {trigger: true});
		return false;
	    }
	} else {
	    if (route != "setup" && !setup_done) {
    		app_router.navigate('setup', {trigger: true});
    		return false;
	    } else if (route == "setup" && setup_done) {
    		app_router.navigate('home', {trigger: true});
		return false;
	    }
	}

	if (RockStorGlobals.currentAppliance == null) {
	    setApplianceName();
	}
	if (!RockStorGlobals.browserChecked) {
	    checkBrowser();
	}
    },


    loginPage: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("setup", "user");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new LoginView();
	$('#maincontent').append(this.currentLayout.render().el);

    },
    doSetup: function() {
	RockStorSocket.removeAllListeners();
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new SetupView();
	$('#maincontent').append(this.currentLayout.render().el);

    },

    showHome: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("dashboard", "dashboard");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new HomeLayoutView();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showDisks: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "disks");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new DisksView();
	$('#maincontent').append(this.currentLayout.render().el);

    },

    blinkDrive: function(diskName) {
	this.renderSidebar('storage', 'disks');
	this.cleanup();
	this.currentLayout = new BlinkDiskView({diskName: diskName});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showDisk: function(diskName) {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "disks");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new DiskDetailsLayoutView({
	    diskName: diskName
	});
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showPools: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "pools");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new PoolsView();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addPool: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "pools");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new AddPoolView();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showPool: function(poolName, cView) {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "pools");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new PoolDetailsLayoutView({
	    poolName: poolName,
	    cView: cView,
	});
	$('#maincontent').append(this.currentLayout.render().el);
    },

    //Support

    showSupport: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("support", "support");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new SupportView();
	$('#maincontent').append(this.currentLayout.render().el);
    },


    addSupportCase: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("support", "support");
	$('#maincontent').empty();
	$('#maincontent').append(addSupportCaseView.render().el);
    },

    showSupportCase: function(supportCaseId) {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("support", "support");

	var supportCaseDetailView = new SupportCaseDetailView({
	    model: new SupportCase({supportCaseId: supportCaseId})
	});
	$('#maincontent').empty();
	$('#maincontent').append(supportCaseDetailView.render().el);
    },


    //shares

    showShares: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "shares");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new SharesView();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showSnaps: function(shareName) {
	var snapshotsTableView = new SnapshotsTableView({
	    model: new Share({shareName: shareName})
	});
    },

    showSnap: function(shareName, snapName) {
	var snapshotsTableView = new SnapshotsTableView({
	    model: new Share({shareName: shareName})
	});
    },

    addShare: function(poolName) {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "shares");
	$('#maincontent').empty();
	this.cleanup();
	if (_.isUndefined(poolName)){
    	    this.currentLayout = new AddShareView();
	} else {
	    this.currentLayout = new AddShareView({ poolName: poolName });
	}
	$('#maincontent').append(this.currentLayout.render().el);

    },

    showShare: function(shareName, cView) {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "shares");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new ShareDetailsLayoutView({
	    shareName: shareName,
	    cView: cView,
	});
	$('#maincontent').append(this.currentLayout.render().el);
    },

    deleteShare: function(shareName) {

    },

    showSnapshots: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "snapshots");
	$('#maincontent').empty();
	this.cleanup();
	this.currentLayout = new SnapshotsView();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showServices: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("system", "services");
	this.cleanup();
	this.currentLayout = new ServicesView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);

    },

    configureService: function(serviceName) {
	this.renderSidebar("system", "services");
	this.cleanup();
	this.currentLayout = new ConfigureServiceView({serviceName: serviceName});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showUsers: function() {
	this.renderSidebar("system", "users");
	this.cleanup();
	this.currentLayout = new UsersView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addUser: function() {
	this.renderSidebar("system", "users");
	this.cleanup();
	this.currentLayout = new AddUserView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    editUser: function(username) {
	this.renderSidebar("system", "users");
	this.cleanup();
	this.currentLayout = new AddUserView({username: username});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showGroups: function() {
	this.renderSidebar("system", "groups");
	this.cleanup();
	this.currentLayout = new GroupsView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addGroup: function() {
	this.renderSidebar("system", "groups");
	this.cleanup();
	this.currentLayout = new AddGroupView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    editGroup: function() {
	this.renderSidebar("system", "groups");
	this.cleanup();
	this.currentLayout = new AddGroupView({groupname: groupname});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showProbeRunList: function() {
	this.renderSidebar("analytics", "probe_runs");
	this.cleanup();
	this.currentLayout = new ProbeRunListView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    runProbe: function() {
	this.renderSidebar("analytics", "run_probe");
	this.cleanup();
	this.currentLayout = new RunProbeView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showProbeDetail: function(probeName, probeId) {
	this.cleanup();
	this.currentLayout = new ProbeDetailView({
	    probeId: probeId,
	    probeName: probeName
	});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    renderSidebar: function(name, selected) {
	var sidenavTemplate = window.JST["common_sidenav_" + name];
	$("#sidebar-inner").html(sidenavTemplate({selected: selected}));
    },

    showReplication: function() {
	this.renderSidebar("storage", "replication");
	this.cleanup();
	this.currentLayout = new ReplicationView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    editReplicationTask: function(replicaId) {
	this.renderSidebar('storage', 'replication');
	this.cleanup();
	this.currentLayout = new AddReplicationTaskView({replicaId: replicaId});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showReplicaTrails: function(replicaId) {
	this.renderSidebar("storage", "replication");
	this.cleanup();
	this.currentLayout = new ReplicaTrailsView({
	    replicaId: replicaId
	});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addReplicationTask: function() {
	this.renderSidebar("storage", "replication");
	this.cleanup();
	this.currentLayout = new AddReplicationTaskView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showReplicationReceives: function() {
	this.renderSidebar("storage", "replication-receive");
	this.cleanup();
	this.currentLayout = new ReplicationReceiveView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showReceiveTrails: function(replicaShareId) {
	this.renderSidebar("storage", "replication-receive");
	this.cleanup();
	this.currentLayout = new ReplicaReceiveTrailsView({
	    replicaShareId: replicaShareId
	});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showNFSExports: function() {
	this.renderSidebar('storage', 'nfs-exports');
	this.cleanup();
	this.currentLayout = new NFSExportsView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    nfsAdvancedEdit: function() {
	this.renderSidebar('storage', 'nfs-exports');
	this.cleanup();
	this.currentLayout = new NFSAdvancedEditView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    editNFSExport: function(nfsExportGroupId) {
	this.renderSidebar('storage', 'nfs-exports');
	this.cleanup();
	this.currentLayout = new EditNFSExportView({
	    nfsExportGroupId: nfsExportGroupId
	});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showNetworks: function() {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("system", "network");
	this.cleanup();
	this.currentLayout = new NetworksView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    editNetwork: function(name) {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("system", "network");
	this.cleanup();
	this.currentLayout = new EditNetworkView({name: name});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    createCloneFromShare: function(shareName) {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "shares");
	this.cleanup();
	this.currentLayout = new CreateCloneView({
	    sourceType: 'share',
	    shareName: shareName
	});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    createCloneFromSnapshot: function(shareName, snapName) {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "shares");
	this.cleanup();
	this.currentLayout = new CreateCloneView({
	    sourceType: 'snapshot',
	    shareName: shareName,
	    snapName: snapName
	});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    rollbackShare: function(shareName) {
	RockStorSocket.removeAllListeners();
	this.renderSidebar("storage", "shares");
	this.cleanup();
	this.currentLayout = new RollbackView({
	    shareName: shareName,
	});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showScheduledTasks: function() {
	this.renderSidebar('system', 'scheduled-tasks');
	this.cleanup();
	this.currentLayout = new ScheduledTasksView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addScheduledTask: function() {
	this.renderSidebar('system', 'scheduled-tasks');
	this.cleanup();
	this.currentLayout = new AddScheduledTaskView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    editScheduledTask: function(taskDefId) {
	this.renderSidebar('system', 'scheduled-tasks');
	this.cleanup();
	this.currentLayout = new AddScheduledTaskView({taskDefId: taskDefId});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    updateCertificate: function() {
	this.renderSidebar('system', 'update-certificate');
	this.cleanup();
	this.currentLayout = new UpdateCertificateView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    configBackup: function() {
	this.renderSidebar('system', 'config-backup');
	this.cleanup();
	this.currentLayout = new ConfigBackupView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showTasks: function(taskDefId) {
	this.renderSidebar("system", "scheduled-tasks");
	this.cleanup();
	this.currentLayout = new TasksView({
	    taskDefId: taskDefId
	});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showSambaExports: function() {
	this.renderSidebar('storage', 'samba');
	this.cleanup();
	this.currentLayout = new SambaView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addSambaExport: function() {
	this.renderSidebar('storage', 'samba');
	this.cleanup();
	this.currentLayout = new AddSambaExportView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    editSambaExport: function(sambaShareId) {
	this.renderSidebar('storage', 'samba');
	this.cleanup();
	this.currentLayout = new AddSambaExportView({sambaShareId: sambaShareId});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },


    showSFTP: function() {
	this.renderSidebar('storage', 'sftp');
	this.cleanup();
	this.currentLayout = new SFTPView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addSFTPShare: function() {
	this.renderSidebar('storage', 'sftp');
	this.cleanup();
	this.currentLayout = new AddSFTPShareView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showAFP: function() {
	this.renderSidebar('storage', 'afp');
	this.cleanup();
	this.currentLayout = new AFPView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addAFPShare: function() {
	this.renderSidebar('storage', 'afp');
	this.cleanup();
	this.currentLayout = new AddAFPShareView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    editAFPShare: function(afpShareId) {
	this.renderSidebar('storage', 'afp');
	this.cleanup();
	this.currentLayout = new AddAFPShareView({afpShareId: afpShareId});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showVersion: function() {
	this.renderSidebar("system", "version");
	this.cleanup();
	this.currentLayout = new VersionView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showShutdownView: function() {
	this.cleanup();
	this.currentLayout = new ShutdownView();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showReboot: function() {
	this.cleanup();
	this.currentLayout = new RebootView();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showRockons: function() {
	this.renderSidebar("rockons", "rockons");
	this.cleanup();
	this.currentLayout = new RockonsView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showImages: function() {
	this.renderSidebar("rockons", "images");
	this.cleanup();
	this.currentLayout = new ImagesView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showContainers: function() {
	this.renderSidebar("rockons", "containers");
	this.cleanup();
	this.currentLayout = new ContainersView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showAppliances: function() {
	this.renderSidebar("system", "appliances");
	this.cleanup();
	this.currentLayout = new AppliancesView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addAppliance: function() {
	this.renderSidebar("system", "appliances");
	this.cleanup();
	this.currentLayout = new AddApplianceView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    showAccessKeys: function() {
	this.renderSidebar("system", "access-keys");
	this.cleanup();
	this.currentLayout = new AccessKeysView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    addAccessKey: function() {
	this.renderSidebar("system", "access-keys");
	this.cleanup();
	this.currentLayout = new AddAccessKeyView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    handle404: function() {
	this.cleanup();
	this.currentLayout = new Handle404View();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    handle500: function() {
	this.cleanup();
	this.currentLayout = new Handle500View();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    cleanup: function() {
	hideMessage();
	RockStorSocket.removeAllListeners();
	if (!_.isNull(this.currentLayout)) {
	    if (_.isFunction(this.currentLayout.cleanup)) {
		this.currentLayout.cleanup();
	    }
	}
    },

    showEmail: function() {
	this.renderSidebar('system', 'email');
	this.cleanup();
	this.currentLayout = new EmailView();
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    },

    editEmail: function(emailID) {
        this.renderSidebar("system", "email");
	this.cleanup();
	this.currentLayout = new EmailView({emailID: emailID});
	$('#maincontent').empty();
	$('#maincontent').append(this.currentLayout.render().el);
    }

});

// Initiate the router
var app_router = new AppRouter;
// ###Render the view###
// On document load, render the view.
$(document).ready(function() {
    // Start Backbone history a neccesary step for bookmarkable URL's
    if (!RockStorGlobals.navbarLoaded) {
	refreshNavbar();
    }
    Backbone.history.start();
    $('#appliance-name').click(function(event) {
	event.preventDefault();
	//showApplianceList();
	app_router.navigate('appliances', {trigger: true});
    });

    // Global ajax error handler
    $(document).ajaxError(function(event, jqXhr, ajaxSettings, e) {
	var commonerr_template = window.JST.common_commonerr;
	var popuperrTemplate = window.JST.common_popuperr;
	var unknownerr_template = window.JST.common_unknownerr;
	var htmlErr = null;
	var resType = jqXhr.getResponseHeader('Content-Type');
	var detail = jqXhr.responseText;
	var errJson = {};
	if (jqXhr.status != 403) {
	    // dont show forbidden errors (for setup screen)
	    if (jqXhr.getResponseHeader('Content-Type').match(/json/)) {
		errJson = getXhrErrorJson(jqXhr);
		detail = errJson.detail;
	    } else if (jqXhr.status >= 400 && jqXhr.status < 500) {
		detail = 'Unknown client error doing a ' + ajaxSettings.type + ' to ' + ajaxSettings.url;
	    } else if (jqXhr.status >= 500 && jqXhr.status < 600) {
		detail = 'Unknown internal error doing a ' + ajaxSettings.type + ' to ' + ajaxSettings.url;
	    }
	    if (ajaxSettings.type == 'GET') {
		$("#globalerrmsg").html(commonerr_template({
		    jqXhr: jqXhr,
		    detail: detail,
		    help: errJson.help,
		    ajaxSettings: ajaxSettings
		}));
	    } else {
		$('.overlay-content', '#global-err-overlay').html(popuperrTemplate({
		    detail: detail
		}));
		$('#global-err-overlay').overlay().load();
	    }
	}
    });

    $('#global-err-overlay').on('click', '.err-help-toggle', function(event) {
	if (event) event.preventDefault();
	var displayed = $('.err-help', '#global-err-overlay').css('display') == 'block';
	var display = displayed ? 'none' : 'block';
	$('.err-help', '#global-err-overlay').css('display', display);
	var val = displayed ? 'More...' : 'Close';
	$('.err-help-toggle', '#global-err-overlay').html(val);
    });

    $('#globalerrmsg').on('click', '.err-help-toggle', function(event) {
	if (event) event.preventDefault();
	var displayed = $('.err-help').css('display') == 'block';
	var display = displayed ? 'none' : 'block';
	$('.err-help').css('display', display);
	var val = displayed ? 'More...' : 'Close';
	$('.err-help-toggle').html(val);
    });

    $('#globalerrmsg').on('click', '.close', function(event) {
	if (event) event.preventDefault();
	$('#globalerrmsg').empty();
    });


    // Initialize global error popup
    $('#global-err-overlay').overlay({load: false});

    // handle btn navbar toggle ourselves since bootstrap collapse
    // seems to conflict with something
    $('body').on('click.collapse.data-api', '[data-toggle=mycollapse]', function ( e ) {
	var $this = $(this), target = $this.attr('data-target');
	var h = $(target).css('height');
	if (!($(target).hasClass('in'))) {
	    $(target).addClass('in');
	    $(target).css('height', 'auto');
	} else {
	    $(target).removeClass('in');
	    $(target).css('height', '0');
	}
    });

    // donate button handler
    $('#donate_nav').click(function(event) {
	if (event) {
	    event.preventDefault();
	}
	$('#donate-modal').modal('show');
    });

    $('#donate-modal #contrib-custom').click(function(e) {
	$('#donate-modal #custom-amount').css('display', 'inline');
    });
    $('#donate-modal .contrib-other').click(function(e) {
	$('#donate-modal #custom-amount').css('display', 'none');
    });

    $('#donate-modal #donateYes').click(function(event) {
	contrib = $('#donate-modal input[type="radio"][name="contrib"]:checked').val();
	if (contrib=='custom') {
	    contrib = $('#custom-amount').val();
	}
	if (_.isNull(contrib) || _.isEmpty(contrib) || isNaN(contrib)) {
	    contrib = 0; // set contrib to 0, let user input the number on paypal
	}
	$('#contrib-form input[name="amount"]').val(contrib);
	$('#contrib-form').submit();
	$('#donate-modal').modal('hide');
    });

    /********** Websockets **************/
    // These are global websocket events

    // Grab the far right of the breadcrumb (under nav)
    var $loadavg = $('#appliance-loadavg');

    var kernelInfo = function(data) {
	$loadavg.text('Linux: ' + data);
    };

    var displayLoadAvg = function(data) {
	var n = parseInt(data);
	var secs = n % 60;
	var mins = Math.round(n/60) % 60;
	var hrs = Math.round(n / (60*60)) % 24;
	var days = Math.round(n / (60*60*24)) % 365;
	var yrs = Math.round(n / (60*60*24*365));
	var str = 'Uptime: ';
	if (yrs == 1) {
	    str += yrs + ' year, ';
	} else if (yrs > 1) {
	    str += yrs + ' years, ';
	}
	if (days == 1) {
	    str += days + ' day, ';
	} else if (days > 1) {
	    str += days + ' days, ';
	}
	if (hrs < 10) {
	    str += '0';
	}
	str += hrs + ':';
	if (mins < 10) {
	    str += '0';
	}
	str += mins;
	$('#uptime').text(str);
    };

    var displayUpdate = function(data) {
	var currentVersion = data[0];
	var mostRecentVersion = data[1];
	if (currentVersion != mostRecentVersion) {
	    $('#version-msg').html('RockStor ' + currentVersion + ' <i class="glyphicon glyphicon-arrow-up"></i>');
	} else {
	    $('#version-msg').html('RockStor ' + currentVersion);
	}
    };


    var kernelError = function(data) {
	// If 'kernel' does not show up in the string, we're ok
	if (data.indexOf('kernel') !== -1) {
	    // Put an alert at the top of the page
	    $('#browsermsg').html('<div class="alert alert-danger"><button type="button" class="close" data-dismiss="alert">&times;</button>' + data + '</div>');
	}
    };


    RockStorSocket.addListener(kernelInfo, this, 'sysinfo:kernel_info');
    RockStorSocket.addListener(displayLoadAvg, this, 'sysinfo:uptime');
    RockStorSocket.addListener(kernelError, this, 'sysinfo:kernel_error');
    RockStorSocket.addListener(displayUpdate, this, 'sysinfo:software-update');

    RockStorSocket.sysinfo.on('kernel_error', function(data) {
	// Handling errors just by emitting message via the server
	if (data.error.indexOf('kernel') !== -1) {
	    // Put an alert at the top of the page
	    $('#browsermsg').html('<div class="alert alert-danger"><button type="button" class="close" data-dismiss="alert">&times;</button>' + data.error + '</div>');
	}

    });

    //insert pagination partial helper functions here
    Handlebars.registerHelper('pagination', function() {

      var totalPageCount = this.collection.pageInfo().num_pages,
          currPageNumber = this.collection.pageInfo().page_number,
          maxEntriesPerPage = this.collection.pageSize,
          totalEntryCount = this.collection.count,
          pagePrev = this.collection.pageInfo().prev,
          pageNext = this.collection.pageInfo().next,
          backwardIcon = '<i class="glyphicon glyphicon-backward"></i>',
          fastBackwardIcon = '<i class="glyphicon glyphicon-fast-backward"></i>',
          forwardIcon = '<i class="glyphicon glyphicon-forward"></i>',
          fastForwardIcon = '<i class="glyphicon glyphicon-fast-forward"></i>'
          html = '',
          entries = currPageNumber * maxEntriesPerPage,
          entry_prefix = 0;

          if (totalPageCount > 1) {
            html += '<nav>';
            if(currPageNumber * maxEntriesPerPage > totalEntryCount){
              entries = totalEntryCount;
            }
            entry_prefix = (currPageNumber - 1) * (maxEntriesPerPage) + 1 ;

            html += '<p><i>Displaying entries ' + entry_prefix + ' - ' + (entries) + ' of ' + totalEntryCount + '</i></p>';
            html += '<ul class="pagination">';
            html += '<li><a class="go-to-page" href="#" data-page="1">' + fastBackwardIcon + '</a></li>';
            if (pagePrev) {
              html += '<li><a class="prev-page" href="#">' + backwardIcon + '</a></li>';
            } else {
              html += '<li class="disabled"><a class="prev-page" href="#">' + backwardIcon + '</a></li>';
            }

            var start = currPageNumber - 4 ;
            if(start <= 0){
              start = 1;
            }
            var end = start + 9;
            if(end > totalPageCount){
              end = totalPageCount;
            }
            for (var i=start; i<= end; i++) {
              if (i == currPageNumber) {
                  html += '<li class="active"><a class="go-to-page" href="#" data-page="' + i + '">' + i + '</a></li>';
              } else {
                  html += '<li><a class="go-to-page" href="#" data-page="' + i + '">' + i + '</a></li>';
              }
            }
            if (pageNext) {
                html += '<li><a class="next-page" href="#">' + fastForwardIcon + '</a></li>';
            } else {
                html += '<li class="disabled"><a class="next-page" href="#">' + forwardIcon + '</a></li>';
            }
              html += '<li><a class="go-to-page" href="#" data-page="' + totalPageCount + '">'+ fastForwardIcon +'</a></li>';
              html += '</ul>';
              html += '</nav>';
         }

        return new Handlebars.SafeString(html);
    });

});
