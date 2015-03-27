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

RockonsView = RockstorLayoutView.extend({


    initialize: function() {
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.rockons_rockons;
	this.rockons = new RockOnCollection({});
	this.dependencies.push(this.rockons);
	this.updateFreq = 15000;
    },

    events: {
	'click #js-install-rockon': 'installRockon',
	'click #js-uninstall-rockon': 'uninstallRockon',
	'click #js-rockons-installed': 'installedRockons',
	'click .slider-stop': 'stopRockon',
	'click .slider-start': 'startRockon'
    },

    render: function() {
	//this.fetch(this.renderRockons, this);
	this.rockons.fetch();
	this.updateStatus();
	return this;
    },

    renderRockons: function() {
	var _this = this;
	$(this.el).html(this.template({rockons: this.rockons}));
	if (!this.dockerServiceView) {
	    this.dockerServiceView = new DockerServiceView({
		parentView: this,
		dockerService: this.dockerService
	    });
	}

	this.$('input.service-status').simpleSlider({
	    "theme": "volume",
	    allowedValues: [0,1],
	    snap: true
	});

	this.$('input.service-status').each(function(i, el) {
	    var slider = $(el).data('slider-object');
	    slider.trackEvent = function(e) {};
	    slider.dragger.unbind('mousedown');
	});

	$('#docker-service-ph').append(this.dockerServiceView.render().el);
	$('#install-rockon-overlay').overlay({load: false});
	this.$("ul.css-tabs").tabs("div.css-panes > div");
	// var active = this.$("ul.css-tabs").tabs("option", "active");
	// console.log('active', active);
    },

    installRockon: function(event) {
	var _this = this;
	event.preventDefault();
	var button = $(event.currentTarget);
	var rockon_id = button.attr('data-name');
	var rockon_o = _this.rockons.get(rockon_id);
	var wizardView = new RockonInstallWizardView({
	    model: new Backbone.Model({ rockon: rockon_o }),
	    title: 'Install this awesome Rockon',
	    parent: this
	});
	$('.overlay-content', '#install-rockon-overlay').html(wizardView.render().el);
	$('#install-rockon-overlay').overlay().load();
    },

    uninstallRockon: function(event) {
	var _this = this;
	event.preventDefault();
	var button = $(event.currentTarget);
	if (buttonDisabled(button)) return false;
	var rockon_id = button.attr('data-name');
	var rockon_o = _this.rockons.get(rockon_id);
	if (confirm("Are you sure you want to uninstall this Rockon(" + rockon_o.get('name') + ")?")) {
	    disableButton(button);
	    $.ajax({
		url: '/api/rockons/' + rockon_id + '/uninstall',
		type: 'POST',
		dataType: 'json',
		success: function() {
		    _this.render();
		    enableButton(button);
		},
		error: function(xhr, status, error) {
		    enableButton(button);
		}
	    });
	}
    },

    getRockonId: function(event) {
	var slider = $(event.currentTarget);
	return slider.attr('data-rockon-id');
    },

    getSliderVal: function(id) {
	return this.$('input[data-rockon-id='+id+']').data('slider-object').value;
    },

    setSliderVal: function(id, val) {
	this.$('input[data-rockon-id='+id+']').simpleSlider('setValue', val);
    },

    startRockon: function(event) {
	var _this = this;
	var rockon_id = this.getRockonId(event);
	if (this.getSliderVal(rockon_id).toString() == "1") { return; }
	console.log('before call', this.rockon);
	this.stopPolling();
	$.ajax({
	    url: '/api/rockons/' + rockon_id + '/start',
	    type: 'POST',
	    dataType: 'json',
	    success: function(data, status, xhr) {
		console.log('after call', this.rockon);
		_this.setSliderVal(rockon_id, 1);
		_this.updateStatus();
	    },
	    error: function(data, status, xhr) {
		console.log('error while starting rockon');
	    }
	});
    },

    stopRockon: function(event) {
	var _this = this;
	var rockon_id = this.getRockonId(event);
	if (this.getSliderVal(rockon_id).toString() == "0") { return; }
	this.stopPolling();
	$.ajax({
	    url: '/api/rockons/' + rockon_id + '/stop',
	    type: 'POST',
	    dataType: 'json',
	    success: function(data, status, xhr) {
		_this.setSliderVal(rockon_id, 0);
		_this.updateStatus();
	    },
	    error: function(data, status, xhr) {
		console.log('error while stopping rockon');
	    }
	});
    },

    pendingOps: function() {
	var pending = this.rockons.find(function(rockon) {
	    if ((rockon.get('status').search('pending') != -1) || (rockon.get('state').search('pending') != -1)) {
		return true;
	    }
	});
	if (pending) { return true; }
	return false;
    },

    updateStatus: function() {
	console.log('in update status');
	var _this = this;
	_this.startTime = new Date().getTime();
	_this.rockons.fetch({
	    silent: true,
	    success: function(data, response, options) {
		_this.renderRockons();
		if (_this.pendingOps()) {
		    var ct = new Date().getTime();
		    var diff = ct - _this.startTime;
		    if (diff > _this.updateFreq) {
			_this.updateStatus();
		    } else {
			_this.timeoutId = window.setTimeout( function() {
			    _this.updateStatus();
			}, _this.updateFreq - diff);
		    }
		} else {
		    _this.stopPolling();
		}
	    }
	});
    },

    stopPolling: function() {
	if (!_.isUndefined(this.timeoutId)) {
	    window.clearInterval(this.timeoutId);
	}
    },

    installedRockons: function(event) {
	if (this.pendingOps()) {
	    this.updateStatus();
	}
    }

});


