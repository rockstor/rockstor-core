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

ReplicationView = RockstorLayoutView.extend({
    events: {
	'click a[data-action=delete]': 'deleteTask',
	'switchChange.bootstrapSwitch': 'switchStatus',
    },

    initialize: function() {
    	// call initialize of base
    	this.constructor.__super__.initialize.apply(this, arguments);
    	// set template
    	this.template = window.JST.replication_replication;
    	this.paginationTemplate = window.JST.common_pagination;
    	// add dependencies
    	this.collection = new ReplicaCollection();
    	this.dependencies.push(this.collection);
    	this.serviceName = 'replication';
    	this.replicationService = new Service({name: this.serviceName});
    	this.dependencies.push(this.replicationService);
    	this.replicaTrails = new ReplicaTrailCollection();
    	this.replicaTrails.pageSize = RockStorGlobals.maxPageSize;
    	this.dependencies.push(this.replicaTrails);
    	this.appliances = new ApplianceCollection();
    	this.dependencies.push(this.appliances);
    	this.shares = new ShareCollection();
    	this.dependencies.push(this.shares);
    	this.replicaShareMap = {};
    	this.replicaTrailMap = {};
    	this.collection.on('reset', this.renderReplicas, this);
    },

    render: function() {
    	this.fetch(this.renderReplicas, this);
    	return this;
    },

    renderReplicas: function() {
    	var _this = this;
    	this.otherAppliances =  this.appliances.filter(function(appliance) {
    	    return appliance.get('current_appliance') == false;
    	});
    	this.freeShares = this.shares.reject(function(share) {
    	    return !_.isUndefined(_this.collection.find(function(replica) {
    		return replica.get('share') == share.get('name');
    	    })) ;
    	});
    	// remove existing tooltips
    	if (this.$('[rel=tooltip]')) {
    	    this.$('[rel=tooltip]').tooltip('hide');
    	}
    	var shares = this.collection.map(function(replica) {
    	    return replica.get('share');
    	});
    	_.each(shares, function(share) {
    	    _this.replicaShareMap[share] = _this.collection.filter(function(replica) {
    		return replica.get('share') == share;
    	    });
    	});
    	this.collection.each(function(replica, index) {
    	    var tmp = _this.replicaTrails.filter(function(replicaTrail) {
    		return replicaTrail.get('replica') == replica.id;
    	    });
    	    _this.replicaTrailMap[replica.id] = _.sortBy(tmp, function(replicaTrail) {
    		return moment(replicaTrail.get('snapshot_created')).valueOf();
    	    }).reverse();
    	});
    	$(this.el).html(this.template({
    	    replicationService: this.replicationService,
    	    replicas: this.collection,
    	    replicaShareMap: this.replicaShareMap,
    	    replicaTrailMap: this.replicaTrailMap,
    	    otherAppliances: this.otherAppliances,
    	    freeShares: this.freeShares
    	}));

	//initalize Bootstrap Switch
	this.$("[type='checkbox']").bootstrapSwitch();
	if (typeof this.current_status == 'undefined') {
            this.current_status = this.replicationService.get('status');
	}
	this.$('input[name="replica-service-checkbox"]').bootstrapSwitch('state', this.current_status, true);
	this.$("[type='checkbox']").bootstrapSwitch('onColor','success'); //left side text color
	this.$("[type='checkbox']").bootstrapSwitch('offColor','danger'); //right side text color

	// Display Service Warning
    	if (!this.current_status) {
    	    this.$('#replication-warning').show();
    	} else {
    	    this.$('#replication-warning').hide();
    	}

    	this.$('[rel=tooltip]').tooltip({ placement: 'bottom'});
    	this.$(".ph-pagination").html(this.paginationTemplate({
    	    collection: this.collection
    	}));
    	this.$('#replicas-table').tablesorter();
    },

    switchStatus: function(event,state){
	//the bootsrap switch can either be Service or Status Switch
	var replicaSwitchName = $(event.target).attr('name');
	if (replicaSwitchName == "replica-service-checkbox"){
            if (state){
		this.startService();
            }else {
		this.stopService();
            }
	} else if(replicaSwitchName == "replica-task-checkbox"){
            var replicaId = $(event.target).attr('data-replica-id');
            if (state){
		this.enable(replicaId);
            }else {
		this.disable(replicaId);
            }
	}
    },

    enable: function(replicaId) {
    	var _this = this;
    	$.ajax({
    	    url: '/api/sm/replicas/' + replicaId,
    	    type: 'PUT',
    	    dataType: 'json',
    	    contentType: 'application/json',
    	    data: JSON.stringify({enabled: true}),
    	    success: function() {
    		_this.collection.fetch({
    		    success: function() {
    			_this.renderReplicas();
    		    }
    		});
    	    },
    	    error: function(xhr, status, error) {
    	    }
    	});
    },

    disable: function(replicaId) {
	var _this = this;
    	$.ajax({
    	    url: '/api/sm/replicas/' + replicaId,
    	    type: 'PUT',
    	    dataType: 'json',
    	    contentType: 'application/json',
    	    data: JSON.stringify({enabled: false}),
    	    success: function() {
    		_this.collection.fetch({
    		    success: function() {
    			_this.renderReplicas();
    		    }
    		});
    	    },
    	    error: function(xhr, status, error) {
    		enableButton(button);
    	    }
    	});
    },

    deleteTask: function(event) {
    	var _this = this;
    	if (event) { event.preventDefault(); }
    	var button = $(event.currentTarget);
    	if (buttonDisabled(button)) return false;
    	var rTaskId = $(event.currentTarget).attr("data-task-id");
    	var rTaskName = $(event.currentTarget).attr("data-task-name");
    	if(confirm("Delete Replication task:  " + rTaskName + ". Are you sure?")){
    	    $.ajax({
    		url: '/api/sm/replicas/' + rTaskId,
    		type: "DELETE",
    		dataType: "json",
    		success: function() {
    		    enableButton(button);
    		    _this.collection.fetch({
    			success: function() {
    			    _this.renderReplicas();
    			}
    		    });
    		},
    		error: function(xhr, status, error) {
    		    enableButton(button);
    		}
    	    });
    	}
    },

    startService: function(event){
    	var _this = this;
    	var serviceName = this.serviceName;
    	this.setStatusLoading(serviceName, true);
    	$.ajax({
    	    url: "/api/sm/services/replication/start",
    	    type: "POST",
    	    dataType: "json",
    	    success: function(data, status, xhr) {
    		_this.setStatusLoading(serviceName, false);
		_this.current_status = true;
    		//hide replication service warning
    		_this.$('#replication-warning').hide();
    	    },
    	    error: function(xhr, status, error) {
    		_this.setStatusError(serviceName, xhr);
    	    }
    	});
    },

    stopService: function(event) {
	var _this = this;
    	var serviceName = this.serviceName;
      	this.setStatusLoading(serviceName, true);
      	$.ajax({
      	    url: "/api/sm/services/replication/stop",
      	    type: "POST",
      	    dataType: "json",
      	    success: function(data, status, xhr) {
      		_this.setStatusLoading(serviceName, false);
		_this.current_status = false;
    		//display replication service warning
    		_this.$('#replication-warning').show();
      	    },
      	    error: function(xhr, status, error) {
      		_this.setStatusError(serviceName, xhr);
      	    }
      	});
    },

    setStatusLoading: function(serviceName, show) {
    	var statusEl = this.$('div.command-status[data-service-name="'+serviceName+'"]');
    	if (show) {
    	    statusEl.html('<img src="/static/storageadmin/img/ajax-loader.gif"></img>');
    	} else {
    	    statusEl.empty();
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
    }

});

// Add pagination
Cocktail.mixin(ReplicationView, PaginationMixin);
