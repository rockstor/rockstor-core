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
        this.rockons.pageSize = RockStorGlobals.maxPageSize;
        this.service = new Service({
            name: 'docker'
        });
        this.dependencies.push(this.rockons, this.service);
        this.updateFreq = 15000;
        this.defTab = 0;
        this.initHandlebarHelpers();
    },

    events: {
        'switchChange.bootstrapSwitch': 'rockonToggle',
        'click #js-install-rockon': 'installRockon',
        'click #js-uninstall-rockon': 'uninstallRockon',
        'click #js-rockons-installed': 'installedRockons',
        'click #js-update-rockons': 'updateRockons',
        'click #js-rockon-settings': 'rockonSettings',
        'click #js-rockon-info': 'rockonInfo'
    },

    render: function() {
        this.service.fetch();
        this.rockons.fetch();
        this.updateStatus();

        return this;
    },

    renderRockons: function() {
        var _this = this;

        var ui_map = {};
        var uis = this.rockons.filter(function(rockon) {
            ui_map[rockon.get('id')] = null;
            if (rockon.get('ui')) {
                var protocol = 'http://';
                if (rockon.get('https')) {
                    protocol = 'https://';
                }
                var ui_link = protocol + window.location.hostname;
                if (rockon.get('ui_port')) {
                    ui_link += ':' + rockon.get('ui_port');
                }
                if (rockon.get('link')) {
                    ui_link += '/' + rockon.get('link');
                }
                ui_map[rockon.get('id')] = ui_link;
            }
            return false;
        });
        $(this.el).html(this.template({
            rockons: _this.rockons,
            rockonJson: _this.rockons.toJSON(),
            status: _this.service.get('status'),
            ui_map: ui_map
        }));

        if (!this.dockerServiceView) {
            this.dockerServiceView = new DockerServiceView({
                parentView: _this
            });
        }
        // Render the Rockons template with a status describing whether
        // the Rockons service has been enabled

        $('#docker-service-ph').append(this.dockerServiceView.render().el);

        $('#install-rockon-overlay').overlay({
            load: false
        });
        this.$('ul.nav.nav-tabs').tabs('div.css-panes > div');
        this.$('.nav-tabs li:eq(' + this.defTab + ') a').click();

        //initalize bootstrap switch
        this.$('[type=\'checkbox\']').bootstrapSwitch();
        this.$('[type=\'checkbox\']').bootstrapSwitch('onColor', 'success'); //left side text color
        this.$('[type=\'checkbox\']').bootstrapSwitch('offColor', 'danger'); //right side text color
    },

    installRockon: function(event) {
        var _this = this;
        this.defTab = 0;
        event.preventDefault();
        var button = $(event.currentTarget);
        var rockon_id = button.attr('data-name');
        var rockon_o = _this.rockons.get(rockon_id);
        var wizardView = new RockonInstallWizardView({
            model: new Backbone.Model({
                rockon: rockon_o
            }),
            title: rockon_o.get('name') + ' install wizard',
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
        if (confirm('Are you sure you want to uninstall this Rock-on (' + rockon_o.get('name') + ')?')) {
            disableButton(button);
            $.ajax({
                url: '/api/rockons/' + rockon_id + '/uninstall',
                type: 'POST',
                dataType: 'json',
                success: function() {
                    _this.defTab = 0;
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
        var rockon_id = _this.getRockonId(event);
        var rockon_o = _this.rockons.get(rockon_id);
        _this.stopPolling();
        var wizardView = new RockonSettingsWizardView({
            model: new Backbone.Model({
                rockon: rockon_o
            }),
            title: rockon_o.get('name') + ' Settings',
            parent: this
        });
        $('.overlay-content', '#install-rockon-overlay').html(wizardView.render().el);
        $('#install-rockon-overlay').overlay().load();
    },

    rockonInfo: function(event) {
        var _this = this;
        event.preventDefault();
        var rockon_id = _this.getRockonId(event);
        var rockon_o = _this.rockons.get(rockon_id);
        _this.stopPolling();
        var infoView = new RockonInfoView({
            model: new Backbone.Model({
                rockon: rockon_o
            }),
            title: 'Additional information about ' + rockon_o.get('name') + ' Rock-on',
            parent: this
        });
        $('.overlay-content', '#install-rockon-overlay').html(infoView.render().el);
        $('#install-rockon-overlay').overlay().load();
    },

    getRockonId: function(event) {
        var slider = $(event.currentTarget);
        return slider.attr('data-rockon-id');
    },

    rockonToggle: function(event, state) {
        var rockonId = $(event.target).attr('data-rockon-id');
        if (state) {
            this.startRockon(rockonId);
        } else {
            this.stopRockon(rockonId);
        }
    },

    startRockon: function(rockonId) {
        var _this = this;
        this.stopPolling();
        $.ajax({
            url: '/api/rockons/' + rockonId + '/start',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.defTab = 0;
                _this.updateStatus();
            },
            error: function(data, status, xhr) {
                console.log('error while starting rockon');
            }
        });
    },

    stopRockon: function(rockonId) {
        var _this = this;
        this.stopPolling();
        $.ajax({
            url: '/api/rockons/' + rockonId + '/stop',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.defTab = 0;
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
        if (pending) {
            return true;
        }
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
                        _this.timeoutId = window.setTimeout(function() {
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
    },

    //@todo: cleanup after figuring out how to track the installed variable.
    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_installedRockons', function() {
            var html = '';
            _this = this;
            var installed = 0;
            this.rockons.each(function(rockon, index) {
                if (rockon.get('state') == 'installed' || rockon.get('state').match('pending')) {
                    installed += 1;
                    html += '<div id="js-rockons-installed" class="tab-section" style="position: relative">';
                    if (rockon.get('state').search('pending') > -1 || rockon.get('status').search('pending') > -1) {
                        var text = 'Installing ...';
                        if (rockon.get('state') == 'pending_uninstall') {
                            text = 'Uninstalling ...';
                        } else if (rockon.get('status') == 'pending_start') {
                            text = 'Starting ...';
                        } else if (rockon.get('status') == 'pending_stop') {
                            text = 'Stopping ...';
                        }
                        html += '<div class="overlay">';
                        html += '<div class="text-center">';
                        html += '<i class="fa fa-3x fa-cog fa-spin"></i>';
                        html += '<div>';
                        html += '<p class="lead">' + text + '</p>';
                        html += '</div>';
                        html += '</div>';
                        html += '</div>';
                    }
                    html += '<div class="row">';
                    html += '<div class="col-md-6">';
                    html += '<a href="' + rockon.get('website') + '" target="_blank"><h3><u>' + rockon.get('name') + '</u></h3></a>';
                    html += '<p>' + rockon.get('description') + '</p>';
                    html += '<h4>Current status: ' + rockon.get('status') + '</h4>';
                    html += '</div>';
                    html += '<div class="col-md-3"></div>';
                    html += '<div class="col-md-3">';
                    if (rockon.get('state') == 'installed' && !rockon.get('status').match('pending')) {
                        if (rockon.get('status') == 'started') {
                            html += '<input type="checkbox" name="rockon-status-checkbox" data-rockon-id="' + rockon.get('id') + '" data-size="mini" checked />';
                        } else {
                            html += '<input type="checkbox" name="rockon-status-checkbox" data-rockon-id="' + rockon.get('id') + '" data-size="mini" />';
                        }
                        html += ' <a id="js-rockon-settings" href="#" class="settings" data-rockon-id="' + rockon.get('id') + '"><i class="glyphicon glyphicon-wrench"></i></a>&nbsp;&nbsp';
                        if (rockon.get('more_info')) {
                            html += '<a id="js-rockon-info" href="#" class="moreinfo" data-rockon-id="' + rockon.get('id') + '"><i class="fa fa-info-circle"></i></a>';
                        }
                        html += '<br><br>';
                        if (_this.ui_map[rockon.get('id')]) {
                            if (rockon.get('status') == 'started') {
                                html += '<a href="' + _this.ui_map[rockon.get('id')] + '" target="_blank" class="btn btn-primary">' + rockon.get('name') + ' UI</a> ';
                            } else {
                                html += '<a href="#" class="btn btn-primary disabled" title="Switch on to access the UI">' + rockon.get('name') + ' UI</a> ';
                            }
                        }
                        if (rockon.get('status') != 'started') {
                            html += '<a id="js-uninstall-rockon" class="btn btn-danger" data-name="' + rockon.get('id') + '">Uninstall</a>';
                        }

                    }
                    html += '</div>';
                    html += '</div>';
                    html += '</div>';
                }
            });
            if (installed == 0) {
                html += '<div class="tab-section">';
                html += '<div class="row">';
                html += '<div class="col-md-12">';
                html += '<h3>There are no Rock-ons installed currently.</h3>';
                html += '</div>';
                html += '</div>';
                html += '</div>';
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('display_allRockons', function() {
            var html = '';
            var all = 0;
            this.rockons.each(function(rockon, index) {
                if (rockon.get('state') == 'available' || rockon.get('state') == 'install_failed') {
                    all += 1;
                    html += '<div class="tab-section">';
                    html += '<div class="row">';
                    html += '<div class="col-md-12">';
                    html += '<a href="' + rockon.get('website') + '" target="_blank"><h3>' + rockon.get('name') + '</h3></a>';
                    html += '<p>' + rockon.get('description') + '</p>';
                    if (rockon.get('state') == 'install_failed') {
                        html += '<strong>Failed to install in the previous attempt.</strong> Here\'s how you can proceed.';
                        html += '<ul>';
                        html += '<li>Check logs in /opt/rockstor/var/log for clues.</li>';
                        html += '<li>Install again.</li>';
                        html += '<li>If the problem persists, post on the <a href="http://forum.rockstor.com" target="_blank">Forum</a> or email support@rockstor.com</li>';
                        html += '</ul>';
                    }
                    html += '<a id="js-install-rockon" class="btn btn-primary pull-right" href="#" data-name="' + rockon.get('id') + '">Install</a>';
                    html += '</div>';
                    html += '</div>';
                    html += '</div>';
                }
            });
            if (all == 0) {
                html += '<div class="tab-section">';
                html += '<div class="row">';
                html += '<div class="col-md-12">';
                html += '<h3>Click on Update button to check for new Rock-ons.</h3>';
                html += '</div>';
                html += '</div>';
                html += '</div>';
            }
            return new Handlebars.SafeString(html);
        });
    }

});


RockonInstallWizardView = WizardView.extend({
    initialize: function() {
        WizardView.prototype.initialize.apply(this, arguments);
        this.pages = [];
        this.rockon = this.model.get('rockon');
        this.volumes = new RockOnVolumeCollection(null, {
            rid: this.rockon.id
        });
        this.ports = new RockOnPortCollection(null, {
            rid: this.rockon.id
        });
        this.custom_config = new RockOnCustomConfigCollection(null, {
            rid: this.rockon.id
        });
        this.devices = new RockOnDeviceCollection(null, {
            rid: this.rockon.id
        });
        this.environment = new RockOnEnvironmentCollection(null, {
            rid: this.rockon.id
        });
    },

    fetchVolumes: function() {
        var _this = this;
        this.volumes.fetch({
            success: function() {
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
                _this.fetchDevices();
            }
        });
    },

    fetchCustomConfig: function() {
        var _this = this;
        this.custom_config.fetch({
            success: function() {
                _this.model.set('custom_config', _this.custom_config);
                _this.fetchEnvironment();
            }
        });
    },

    fetchDevices: function() {
        var _this = this;
        this.devices.fetch({
            success: function() {
                _this.model.set('devices', _this.devices);
                _this.fetchCustomConfig();
            }
        });
    },

    fetchEnvironment: function() {
        var _this = this;
        this.environment.fetch({
            success: function() {
                _this.model.set('environment', _this.environment);
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
        if (this.devices.length > 0) {
            this.pages.push(RockonDeviceChoice);
        }
        if (this.environment.length > 0) {
            this.pages.push(RockonEnvironment);
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
        return ((this.pages.length > 1) &&
            ((this.pages.length - 1) == this.currentPageNum));
    },

    finish: function() {
        this.parent.$('#install-rockon-overlay').overlay().close();
        this.parent.render();
    }
});

RockonShareChoice = RockstorWizardPage.extend({
    initialize: function() {
        this.template = window.JST.rockons_install_choice;
        this.vol_template = window.JST.rockons_vol_form;
        this.rockon = this.model.get('rockon');
        this.volumes = this.model.get('volumes');
        this.shares = new ShareCollection();
        this.shares.setPageSize(100);
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.shares.on('reset', this.renderVolumes, this);
    },

    render: function() {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        this.shares.fetch();
        return this;
    },

    renderVolumes: function() {
        this.$('#ph-vols-table').html(this.vol_template({
            volumes: this.volumes.toJSON(),
            shares: this.shares.toJSON()
        }));
        //form validation
        this.volForm = this.$('#vol-select-form');
        var rules = {};
        var messages = {};
        this.volumes.each(function(volume) {
            rules[volume.id] = {
                required: true
            };
            messages[volume.id] = 'Please read the tooltip and make the right selection';
        });
        this.validator = this.volForm.validate({
            rules: rules,
            messages: messages
        });
    },

    save: function() {

        // Validate the form
        if (!this.volForm.valid()) {
            this.validator.showErrors();
            return $.Deferred().reject();
        }

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
        this.ports = this.model.get('ports');
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        this.$('#ph-ports-form').html(this.port_template({
            ports: this.ports.toJSON()
        }));

        // Add form validation
        this.portForm = this.$('#port-select-form');
        var rules = {};
        var messages = {};
        this.ports.each(function(port) {
            rules[port.id] = {
                required: true,
                number: true
            };
            messages[port.id] = 'Please enter a valid port number';
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
            port_map[this.$('#' + port.id).val()] = port.get('containerp');
            return port;
        }, this);
        this.model.set('port_map', port_map);
        return $.Deferred().resolve();
    },
});

RockonCustomChoice = RockstorWizardPage.extend({
    initialize: function() {
        this.template = window.JST.rockons_custom_choice;
        this.cc_template = window.JST.rockons_cc_form;
        this.custom_config = this.model.get('custom_config');
        this.initHandlebarHelpers();
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        //@todo: working only for the ownCloud and Discourse rockons. Fix to work for the rest
        this.$('#ph-cc-form').html(this.cc_template({
            cc: this.custom_config.toJSON()
        }));
        this.cc_form = this.$('#custom-choice-form');
        var rules = {};
        var messages = {};
        this.custom_config.each(function(cc) {
            rules[cc.id] = 'required';
            messages[cc.id] = 'This is a required field.';
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
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('findInputType', function(ccLabel) {
            if (ccLabel.match(/password/i)) {
                return true;
            }
            return false;
        });
    }
});

RockonDeviceChoice = RockonCustomChoice.extend({
    initialize: function() {
        this.template = window.JST.rockons_device_choice;
        this.device_template = window.JST.rockons_device_form;
        this.device_config = this.model.get('devices');
        this.initHandlebarHelpers();
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        this.$('#ph-device-form').html(this.device_template({
            device: this.device_config.toJSON()
        }));
        this.device_form = this.$('#device-choice-form');
        this.$('#ph-device-form').html(this.device_template({
            device: this.device_config.toJSON()
        }));
        this.device_form = this.$('#device-choice-form');

        // Add form validation
        var rules = {};
        var messages = {};
        this.device_config.each(function(device) {
            rules[device.id] = {
                checkDevice: true,
                required: false
            };
        });

        $.validator.addMethod('checkDevice', function(value, element) {
            var regExp = new RegExp(/^\/dev\/[A-Za-z0-9,-/ ]+$/);
            return this.optional(element) || regExp.test(value);
        }, 'Please enter a valid absolute path.');

        this.validator = this.device_form.validate({
            rules: rules,
            messages: messages
        });
        return this;
    },

    save: function() {
        if (!this.device_form.valid()) {
            this.validator.showErrors();
            return $.Deferred().reject();
        }
        var dev_map = {};
        var devices = this.device_config.filter(function(cdev) {
            dev_map[cdev.get('dev')] = this.$('#' + cdev.id).val();
            return cdev;
        }, this);
        this.model.set('dev_map', dev_map);
        return $.Deferred().resolve();
    }
});

RockonEnvironment = RockonCustomChoice.extend({
    initialize: function() {
        RockonCustomChoice.prototype.initialize.apply(this, arguments);
        this.custom_config = this.model.get('environment');
    },

    save: function() {
        if (!this.cc_form.valid()) {
            this.validator.showErrors();
            return $.Deferred().reject();
        }
        var env_map = {};
        var envars = this.custom_config.filter(function(cvar) {
            env_map[cvar.get('key')] = this.$('#' + cvar.id).val();
            return cvar;
        }, this);
        this.model.set('env_map', env_map);
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
        this.dev_map = this.model.get('dev_map');
        this.env_map = this.model.get('env_map');
        this.ports = this.model.get('ports');
        this.devices = this.model.get('devices');
        this.environment = this.model.get('environment');
        this.cc = this.model.get('custom_config');
        this.rockon = this.model.get('rockon');
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        this.$('#ph-summary-table').html(this.table_template({
            share_map: this.share_map,
            port_map: this.port_map,
            cc_map: this.cc_map,
            dev_map: this.dev_map,
            env_map: this.env_map
        }));
        return this;
    },

    save: function() {
        var _this = this;
        //$('button#next-page').prop('disable', true);
        document.getElementById('next-page').disabled = true;
        return $.ajax({
            url: '/api/rockons/' + this.rockon.id + '/install',
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                'ports': this.port_map,
                'shares': this.share_map,
                'cc': this.cc_map,
                'devices': this.dev_map,
                'environment': this.env_map
            }),
            success: function() {
                document.getElementById('next-page').disabled = false;
            },
            error: function(request, status, error) {}
        });
    },
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

RockonInfoView = WizardView.extend({
    initialize: function() {
        WizardView.prototype.initialize.apply(this, arguments);
        this.pages = [RockonInfoSummary, ];
    },

    render: function() {
        WizardView.prototype.render.apply(this, arguments);
        return this;
    },

    modifyButtonText: function() {
        this.$('#prev-page').hide();
        this.$('#next-page').hide();
    }
});

RockonSettingsWizardView = WizardView.extend({
    events: {
        'click #next-page': 'nextPage',
        'click #prev-page': 'prevPage',
        'click #add-label': 'addLabels'
    },

    initialize: function() {
        WizardView.prototype.initialize.apply(this, arguments);
        this.template = window.JST.rockons_wizard_summary;
        this.pages = [RockonSettingsSummary, ];
        this.rockon = this.model.get('rockon');
        this.volumes = new RockOnVolumeCollection(null, {
            rid: this.rockon.id
        });
        this.ports = new RockOnPortCollection(null, {
            rid: this.rockon.id
        });
        this.custom_config = new RockOnCustomConfigCollection(null, {
            rid: this.rockon.id
        });
        this.devices = new RockOnDeviceCollection(null, {
            rid: this.rockon.id
        });
        this.environment = new RockOnEnvironmentCollection(null, {
            rid: this.rockon.id
        });
        this.labels = new RockOnLabelCollection(null, {
            rid: this.rockon.id
        });
        this.containers = new ContainerCollection(null, {
            rid: this.rockon.id
        });

        this.shares = {};
        this.model.set('shares', this.shares);
        this.new_labels = {};
        this.model.set('new_labels', this.new_labels);
        this.evAgg.bind('addLabels', this.addLabels, this);
    },

    fetchVolumes: function() {
        var _this = this;
        this.volumes.fetch({
            success: function() {
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
                _this.fetchDevices();
            }
        });
    },

    fetchDevices: function() {
        var _this = this;
        this.devices.fetch({
            success: function() {
                _this.model.set('devices', _this.devices);
                _this.fetchCustomConfig();
            }
        });
    },

    fetchCustomConfig: function() {
        var _this = this;
        this.custom_config.fetch({
            success: function() {
                _this.model.set('custom_config', _this.custom_config);
                _this.fetchEnvironment();
            }
        });
    },

    fetchEnvironment: function() {
        var _this = this;
        this.environment.fetch({
            success: function() {
                _this.model.set('environment', _this.environment);
                _this.fetchContainers();
            }
        });
    },

    fetchContainers: function() {
        var _this = this;
        this.containers.fetch({
            success: function() {
                _this.model.set('containers', _this.containers);
                _this.fetchLabels();
            }
        });
    },

    fetchLabels: function() {
        var _this = this;
        this.labels.fetch({
            success: function() {
                _this.model.set('labels', _this.labels);
                _this.addPages();
            }
        });
    },

    addLabels: function() {
        this.pages[1] = RockonAddLabel;
        this.pages[2] = RockonSettingsSummary;
        this.pages[3] = RockonSettingsComplete;
        WizardView.prototype.render.apply(this, arguments);
        return this;
    },

    render: function() {
        this.fetchVolumes();
        return this;
    },

    addPages: function() {
        if (this.rockon.get('volume_add_support')) {
            this.pages.push.apply(this.pages, [RockonAddShare, RockonSettingsSummary,
                RockonSettingsComplete
            ]);
        }
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
            this.$('#add-label').html('Add Label');
            this.$('#add-label').css({'display': 'inline'});
            this.$('#next-page').html('Add Storage');
            if (!this.rockon.get('volume_add_support')) {
                this.$('#next-page').hide();
            } else {
                if (this.rockon.get('status') == 'started') {
                    var _this = this;
                    this.$('.wizard-btn').click(function() {
                        //disabling the button so that the backbone event is not triggered after the alert click.
                        _this.$('.wizard-btn').prop('disabled', true);
                        alert('Rock-on must be turned off to change its settings.');
                    });
                }
            }
        } else if (this.currentPageNum == (this.pages.length - 2)) {
            this.$('#prev-page').show();
            this.$('#next-page').html('Next');
        } else if (this.currentPageNum == (this.pages.length - 1)) {
            this.$('#prev-page').show();
            this.$('#add-label').hide();
            this.$('#next-page').html('Submit');
        } else {
            this.$('#prev-page').show();
            this.$('#add-label').hide();
            this.$('#next-page').html('Next');
            this.$('#ph-wizard-buttons').show();
        }
    },

    lastPage: function() {
        return ((this.pages.length > 1) &&
            ((this.pages.length - 1) == this.currentPageNum));
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
        this.shares.setPageSize(100);
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
            shares: this.filtered_shares.map(function(s) {
                return s.toJSON();
            })
        }));
        this.share_form = this.$('#vol-select-form');
        this.validator = this.share_form.validate({
            rules: {
                'volume': 'required',
                'share': 'required'
            },
            messages: {
                'volume': 'Must be a valid unix path. Eg: /data/media',
                'share': 'Select an appropriate Share to map'
            }
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

RockonAddLabel = RockstorWizardPage.extend({
    initialize: function() {
        this.template = window.JST.rockons_add_labels;
        this.sub_template = window.JST.rockons_add_labels_form;
        this.rockon = this.model.get('rockon');
        this.containers = new ContainerCollection(null, {
            rid: this.rockon.id
        });
        this.containers.setPageSize(100);
        this.count = 1;
        this.maxlabels = 10; // Define maximum numbers of labels
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.containers.on('reset', this.renderContainers, this);
    },

    events: {
        'click #b1': 'addField',
        'click .remove-me': 'removeField'
    },

    addField: function(event) {
        event.preventDefault();
        var count = this.count;
        if (count < this.maxlabels) {
            count++;
            this.count = count;
            var nbox = '<div id="label-box' + count +'" class="form-group">' +
                '<label class="col-sm-3 control-label" for="labels">Label:  <span class="required">*</span></label>' +
                '<div class="controls col-sm-5">' +
                '<input class="form-control input-btn" name="labels[]" id="field' + count +'" placeholder="Enter another label" type="text" />' +
                '<button id="remove_' + count + '" class="btn btn-danger remove-me">-</button>' +
                '<button id="b1" class="btn" type="button">+</button>' +
                '</div>' +
                '<i class="fa fa-info-circle fa-lg" title="Enter the desired label in the following form: mycustomlabel"></i>' +
                '</div>';
            var newbox = $(nbox);
            $('.label-box-new').append(newbox);
        } else {
            alert('Maximum number of labels reached.');
        }
    },

    removeField: function(event) {
        event.preventDefault();
        var count = this.count;
        $(event.currentTarget).parent('div').parent('div').remove();
        count--;
        this.count = count;
        return this;
    },

    render: function() {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        this.containers.fetch();
        return this;
    },

    fetchContainers: function() {
        var _this = this;
        this.containers.fetch({
            success: function() {
                _this.model.set('containers', _this.containers);
            }
        });
        return this;
    },

    renderContainers: function() {
        this.containers_map = this.model.get('containers');
        this.used_containers = [];
        var _this = this;
        for (var c in this.containers_map) {
            this.used_containers.push(c);
        }
        this.filtered_containers = this.containers.filter(function(container) {
            if (_this.used_containers.indexOf(container.get('name')) == -1) {
                return container;
            }
        }, this);
        this.$('#ph-add-labels-form').html(this.sub_template({
            containers: this.filtered_containers.map(function(c) {
                return c.toJSON();
            })
        }));
        this.container_form = this.$('#container-select-form');
        this.validator = this.container_form.validate({
            rules: {
                'container': 'required',
                'labels[]': 'required'
            },
            messages: {
                'container': 'Please select a container',
                'labels[]': 'Please enter a label'
            }
        });
        // Ensure previous page is correct
        if (this.rockon.get('volume_add_support')) {
            this.parent.pages[1] = RockonAddShare;
        } else {
        this.parent.pages[1] = RockonAddLabel;
        }
        return this;
    },

    save: function() {
        if (!this.container_form.valid()) {
            this.validator.showErrors();
            return $.Deferred().reject();
        }
        var field_data = $('input[name^=labels]').map(function(idx, elem) {
            if ($(elem).val() != "") {
                return $(elem).val();
            }
        }).get();
        var new_labels = {};
        field_data.forEach(function(prop) {
            new_labels[prop] = this.$('#container').val();
        });
        this.new_labels = new_labels;
        this.model.set('new_labels', this.new_labels);
        return $.Deferred().resolve();
    }
});

RockonInfoSummary = RockstorWizardPage.extend({
    initialize: function() {
        this.template = window.JST.rockons_settings_summary;
        this.sub_template = window.JST.rockons_more_info;
        this.rockon = this.model.get('rockon');
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
    },

    render: function() {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        this.$('#ph-settings-summary-table').html(this.sub_template({
            rockonMoreInfo: this.rockon.get('more_info')
        }));
        return this;
    }
});

RockonSettingsSummary = RockstorWizardPage.extend({
    initialize: function() {
        this.template = window.JST.rockons_settings_summary;
        this.sub_template = window.JST.rockons_settings_summary_table;
        this.rockon = this.model.get('rockon');
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.initHandlebarHelpers();
    },

    render: function() {
        RockstorWizardPage.prototype.render.apply(this, arguments);
        this.$('#ph-settings-summary-table').html(this.sub_template({
            model: this.model,
            volumes: this.model.get('volumes').toJSON(),
            new_volumes: this.model.get('shares'),
            ports: this.model.get('ports').toJSON(),
            cc: this.model.get('custom_config').toJSON(),
            device: this.model.get('devices').toJSON(),
            env: this.model.get('environment').toJSON(),
            labels: this.model.get('labels').toJSON(),
            new_labels: this.model.get('new_labels'),
            rockon: this.model.get('rockon')
        }));
        // Ensure previous page is correct
        if (!$.isEmptyObject(this.model.get('new_labels'))) {
            this.parent.pages[1] = RockonAddLabel;
        } else {
            if (this.rockon.get('volume_add_support')) {
                this.parent.pages[1] = RockonAddShare;
            } else {
                this.parent.pages[1] = RockonAddLabel;
            }
        }
        return this;
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_newVolumes', function() {
            // Display newly-defined shares and their corresponding mapping
            // for confimation before submit in settings_summary_table.jst
            var html = '';
            for (share in this.new_volumes) {
                html += '<tr>';
                html += '<td>Share</td>';
                html += '<td>' + this.new_volumes[share] + '</td>';
                html += '<td>' + share + '</td>';
                html += '</tr>';
            }
            return new Handlebars.SafeString(html);
        });
        Handlebars.registerHelper('display_newLabels', function() {
            // Display newly-defined labels and their corresponding container
            // for confimation before submit in settings_summary_table.jst
            var html = '';
            for (new_label in this.new_labels) {
                html += '<tr>';
                html += '<td>Label</td>';
                html += '<td>' + this.new_labels[new_label] + '</td>';
                html += '<td>' + new_label + '</td>';
                html += '</tr>';
            }
            return new Handlebars.SafeString(html);
        });
    }
});

RockonSettingsComplete = RockstorWizardPage.extend({
    initialize: function() {
        this.template = window.JST.rockons_update_complete;
        this.rockon = this.model.get('rockon');
        this.shares = this.model.get('shares');
        this.new_labels = this.model.get('new_labels');
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
        if (document.getElementById('next-page').disabled) return false;
        document.getElementById('next-page').disabled = true;
        return $.ajax({
            url: '/api/rockons/' + this.rockon.id + '/update',
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                'shares': this.shares,
                'labels': this.new_labels
            }),
            success: function() {}
        });
    }
});
