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

PaginationMixin = {
		events: {
	"click .go-to-page": "goToPage",
	"click .prev-page": "prevPage",
	"click .next-page": "nextPage",
},
goToPage: function(event) {
	if (event) event.preventDefault();
	this.collection.goToPage(parseInt($(event.currentTarget).attr("data-page")));
},
prevPage: function(event) {
	if (event) event.preventDefault();
	this.collection.prevPage();
},
nextPage: function(event) {
	if (event) event.preventDefault();
	this.collection.nextPage();
}
};

RockstorLayoutView = Backbone.View.extend({
	tagName: 'div',
	className: 'layout',

	initialize: function() {
	this.subviews = {};
	this.dependencies = [];
},

fetch: function(callback, context) {
	var allDependencies = [];
	_.each(this.dependencies, function(dep) {
		allDependencies.push(dep.fetch({silent: true}));
	});
	$.when.apply($, allDependencies).done(function () {
		if (callback) callback.apply(context);
	});
},

});


// RockstorModuleView

RockstorModuleView = Backbone.View.extend({

	tagName: 'div',
	className: 'module',
	requestCount: 0,

	initialize: function() {
	this.subviews = {};
	this.dependencies = [];
},

fetch: function(callback, context) {
	var allDependencies = [];
	_.each(this.dependencies, function(dep) {
		allDependencies.push(dep.fetch({silent: true}));
	});
	$.when.apply($, allDependencies).done(function () {
		if (callback) callback.apply(context);
	});
},

render: function() {
	$(this.el).html(this.template({
		module_name: this.module_name,
		model: this.model,
		collection: this.collection
	}));

	return this;
}
});

RockStorWidgetView = Backbone.View.extend({
	tagName: 'div',
	className: 'widget',

	events: {
	'click .configure-widget': 'configure',
	'click .resize-widget': 'resize',
	'click .close-widget': 'close',
	'click .download-widget': 'download',
},

initialize: function() {
	this.maximized = this.options.maximized;
	this.name = this.options.name;
	this.displayName = this.options.displayName;
	this.parentView = this.options.parentView;
	this.dependencies = [];
},

render: function() {
	$(this.el).attr('id', this.name + '_widget');
},

configure: function(event) {
	if (!_.isUndefined(event) && !_.isNull(event)) {
		event.preventDefault();
	}
},

resize: function(event) {
	if (!_.isUndefined(event) && !_.isNull(event)) {
		event.preventDefault();
	}
	var c = $(this.el).closest('div.widgets-container');
	var w = $(this.el).closest('div.widget-ph'); // current widget
	var widgetDef = RockStorWidgets.findByName(this.name);
	if (!this.maximized) {
		// Maximizing
		// Remember current position
		this.originalPosition = w.index();
		// remove list item from current position
		w.detach();
		// insert at first position in the list
		c.prepend(w);
		// resize to max
		w.attr('data-ss-colspan',widgetDef.maxCols);
		w.attr('data-ss-rowspan',widgetDef.maxRows);
		this.maximized = true;
	} else {
		// Restoring
		w.detach();
		w.attr('data-ss-colspan',widgetDef.cols);
		w.attr('data-ss-rowspan',widgetDef.rows);
		// find current list item at original index
		if (_.isNull(this.originalPosition) ||
				_.isUndefined(this.originalPosition)) {
			this.originalPosition = 0;
		}
		curr_w = c.find("div.widget-ph:eq("+this.originalPosition+")");
		// insert widget at original position
		if (curr_w.length > 0) {
			// if not last widget
			curr_w.before(w);
		} else {
			c.append(w);
		}
		this.maximized = false;
	}
	// trigger rearrange so shapeshift can do its job
	c.trigger('ss-rearrange');
	this.parentView.saveWidgetConfiguration();
},

close: function(event) {
	if (!_.isUndefined(event) && !_.isNull(event)) {
		event.preventDefault();
	}
	this.parentView.removeWidget(this.name, this);
},

download: function(event) {
	if (!_.isUndefined(event) && !_.isNull(event)) {
		event.preventDefault();
	}
},

cleanup: function() {
	logger.debug("In RockStorWidgetView close");
},

fetch: function(callback, context) {
	var allDependencies = [];
	_.each(this.dependencies, function(dep) {
		allDependencies.push(dep.fetch({silent: true}));
	});
	$.when.apply($, allDependencies).done(function () {
		if (callback) callback.apply(context);
	});
},

});

RockstorButtonView = Backbone.View.extend({
	tagName: 'div',
	className: 'button-bar',

	initialize: function() {
	this.actions = this.options.actions;
	this.layout = this.options.layout;
	this.template = window.JST.common_button_bar;

},

render: function() {
	$(this.el).append(this.template({actions: this.actions}));
	this.attachActions();
	return this;
},

attachActions: function() {

}

});

