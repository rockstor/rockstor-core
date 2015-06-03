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
	this.defTab = 0;
    },

    events: {
	'click #js-install-rockon': 'installRockon',
	'click #js-uninstall-rockon': 'uninstallRockon',
	'click #js-rockons-installed': 'installedRockons',
	'click .slider-stop': 'stopRockon',
	'click .slider-start': 'startRockon',
	'click #js-update-rockons': 'updateRockons',
	'click #js-rockon-settings': 'rockonSettings'
    },

    render: function() {
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
	this.$("ul.css-tabs").data("tabs").click(this.defTab);
    },

    installRockon: function(event) {
	var _this = this;
	event.preventDefault();
	var button = $(event.currentTarget);
	var rockon_id = button.attr('data-name');
	var rockon_o = _this.rockons.get(rockon_id);
	var wizardView = new RockonInstallWizardView({
	    model: new Backbone.Model({ rockon: rockon_o }),
	    title: 'Rock-on install wizard [' + rockon_o.get('name') + ']',
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

    updateRockons: function(event) {
	var _this = this;
	event.preventDefault();
	var button = $(event.currentTarget);
	if (buttonDisabled(button)) return false;
	disableButton(button);
	$.ajax({
	    url: '/api/rockons/update',
	    type: 'POST',
	    dataType: 'json',
	    success: function() {
		_this.defTab = 1;
		_this.render();
		enableButton(button);
	    },
	    error: function(xhr, status, error) {
		enableButton(button);
	    }
	});
    },

    rockonSettings: function(event) {
	var _this = this;
	event.preventDefault();
	var rockon_id = this.getRockonId(event);
	var rockon_o = _this.rockons.get(rockon_id);
	this.stopPolling();
	var wizardView = new RockonSettingsWizardView({
	    model: new Backbone.Model({ rockon: rockon_o}),
	    title: rockon_o.get('name') + ' Settings',
	    parent: this
	});
	$('.overlay-content', '#install-rockon-overlay').html(wizardView.render().el);
	$('#install-rockon-overlay').overlay().load();
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
	this.stopPolling();
	$.ajax({
	    url: '/api/rockons/' + rockon_id + '/start',
	    type: 'POST',
	    dataType: 'json',
	    success: function(data, status, xhr) {
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
	var share_map = {};
	var volumes = this.volumes.filter(function(volume) {
	    share_map[volume.get('dest_dir')] = this.$('#' + volume.id).val();
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

      // Add form validation
      this.portForm = this.$('#port-select-form');
      var rules = {};
      var messages = {};
      this.ports.each(function(port) {
	rules[port.id] = { required: true, number: true };
        messages[port.id] = "Please enter a valid port number";
      });
      this.validator = this.portForm.validate({
        rules: rules,
        messages: messages
      });
      return this;
    },

    save: function() {

	// Validate the form
	if (!this.portForm.valid()) {
            this.validator.showErrors();
            // return rejected promise so that the wizard doesn't proceed to the next page.
            return $.Deferred().reject();
	}

	var port_map = {};
	var cports = this.ports.filter(function(port) {
	    port_map[port.get('containerp')] = this.$('#' + port.id).val();
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
	this.cc_form = this.$('#custom-choice-form');
	var rules = {};
	var messages = {};
	this.custom_config.each(function(cc) {
	    rules[cc.id] = "required";
	    messages[cc.id] = "This is a required field.";
	});
	this.validator = this.cc_form.validate({
	    rules: rules,
	    messages: messages
	});
	return this;
    },

    save: function() {
	if (!this.cc_form.valid()) {
	    this.validator.showErrors();
	    return $.Deferred().reject();
	}
	var cc_map = {};
	var cconfigs = this.custom_config.filter(function(cc) {
	    cc_map[cc.get('key')] = this.$('#' + cc.id).val();
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
	this.rockon = this.model.get('rockon');
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.$('#ph-summary-table').html(this.table_template({
	    share_map: this.share_map,
	    port_map: this.port_map,
	    cc_map: this.cc_map}));
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

RockonInstallComplete = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_install_complete;
	this.port_map = this.model.get('port_map');
	this.share_map = this.model.get('share_map');
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
	$(this.el).html(this.template({
	    model: this.model,
	    port_map: this.port_map,
	    share_map: this.share_map
	}));
	return this;
    }

});

RockonSettingsWizardView = WizardView.extend({
    initialize: function() {
	WizardView.prototype.initialize.apply(this, arguments);
	this.pages = [];
	this.rockon = this.model.get('rockon');
	this.volumes = new RockOnVolumeCollection(null, {rid: this.rockon.id});
	this.ports = new RockOnPortCollection(null, {rid: this.rockon.id});
	this.custom_config = new RockOnCustomConfigCollection(null, {rid: this.rockon.id});
	this.shares = {};
	this.model.set('shares', this.shares);
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
	this.pages.push.apply(this.pages,
			      [RockonSettingsSummary, RockonAddShare,
			       RockonSettingsSummary, RockonSettingsComplete]);
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
	if (this.currentPageNum == 0) {
	    this.$('#prev-page').hide();
	    this.$('#next-page').html('Add a Share');
	    if (this.volumes.length == 0) {
		this.$('#next-page').hide();
	    }
	} else if (this.currentPageNum == (this.pages.length - 2)) {
	    this.$('#prev-page').html('Add a Share');
    	    this.$('#next-page').html('Next');
    	} else if (this.currentPageNum == (this.pages.length - 1)) {
    	    this.$('#prev-page').hide();
    	    this.$('#next-page').html('Submit');
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

RockonAddShare = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_add_shares;
	this.sub_template = window.JST.rockons_add_shares_form;
	this.shares = new ShareCollection();
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
	this.shares.on('reset', this.renderShares, this);
    },

    render: function() {
	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.shares.fetch();
	return this;
    },

    renderShares: function() {
	this.share_map = this.model.get('shares');
	this.volumes = this.model.get('volumes');
	this.used_shares = [];
	var _this = this;
	this.volumes.each(function(volume, index) {
	    _this.used_shares.push(volume.get('share_name'));
	});
	for (var s in this.share_map) {
	    this.used_shares.push(s);
	}
	this.filtered_shares = this.shares.filter(function(share) {
	    if (_this.used_shares.indexOf(share.get('name')) == -1) {
		return share;
	    }
	}, this);
	this.$('#ph-add-shares-form').html(this.sub_template({
	    shares: this.filtered_shares
	}));
	this.share_form = this.$('#vol-select-form');
	this.validator = this.share_form.validate({
	    rules: { "volume": "required" },
	    messages: { "volume": "Must be a valid unix path. Eg: /data/media" }
	});
	return this;
    },

    save: function() {
	if (!this.share_form.valid()) {
	    this.validator.showErrors();
	    return $.Deferred().reject();
	}
	this.share_map = this.model.get('shares');
	this.share_map[this.$('#volume').val()] = this.$('#share').val();
	this.model.set('shares', this.share_map);
	return $.Deferred().resolve();
    }


});

RockonSettingsSummary = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_settings_summary;
	this.sub_template = window.JST.rockons_settings_summary_table;
	this.rockon = this.model.get('rockon');
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.$('#ph-settings-summary-table').html(this.sub_template({
	    model: this.model,
	    volumes: this.model.get('volumes'),
	    new_volumes: this.model.get('shares'),
	    ports: this.model.get('ports'),
	    cc: this.model.get('custom_config'),
	    rockon: this.model.get('rockon')
	}));
	return this;
    }
});

RockonSettingsComplete = RockstorWizardPage.extend({
    initialize: function() {
	this.template = window.JST.rockons_update_complete;
	this.rockon = this.model.get('rockon');
	this.shares = this.model.get('shares');
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
	$(this.el).html(this.template({
	    model: this.model
	}));
	return this;
    },

    save: function() {
	var _this = this;
	return $.ajax({
	    url: '/api/rockons/' + this.rockon.id + '/update',
	    type: 'POST',
	    dataType: 'json',
	    contentType: 'application/json',
	    data: JSON.stringify({
		'shares': this.shares
	    }),
	    success: function() {}
	});
    }
});
