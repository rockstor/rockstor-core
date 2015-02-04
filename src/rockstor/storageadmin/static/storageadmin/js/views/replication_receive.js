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

ReplicationReceiveView = RockstorLayoutView.extend({
	events: {
	'click .slider-stop': "stopService",
	'click .slider-start': "startService"
},

initialize: function() {
	// call initialize of base
	this.constructor.__super__.initialize.apply(this, arguments);
	// set template
	this.template = window.JST.replication_replication_receive;
	this.paginationTemplate = window.JST.common_pagination;
	this.serviceName = 'replication';
	this.replicationService = new Service({name: this.serviceName});
	this.dependencies.push(this.replicationService);
	this.collection = new ReplicaShareCollection();
	this.dependencies.push(this.collection);
	this.replicaReceiveTrails = new ReceiveTrailCollection();
	this.replicaReceiveTrails.pageSize = RockStorGlobals.maxPageSize;
	this.dependencies.push(this.replicaReceiveTrails);
	this.updateFreq = 5000;
	this.replicaReceiveTrailMap = {};
},

render: function() {
	var _this = this;
	// TODO fetch from backend when api is ready
	/*
    this.collection  = new ReplicaReceiveCollection([
      { source_task_name: 'task1',  source_appliance: '192.168.1.111', source_share: 'share1', destination_pool: 'reptarget', destination_share: 'share1_replica', last_run: ''},
      { id: 1, source_task_name: 'task2',  source_appliance: '192.168.1.111', source_share: 'share2', destination_pool: 'reptarget', destination_share: 'share2_replica', last_run: ''},
    ]);
    this.replicaReceiveTrails = new ReplicaReceiveTrailCollection([
      {id: 1, "replicaReceive": 1, "snap_name": "share2_replica_snap_8", "kb_sent": 133, "snapshot_created": "2014-01-30T19:53:33.094Z", "snapshot_failed": null, "send_pending": null, "send_succeeded": null, "send_failed": null, "end_ts": "2014-01-30T19:53:35.150Z", "status": "succeeded", "error": null}
    ]);
	 */
	this.fetch(this.renderReceives, this);
	return this;
},

renderReceives: function() {
	var _this = this;
	// Construct map for receive -> trail
	this.collection.each(function(replicaShare, index) {
		var tmp = _this.replicaReceiveTrails.filter(function(replicaReceiveTrail) {
			return replicaReceiveTrail.get('rshare') == replicaShare.id;
		});
		tmp = tmp.filter(function(replicaReceiveTrail) {
			return replicaReceiveTrail.get('end_ts') != null;
		});
		_this.replicaReceiveTrailMap[replicaShare.id] = _.sortBy(tmp, function(replicaReceiveTrail) {
			return moment(replicaReceiveTrail.get('end_ts')).valueOf();
		}).reverse();
	});
	$(this.el).html(this.template({
		replicationService: this.replicationService,
		replicaShares: this.collection,
		replicaReceiveTrailMap: this.replicaReceiveTrailMap
	}));
	this.$(".ph-pagination").html(this.paginationTemplate({
		collection: this.collection
	}));
	this.$('#replica-receives-table').tablesorter();

	this.$('input.service-status').simpleSlider({
		"theme": "volume",
		allowedValues: [0,1],
		snap: true 
	});

	this.$('input.service-status').each(function(i, el) {
		var slider = $(el).data('slider-object');
		// disable track and dragger events to disable slider
		slider.trackEvent = function(e) {};
		slider.dragger.unbind('mousedown');
	});
	this.displayReplicationWarning(this.serviceName);

},
startService: function(event) {
	var _this = this;
	var serviceName = this.serviceName; 
	// if already started, return
	if (this.getSliderVal(serviceName).toString() == "1") return; 
	this.stopPolling();
	this.setStatusLoading(serviceName, true);
	$.ajax({
		url: "/api/sm/services/replication/start",
		type: "POST",
		dataType: "json",
		success: function(data, status, xhr) {
		_this.highlightStartEl(serviceName, true);
		_this.setSliderVal(serviceName, 1); 
		_this.setStatusLoading(serviceName, false);
		_this.startPolling();
		_this.displayReplicationWarning(serviceName);
	},
	error: function(xhr, status, error) {
		_this.setStatusError(serviceName, xhr);
		_this.startPolling();
	}
	});
},

stopService: function(event) {
	var _this = this;
	var serviceName = $(event.currentTarget).data('service-name'); 
	// if already stopped, return
	if (this.getSliderVal(serviceName).toString() == "0") return; 
	this.stopPolling();
	this.setStatusLoading(serviceName, true);
	$.ajax({
		url: "/api/sm/services/replication/stop",
		type: "POST",
		dataType: "json",
		success: function(data, status, xhr) {
		_this.highlightStartEl(serviceName, false);
		_this.setSliderVal(serviceName, 0); 
		_this.setStatusLoading(serviceName, false);
		_this.startPolling();
		_this.displayReplicationWarning(serviceName);
	},
	error: function(xhr, status, error) {
		_this.setStatusError(serviceName, xhr);
		_this.startPolling();
	}
	});
},

highlightStartEl: function(serviceName, on) {
	var startEl = this.$('div.slider-start[data-service-name="'+serviceName+'"]');
	if (on) {
		startEl.addClass('on');
	} else {
		startEl.removeClass('on');
	}
},

setStatusLoading: function(serviceName, show) {
	var statusEl = this.$('div.command-status[data-service-name="'+serviceName+'"]');
	if (show) {
		statusEl.html('<img src="/static/storageadmin/img/ajax-loader.gif"></img>');
	} else {
		statusEl.empty();
	}
},

startPolling: function() {
	var _this = this;
	// start after updateFreq
	this.timeoutId = window.setTimeout(function() {
		_this.updateStatus();
	}, this.updateFreq);
},

updateStatus: function() {
	var _this = this;
	_this.startTime = new Date().getTime();
	_this.replicationService.fetch({
		silent: true,
		success: function(service, response, options) {
		var serviceName = service.get('name');
		if (service.get('status')) {
			_this.highlightStartEl(serviceName, true);
			_this.setSliderVal(serviceName, 1); 
		} else {
			_this.highlightStartEl(serviceName, false);
			_this.setSliderVal(serviceName, 0); 
		}
		var currentTime = new Date().getTime();
		var diff = currentTime - _this.startTime;
		// if diff > updateFreq, make next call immediately
		if (diff > _this.updateFreq) {
			_this.updateStatus();
		} else {
			// wait till updateFreq msec has elapsed since startTime
			_this.timeoutId = window.setTimeout( function() { 
				_this.updateStatus();
			}, _this.updateFreq - diff);
		}
	}
	});
},

stopPolling: function() {
	if (!_.isUndefined(this.timeoutId)) {
		window.clearInterval(this.timeoutId);
	}
},

setStatusError: function(serviceName, xhr) {
	var statusEl = this.$('div.command-status[data-service-name="' + serviceName + '"]');
	var msg = parseXhrError(xhr);
	// remove any existing error popups
	$('body').find('#' + serviceName + 'err-popup').remove();
	// add icon and popup
	statusEl.empty();
	var icon = $('<i>').addClass('icon-exclamation-sign').attr('rel', '#' + serviceName + '-err-popup');
	statusEl.append(icon);
	var errPopup = this.$('#' + serviceName + '-err-popup');
	var errPopupContent = this.$('#' + serviceName + '-err-popup > div');
	errPopupContent.html(msg);
	statusEl.click(function(){ errPopup.overlay().load(); });
},

setSliderVal: function(serviceName, val) {
	this.$('input[data-service-name='+serviceName+']').simpleSlider('setValue',val);
},

getSliderVal: function(serviceName) {
	return this.$('input[data-service-name='+serviceName+']').data('slider-object').value;
},

displayReplicationWarning: function(serviceName) {
	if (this.getSliderVal(serviceName).toString() == "0") {
		this.$('#replication-warning').show();
	} else {
		this.$('#replication-warning').hide();
	}
},

cleanup: function() {
	this.stopPolling();
}	  

});

// Add pagination
Cocktail.mixin(ReplicationReceiveView, PaginationMixin);