function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) == (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

function csrfSafeMethod(method) {
	// these HTTP methods do not require CSRF protection
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
	crossDomain: false, // obviates need for sameOrigin test
	beforeSend: function(xhr, settings) {
	if (!csrfSafeMethod(settings.type)) {
		var csrftoken = getCookie('csrftoken');
		xhr.setRequestHeader("X-CSRFToken", csrftoken);
	}
}
});

function showError(errorMsg) {
	if (_.isUndefined(errorPopup)) {
		errorPopup = $('#errorPopup').modal({
			show: false
		});
	}
	// $('#errorContent').html("<h3>Error!</h3>");
	var msg = errorMsg;
	try {
		msg = JSON.parse(errorMsg).detail;
	} catch(err) {
	}
	$('#errorContent').html(msg);
	$('#errorPopup').modal('show');
}

errorPopup = undefined;

function showApplianceList() {
	var applianceSelectPopup = $('#appliance-select-popup').modal({
		show: false
	});
	$('#appliance-select-content').html((new AppliancesView()).render().el);
	$('#appliance-select-popup').modal('show');

}


function showSuccessMessage(msg) {
	$('#messages').html(msg);
	$('#messages').css('visibility', 'visible');

}

function hideMessage() {
	$('#messages').html('&nbsp;');
	$('#messages').css('visibility', 'hidden');

}

/* Loading indicator */

$(document).ajaxStart(function() {
	$('#loading-indicator').css('visibility', 'visible');
});

$(document).ajaxStop(function() {
	$('#loading-indicator').css('visibility', 'hidden');
});


function showLoadingIndicator(elementName, context) {
	var _this = context;
	_this.$('#'+elementName).css('visibility', 'visible');
}

function hideLoadingIndicator(elementName, context) {
	var _this = context;
	_this.$('#'+elementName).css('visibility', 'hidden');
}

function disableButton(button) {
	button.data("executing", true);
	button.attr("disabled", true);
}

function enableButton(button) {
	button.data("executing", false);
	button.attr("disabled", false);
}

function buttonDisabled(button) {
	if (button.data("executing")) {
		return true;
	} else {
		return false;
	}
}


function refreshNavbar() {
	$.ajax({
		url: "api/commands/current-user",
		type: "POST",
		dataType: "json",
		global: false, // dont show global loading indicator
		success: function(data, status, xhr) {
		var currentUser= data;
		$('#user-name').css({textTransform: 'none'});
		$('#user-name').html(currentUser+' ');
	},
	error: function(xhr, status, error) {
	//	$('#user-name').html("Hello, <b> Admin! </b>");   
	}
	});

	var navbarTemplate = window.JST.common_navbar;
	$("#navbar-links").html(navbarTemplate({
		logged_in: logged_in, 
		
	}));

	$('.dropdown-toggle').dropdown();

}

// Parses error message from ajax request
// Returns the value of the detail attribute as json
// or a string if it cannot be parsed as json
function parseXhrError(xhr) {
	var msg = xhr.responseText;
	try {
		msg = JSON.parse(msg).detail;
	} catch(err) {
	}
	if (typeof(msg)=="string") {
		try {
			msg = JSON.parse(msg);
		} catch(err) {
		}
	}
	return msg;
}

function getXhrErrorJson(xhr) {
	var json = {};
	try { json = JSON.parse(xhr.responseText); } catch(err) { }
	return json;
}

function setApplianceName() {
	var appliances = new ApplianceCollection();
	appliances.fetch({
		success: function(request) {
		if (appliances.length > 0) {
			RockStorGlobals.currentAppliance =
					appliances.find(function(appliance) {
						return appliance.get('current_appliance') == true;
					});
			$('#appliance-name').html('<i class="fa fa-desktop"></i>&nbsp;Hostname: ' + RockStorGlobals.currentAppliance.get('hostname') + '&nbsp;&nbsp;&nbsp;&nbsp;Mgmt IP: ' + RockStorGlobals.currentAppliance.get('ip'));
		}
	},
	error: function(request, response) {
	}

	});
}

function updateLoadAvg() {
	RockStorGlobals.loadAvgTimer = window.setInterval(function() {
		fetchLoadAvg();
	}, 60000);
	fetchLoadAvg();
	RockStorGlobals.loadAvgDisplayed = true;
}


function fetchLoadAvg() {
	$.ajax({
		url: "/api/sm/sprobes/loadavg?limit=1&format=json",
		type: "GET",
		dataType: "json",
		global: false, // dont show global loading indicator
		success: function(data, status, xhr) {
		displayLoadAvg(data);
	},
	error: function(xhr, status, error) {
	}
	});
}

function fetchKernelInfo() {
	$.ajax({
		url: '/api/commands/kernel',
		type: 'POST',
		dataType: 'json',
		global: false,
		success: function(data, status, xhr) {
		RockStorGlobals.kernel = data;
	},
	error: function(xhr, status, error) {
		msg = JSON.parse(xhr.responseText).detail;
		$('#browsermsg').html('<div class="alert alert-error"><button type="button" class="close" data-dismiss="alert">&times;</button>' + msg + '</div>');
	}
	});
}

