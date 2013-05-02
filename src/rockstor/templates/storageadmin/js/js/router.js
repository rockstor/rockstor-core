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
    "setup": "doSetup",
    "home": "showHome",
    "disks": "showDisks",
    "pools": "showPools",
    "pools/:poolName": "showPool",
    "add_pool": "addPool",
    "shares": "showShares",
    "add_share": "addShare",
    "shares/:shareName": "showShare",
    "shares/:shareName/:snapshots": "showSnaps",
    "shares/:shareName/:snapshots/:snapName": "showSnap",
    "services": "showServices",
    "support":"showSupport",
    "support/:supportCaseId": "showSupportCase",
    "add_support_case": "addSupportCase",
    "*path": "showHome"
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
    $('#maincontent').empty();
    this.cleanup();
    this.currentLayout = new HomeLayoutView();
    $('#maincontent').append(this.currentLayout.render().el);
  },
  
  showDisks: function() {
    RockStorSocket.removeAllListeners();
    $('#maincontent').empty();
    this.cleanup();
    this.currentLayout = new DisksView();
    $('#maincontent').append(this.currentLayout.render().el);
  },
  
  showPools: function() {
    RockStorSocket.removeAllListeners();
    $('#maincontent').empty();
    this.cleanup();
    this.currentLayout = new PoolsView();
    $('#maincontent').append(this.currentLayout.render().el);
  },

  addPool: function() {
    RockStorSocket.removeAllListeners();
    $('#maincontent').empty();
    $('#maincontent').append(addPoolView.render().el);
  },

  showPool: function(poolName) {
    RockStorSocket.removeAllListeners();
    var poolDetailsLayoutView = new PoolDetailsLayoutView({
      poolName: poolName
    });
    $('#maincontent').empty();
    $('#maincontent').append(poolDetailsLayoutView.render().el);
  },
  
  //Support
  
  showSupport: function() {
	    RockStorSocket.removeAllListeners();
	    $('#maincontent').empty();
	    this.cleanup();
	    this.currentLayout = new SupportView();
	    $('#maincontent').append(this.currentLayout.render().el);
	  },


  addSupportCase: function() {
	    RockStorSocket.removeAllListeners();
	    $('#maincontent').empty();
	    $('#maincontent').append(addSupportCaseView.render().el);
	  },

  showSupportCase: function(supportCaseId) {
	    RockStorSocket.removeAllListeners();

		var supportCaseDetailView = new SupportCaseDetailView({
		  model: new SupportCase({supportCaseId: supportCaseId})
		});
		$('#maincontent').empty();
		$('#maincontent').append(supportCaseDetailView.render().el);
	  },
  

  //shares
  
  showShares: function() {
    RockStorSocket.removeAllListeners();
    $('#maincontent').empty();
    this.cleanup();
    this.currentLayout = new SharesLayoutView();
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
  addShare: function() {
    RockStorSocket.removeAllListeners();
    $('#maincontent').empty();
    $('#maincontent').append(addShareView.render().el);
  },
  showShare: function(shareName) {
    RockStorSocket.removeAllListeners();
    //var shareDetailView = new ShareDetailView({
      //model: new Share({shareName: shareName})
    //});
    var shareDetailsLayoutView = new ShareDetailsLayoutView({
      shareName: shareName 
    });

    $('#maincontent').empty();
    //$('#maincontent').append(shareDetailView.render().el);
    $('#maincontent').append(shareDetailsLayoutView.render().el);

  },
  deleteShare: function(shareName) {

  },
  showServices: function() {
    RockStorSocket.removeAllListeners();
    this.cleanup();
    this.currentLayout = new ServicesView();
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
  }
  
});

// Initiate the router
var app_router = new AppRouter;
// ###Render the view###
// On document load, render the view.
$(document).ready(function() {
  // Start Backbone history a neccesary step for bookmarkable URL's
  Backbone.history.start();
  $('#appliance-name').click(function(event) {
    event.preventDefault();
    console.log('appliance-name clicked');
    showApplianceList();
  });

  // Initialize websocket connection
  // logger.debug('connecting to websocket');
  // RockStorSocket.socket = io.connect('https://' + document.location.host + ':' + NGINX_WEBSOCKET_PORT, 
    // {secure: true}
  // );
  // RockStorSocket.socket.on('sm_data', RockStorSocket.msgHandler);
  
});

