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
    }

});


RockonInstallWizardView = WizardView.extend({
    initialize: function() {
	WizardView.prototype.initialize.apply(this, arguments);
	this.pages = [];
	this.rockon = this.model.get('rockon');
    },

    setCurrentPage: function() {
	this.pages[0] = RockonShareChoice;
	this.pages[1] = RockonPortChoice;
	this.pages[2] = RockonCustomChoice;
	this.pages[3] = RockonInstallSummary;
	this.pages[4] = RockonInstallComplete;

	this.currentPage = new this.pages[this.currentPageNum]({
	    model: this.model,
	    parent: this,
	    evAgg: this.evAgg
	});
    },

    lastPage: function() {
	return ((this.pages.length > 1)
		&& ((this.pages.length-1) == this.currentPageNum));
    },

    modifyButtonText: function() {
    	switch(this.currentPageNum) {
    	case 0:
	    this.$('#prev-page').hide();
    	    break;
	case 3:
	    this.$('#next-page').html('Submit');
	    break;
    	default:
	    this.$('#prev-page').show();
    	    this.$('#ph-wizard-buttons').show();
    	    break;
    	}
    	if (this.lastPage()) {
	    this.$('#prev-page').hide();
	    this.$('#next-page').html('Close');
	}
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
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    }
});