function displayLoadAvg(data) {
	var n = parseInt(data.results[0]['uptime']);
	var load_1 = parseFloat(data.results[0]['load_1']);
	var load_5 = parseFloat(data.results[0]['load_5']);
	var load_15 = parseFloat(data.results[0]['load_15']);
	var secs = n % 60;
	var mins = Math.round(n/60) % 60;
	var hrs = Math.round(n / (60*60)) % 24;
	var days = Math.round(n / (60*60*24)) % 365;
	var yrs = Math.round(n / (60*60*24*365));
	var str = 'Uptime: ';
	if (RockStorGlobals.kernel) {
		str = 'Linux: ' + RockStorGlobals.kernel + ' &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + str;
	}
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
	str += ' &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Load: ' + load_1 + ', ' + load_5 + ', ' + load_15;
	$('#appliance-loadavg').html(str);
}

function fetchServerTime() {
	RockStorGlobals.serverTimeTimer = window.setInterval(function() {
		getCurrentTimeOnServer();
	}, 10000);
	getCurrentTimeOnServer();
	RockStorGlobals.serverTimeFetched = true;
}

function getCurrentTimeOnServer() {
	$.ajax({
		url: "/api/commands/utcnow",
		type: "POST",
		dataType: "json",
		global: false, // dont show global loading indicator
		success: function(data, status, xhr) {
		RockStorGlobals.currentTimeOnServer = new Date(data);
	},
	error: function(xhr, status, error) {
	}
	});
}

function setVersionCheckTimer() {
	RockStorGlobals.versionCheckTimer = window.setInterval(function() {
		checkVersion();
	}, 300000);
	getCurrentVersion();
	RockStorGlobals.versionCheckTimerStarted = true;
}

function getCurrentVersion() {
	$.ajax({
		url: "/api/commands/current-version",
		type: "POST",
		dataType: "json",
		global: false, // dont show global loading indicator
		success: function(data, status, xhr) {
		$('#version-msg').html('RockStor ' + data);
	},
	error: function(xhr, status, error) {
	}
	});
}

function checkVersion() {
	$.ajax({
		url: "/api/commands/update-check",
		type: "POST",
		dataType: "json",
		global: false, // dont show global loading indicator
		success: function(data, status, xhr) {

		var currentVersion = data[0];
		var mostRecentVersion = data[1];
		var changeList = data[2];
		if (currentVersion != mostRecentVersion) {
			$('#version-msg').html('RockStor ' + currentVersion + ' <i class="icon-arrow-up"></i>');
		} else {
			$('#version-msg').html('RockStor ' + currentVersion);
		}
	},
	error: function(xhr, status, error) {
	}
	});

}

function fetchDependencies(dependencies, callback, context) {
	if (dependencies.length == 0) {
		if (callback) callback.apply(context);
	}
	var requestCount = dependencies.length;
	_.each(dependencies, function(dependency) {
		dependency.fetch({
			success: function(request){
			requestCount -= 1;
			if (requestCount == 0) {
				if (callback) callback.apply(context);
			}
		},
		error: function(request, response) {
			requestCount -= 1;
			if (requestCount == 0) {
				if (callback) callback.apply(context);
			}
		}
		});
	});
}

function checkBrowser() {
	var userAgent = navigator.userAgent
			if (!/firefox/i.test(userAgent) && !/chrome/i.test(userAgent)) {
				$('#browsermsg').html('<div class="alert alert-error"><button type="button" class="close" data-dismiss="alert">&times;</button>The RockStor WebUI is supported only on Firefox or Chrome. Some features may not work correctly.</div>');
			}
	RockStorGlobals.browserChecked = true;
}

RockStorProbeMap = [];
RockStorGlobals = {
		navbarLoaded: false,
		applianceNameSet: false,
		currentAppliance: null,
		maxPageSize: 5000,
		browserChecked: false,
		versionCheckTimerStarted: false,
		kernel: null,
}

var RS_DATE_FORMAT = 'MMMM Do YYYY, h:mm:ss a';

// Constants
probeStates = {
		STOPPED: 'stopped',
		CREATED: 'created',
		RUNNING: 'running',
		ERROR: 'error',
};

var RockstorUtil = function() {
	var util = {
			// maintain selected object list
			// list is an array of contains models

			// does the list contain a model with attr 'name' with value 'value'
			listContains: function(list, name, value) {
		return _.find(list, function(obj) {
			return obj.get(name) == value;
		});
	},

	// add obj from collection with attr 'name' and value 'value' to list
	addToList: function(list, collection, name, value) {
		list.push(collection.find(function(obj) {
			return obj.get(name) == value;
		}));
	},

	// remove obj with attr 'name' and value 'value'
	removeFromList: function(list, name, value) {
		var i = _.indexOf(_.map(list, function(obj) {
			return obj.get(name);
		}), value);
		list.splice(i,1);
	}
	}
	return util;
}();
