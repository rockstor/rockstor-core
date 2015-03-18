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

    },

    events: {
	'click #js-install-rockon': 'installRockon',
	'click #js-uninstall-rockon': 'uninstallRockon',
	'click #js-rockons-installed': 'installedRockons'
    },

    render: function() {
	this.fetch(this.renderRockons, this);
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

    installedRockons: function(event) {
	console.log('installed rockons fetched');
	//this.rockons.fetch();
    }

});


RockonInstallWizardView = WizardView.extend({
    initialize: function() {
	WizardView.prototype.initialize.apply(this, arguments);
	this.pages = [];
	this.rockon = this.model.get('rockon');
	this.volumes = new RockOnVolumeCollection(null, {rid: this.rockon.id});
	this.ports = new RockOnVolumeCollection(null, {rid: this.rockon.id});
	this.custom_config = new RockOnCustomConfigCollection(null, {rid: this.rockon.id});
	this.volumes.fetch();
	console.log('volumes', this.volumes);
	this.ports.fetch();
	console.log('ports', this.ports);
	this.custom_config.fetch();
	console.log('custom config', this.custom_config);
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
	this.volumes = new RockOnVolumeCollection(null, {rid: this.rockon.id});
	this.shares = new ShareCollection();
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
	this.volumes.on('reset', this.renderVolumes, this);
	this.shares.on('reset', this.renderVolumes, this);
    },

    render: function() {
	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.volumes.fetch();
	this.shares.fetch();
	return this;
    },

    renderVolumes: function() {
	var volumes = this.volumes.filter(function(volume) {
	    return volume;
	}, this);
	var shares = this.shares.filter(function(share) {
	    return share;
	}, this);
	this.$('#ph-vols-table').html(this.vol_template({volumes: volumes, shares: shares}));
    },

    save: function() {
	var share_map = {};
	var volumes = this.volumes.filter(function(volume) {
	    share_map[this.$('#' + volume.id).val()] = volume.get('dest_dir');
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
	this.rockon = this.model.get('rockon');
	this.ports = new RockOnPortCollection(null, {rid: this.rockon.id});
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
	this.ports.on('reset', this.renderPorts, this);
    },

    render: function() {
    	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.ports.fetch();
    	return this;
    },

    renderPorts: function() {
	var ports = this.ports.filter(function(port) {
	    return port;
	}, this);
    	this.$('#ph-ports-form').html(this.port_template({ports: ports}));
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
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    }
});

RockonInstallSummary = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_install_summary;
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    }
});

RockonInstallComplete = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_install_complete;
	this.rockon = this.model.get('rockon');
	this.port_map = this.model.get('port_map');
	this.volume_map = this.model.get('volume_map');
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
	$(this.el).html(this.template({
	    model: this.model,
	    port_map: this.port_map,
	    volume_map: this.volume_map
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
		'ports': this.model.get('port_map'),
		'shares': this.model.get('share_map')
	    }),
	    success: function() {
		console.log('rockon install success');
	    },
	    error: function(request, status, error) { }
	});
    }
});