RockonInstallWizardView = WizardView.extend({
    initialize: function() {
	WizardView.prototype.initialize.apply(this, arguments);
	this.pages = [];
	this.rockon = this.model.get('rockon');
	this.volumes = new RockOnVolumeCollection(null, {rid: this.rockon.id});
	this.ports = new RockOnPortCollection(null, {rid: this.rockon.id});
	this.custom_config = new RockOnCustomConfigCollection(null, {rid: this.rockon.id});
    },

    fetchVolumes: function() {
	var _this = this;
	this.volumes.fetch({
	    success: function () {
		_this.model.set('volumes', _this.volumes);
		_this.fetchPorts();
	    }
	});
    },

    fetchPorts: function() {
	var _this = this;
	this.ports.fetch({
	    success: function() {
		_this.model.set('ports', _this.ports);
		_this.fetchCustomConfig();
	    }
	});
    },

    fetchCustomConfig: function() {
	var _this = this;
	this.custom_config.fetch({
	    success: function() {
		_this.model.set('custom_config', _this.custom_config);
		_this.addPages();
	    }
	});
    },

    render: function() {
	this.fetchVolumes();
	return this;
    },

    addPages: function() {
	if (this.volumes.length > 0) {
	    this.pages.push(RockonShareChoice);
	}
	if (this.ports.length > 0) {
	    this.pages.push(RockonPortChoice);
	}
	if (this.custom_config.length > 0) {
	    this.pages.push(RockonCustomChoice);
	}
	this.pages.push.apply(this.pages, [RockonInstallSummary, RockonInstallComplete]);
	WizardView.prototype.render.apply(this, arguments);
    	return this;
    },

    setCurrentPage: function() {
	this.currentPage = new this.pages[this.currentPageNum]({
	    model: this.model,
	    parent: this,
	    evAgg: this.evAgg
	});
    },

    modifyButtonText: function() {
    	if (this.currentPageNum == (this.pages.length - 2)) {
    	    this.$('#next-page').html('Submit');
    	} else if (this.currentPageNum == (this.pages.length - 1)) {
    	    this.$('#prev-page').hide();
    	    this.$('#next-page').html('Close');
    	} else if (this.currentPageNum == 0) {
	    this.$('#prev-page').hide();
	} else {
    	    this.$('#prev-page').show();
	    this.$('#next-page').html('Next');
    	    this.$('#ph-wizard-buttons').show();
    	}
    },

    lastPage: function() {
	return ((this.pages.length > 1)
		&& ((this.pages.length-1) == this.currentPageNum));
    },

    finish: function() {
	this.parent.$('#install-rockon-overlay').overlay().close();
	this.parent.render();
    }

});

RockonShareChoice = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_install_choice;
	this.vol_template = window.JST.rockons_vol_table;
	this.rockon = this.model.get('rockon');
	this.volumes = this.model.get('volumes');
	this.shares = new ShareCollection();
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
	this.shares.on('reset', this.renderVolumes, this);
    },

    render: function() {
	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.shares.fetch();
	return this;
    },

    renderVolumes: function() {
	this.$('#ph-vols-table').html(this.vol_template({volumes: this.volumes, shares: this.shares}));
    },

    save: function() {
	var share_map = new Map();
	var volumes = this.volumes.filter(function(volume) {
	    share_map.set(this.$('#' + volume.id).val(), volume);
	    return volume;
	}, this);
	this.model.set('share_map', share_map);
	return $.Deferred().resolve();
    }
});

RockonPortChoice = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_port_choice;
	this.port_template = window.JST.rockons_ports_form;
	this.ports = this.model.get('ports');
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
    	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.$('#ph-ports-form').html(this.port_template({ports: this.ports}));
    	return this;
    },

    save: function() {
	var port_map = {};
	var cports = this.ports.filter(function(port) {
	    port_map[this.$('#' + port.id).val()] = port.get('containerp');
	    return port;
	}, this);
	this.model.set('port_map', port_map);
	return $.Deferred().resolve();
    }
});

RockonCustomChoice = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_custom_choice;
	this.cc_template = window.JST.rockons_cc_form;
	this.custom_config = this.model.get('custom_config');
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.$('#ph-cc-form').html(this.cc_template({cc: this.custom_config}));
	return this;
    },

    save: function() {
	var cc_map = {};
	var cconfigs = this.custom_config.filter(function(cc) {
	    cc_map[this.$('#' + cc.id).val()] = cc.get('val');
	    return cc;
	}, this);
	this.model.set('cc_map', cc_map);
	return $.Deferred().resolve();
    }
});

RockonInstallSummary = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_install_summary;
	this.table_template = window.JST.rockons_summary_table;
	this.share_map = this.model.get('share_map');
	this.port_map = this.model.get('port_map');
	this.cc_map = this.model.get('cc_map');
	this.ports = this.model.get('ports');
	this.cc = this.model.get('custom_config');
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.test_map = new Map();
	for (var i = 0; i < 25; i++) {
	    this.test_map.set(i, i);
	}
	console.log('test_map', this.test_map);
	this.$('#ph-summary-table').html(this.table_template({share_map: this.share_map, port_map: this.port_map, cc_map: this.cc_map, ports: this.ports, cc: this.cc, test_map: this.test_map}));
	return this;
    }
});

RockonInstallComplete = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_install_complete;
	this.rockon = this.model.get('rockon');
	this.port_map = this.model.get('port_map');
	this.share_map = this.model.get('share_map');
	this.cc_map = this.model.get('cc_map');
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
	$(this.el).html(this.template({
	    model: this.model,
	    port_map: this.port_map,
	    share_map: this.share_map
	}));
	return this;
    },

    save: function() {
	var _this = this;
	return $.ajax({
	    url: '/api/rockons/' + this.rockon.id + '/install',
	    type: 'POST',
	    dataType: 'json',
	    contentType: 'application/json',
	    data: JSON.stringify({
		'ports': this.port_map,
		'shares': this.share_map,
		'cc': this.cc_map
	    }),
	    success: function() {
		console.log('rockon install success');
	    },
	    error: function(request, status, error) { }
	});
    }
});
