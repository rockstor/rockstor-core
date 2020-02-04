/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
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

ConfigureServiceView = RockstorLayoutView.extend({

    events: {
        'click #cancel': 'cancel',
        'click #security': 'toggleFormFields',
        'click #enabletls': 'toggleCertUrl',
        'click #mode': 'toggleNutFields'
    },

    initialize: function() {
        // call initialize of base
        var _this = this;
        this.constructor.__super__.initialize.apply(this, arguments);
        this.serviceName = this.options.serviceName;
        this.adStatus = this.options.adStatus;
        // set template
        this.template = window.JST['services_configure_' + this.serviceName];
        this.rules = {
            ntpd: {
                server: 'required'
            },
            smb: {
                workgroup: 'required'
            },
            nis: {
                domain: 'required',
                server: 'required'
            },
            snmpd: {
                syslocation: 'required',
                syscontact: 'required',
                rocommunity: 'required'
            },
            ldap: {
                server: 'required',
                basedn: 'required',
                cert: {
                    required: {
                        depends: function(element) {
                            return _this.$('#enabletls').prop('checked');
                        }
                    }
                }
            },
            docker: {
                rootshare: 'required'
            },
            nut: {
                mode: 'required',
                upsmon: 'required',
                upsname: 'required',
                driver: 'required',
                nutuser: 'required',
                password: 'required',
                nutserver: {
                    required: {
                        depends: function(element) {
                            return (_this.$('#mode').val() == 'netclient');
                        }
                    }
                }
            },
            shellinaboxd: {
                shelltype: 'required',
                css: 'required'
            },
            'active-directory': {
                domain: 'required',
                username: 'required',
                password: 'required'
            },
            replication: {
                listener_port: 'required',
                network_interface: 'required'
            },
            rockstor: {
                listener_port: 'required'
            }
        };

        this.formName = this.serviceName + '-form';
        this.service = new Service({
            name: this.serviceName
        });
        this.dependencies.push(this.service);
        this.shares = new ShareCollection();
        this.shares.setPageSize(100);
        this.dependencies.push(this.shares);
        this.network = new NetworkConnectionCollection();
        this.dependencies.push(this.network);
        this.initHandlebarHelpers();
    },

    render: function() {

        this.fetch(this.renderServiceConfig, this);
        return this;
    },

    renderServiceConfig: function() {

        var _this = this;
        var default_port = 443;
        if (this.service.get('name') == 'replication') {
            default_port = 10002;
        }
        var config = this.service.get('config');
        var configObj = {};
        if (config != null) {
            configObj = JSON.parse(config);
        }
        if (configObj.listener_port) {
            default_port = configObj.listener_port;
        }
        var nutShutdownTimes = {
            'When Battery Low': 0,
            'after 30 seconds': 30,
            'after 1 minute': 60,
            'after 2 minutes': 120,
            'after 4 minutes': 240,
            'after 8 minutes': 480,
            'after 16 minutes': 960,
            'after 32 minutes': 1920
        };
        _this.nutShutdownTimes = nutShutdownTimes;
        $(this.el).html(this.template({
            service: this.service,
            serviceName: this.service.get('display_name'),
            config: configObj,
            shares: this.shares,
            network: this.network,
            defaultPort: default_port,
            adStatus: this.adStatus,
            nutShutdownTimes: nutShutdownTimes
        }));

        this.$('#nis-form :input').tooltip({
            html: true,
            placement: 'right'
        });
        this.$('#snmpd-form :input').tooltip({
            html: true,
            placement: 'right'
        });
        this.$('#ldap-form :input').tooltip({
            html: true,
            placement: 'right'
        });
        this.$('#ntpd-form :input').tooltip({
            html: true,
            placement: 'right'
        });
        this.$('#smb-form #global_config').tooltip({
            html: true,
            placement: 'right',
            template: '<div class="tooltip" role="tooltip"><div class="tooltip-arrow"></div> \
                    <div class="tooltip-inner size300"></div></div>',
            title: 'These lines will be added to the [global] section of smb.conf<br/><br/> \
                    - <strong>Inline comments with # or ; are not allowed, Samba testparm <u>will fail</u></strong><br/><br/> \
                    - <strong>Samba params syntax</strong>:<br/>param = value (1 space both sides of equal sign)<br/><br/> \
                    - <strong>Samba params with equals inside value field (ex. socket options param)</strong>:<br/>socket options = SO_SNDBUF=131072<br/>(spaces on first equal, <u>no spaces</u> around others)<br/><br/> \
                    Please check <a href="https://www.samba.org/samba/docs/man/manpages/smb.conf.5.html" target="_new">Samba official docs</a> for further information'
        });
        this.$('#docker-form #root_share').tooltip({
            html: true,
            placement: 'right',
            title: 'We strongly recommend that you create a separate Share(at least 5GB size) for this purpose. During the lifetime of Rock-ons, several snapshots will be created and space could fill up quickly. It is best managed in a separate Share to avoid clobbering other data.'
        });
        this.$('#active-directory-form #domain').tooltip({
            html: true,
            placement: 'right',
            title: 'Windows Active Directory or Domain Controller to connect to.'
        });
        this.$('#active-directory-form #username').tooltip({
            html: true,
            placement: 'right',
            title: 'Administrator username to use for authentication while joining the domain. Eg: Administrator'
        });
        this.$('#active-directory-form #password').tooltip({
            html: true,
            placement: 'right',
            title: 'Password for the above username.'
        });
        this.$('#active-directory-form #idmap_range').tooltip({
            html: true,
            placement: 'right',
            title: 'Default should work for most cases. rid idmap backend is the only one supported. The default range is 10000 - 999999.'
        });
        this.$('#smartd-form #smartd_config').tooltip({
            html: true,
            placement: 'right',
            title: 'Following are a few example directives. For complete information, read smartd.conf manpage.<br> \
To monitor all possible errors on all disks: <br> <strong>DEVICESCAN -a</strong> <br> \
To monitor /dev/sdb and /dev/sdc but ignore other devices: <br> <strong>/dev/sdb -a</strong> <br> <strong>/dev/sdc -a</strong> <br> \
To email potential problems: <br> <strong>DEVICESCAN -m user@example.com</strong> <br> \
To alert on temperature changes: <br> <strong>DEVICESCAN -W 4,35,40</strong> <br>'
        });
        this.$('#nut-form #mode').tooltip({
            html: true,
            placement: 'right',
            container: 'body',
            title: '<strong>Nut Mode</strong> — Select the overall mode of Network UPS Tools operation. The drop-down list offers the following options:<br> \
<ul>\
<li><strong>Standalone</strong> — The most common and recommended mode if you have a locally connected UPS and don\'t wish for Rockstor to act as a NUT server to any other LAN connected machines.</li> \
<li><strong>Net server</strong> — Is like Standalone only it also offers NUT services to other machines on the network who are running in Net client mode.</li> \
<li><strong>Net client</strong> — Connect to an existing NUT server.</li> \
</ul>'
        });
        this.$('#nut-form #upsname').tooltip({
            html: true,
            placement: 'right',
            title: 'The internal name for the UPS eg "ups". A single word with no special characters ( " = # space or backslash ) Defaults to "ups".'
        });
        this.$('#nut-form #nutserver').tooltip({
            html: true,
            placement: 'right',
            title: 'The hostname or IP address of the NUT server when in Net Client mode. Otherwise this is usually localhost'
        });
        this.$('#nut-form #nutuser').tooltip({
            html: true,
            placement: 'right',
            title: 'The NUT username (not a Rockstor user). Must be a single word without special characters and is case sensitive. Defaults to "monuser".'
        });
        this.$('#nut-form #password').tooltip({
            html: true,
            placement: 'right',
            title: 'The password for the above NUT user.'
        });
        this.$('#nut-form #upsmon').tooltip({
            html: true,
            placement: 'right',
            title: '<strong>Monitor Mode</strong>:<br> \
<ul>\
<li><strong>Master</strong> - Default, this system will shutdown last, allowing slave NUT systems time to shutdown first. UPS data port is most likely directly connected to this system.</li> \
<li><strong>Slave</strong> - This system shuts down as soon as power is critical, it does not wait for any other NUT systems. Mostly used when in netclient mode and no direct UPS data connection.</li> \
</ul>'
        });
        this.$('#nut-form #driver').tooltip({
            html: true,
            placement: 'right',
            title: 'Driver for your UPS. Please see the NUT <a href="http://www.networkupstools.org/stable-hcl.html" target="_blank">Hardware Compatibility List for guidance.</a>'
        });
        this.$('#nut-form #desc').tooltip({
            html: true,
            placement: 'right',
            title: 'Human Friendly name for this UPS device. Defaults to "Rockstor UPS".'
        });
        this.$('#nut-form #port').tooltip({
            html: true,
            placement: 'right',
            title: 'Device name for how this UPS is connected. E.g for the first serial port use "/dev/ttyS0" or if using a USB to serial port adapter then "/dev/ttyUSB0". Use "auto" if connected direct via USB.'
        });
        this.$('#nut-form #shutdowntimer').tooltip({
            html: true,
            placement: 'right',
            title: 'How long the UPS is "On Battery (OB)" before NUT initiates a "Forced Shutdown" (FSD) event. In netclient mode the netserver setting, if set for a shorter period, takes priority and the netserver will attempt to ensuring all netclients are shutdown first.'
        });
        this.$('#replication-form #network_interface').tooltip({
            html: true,
            placement: 'right',
            title: 'Select one of the available Network interfaces to be used by the listener.'
        });
        this.$('#replication-form #listener_port').tooltip({
            html: true,
            placement: 'right',
            title: 'A valid port number(between 1-65535) for the listener. Default/Suggested port -- 10002'
        });
        this.$('#rockstor-form #network_interface').tooltip({
            html: true,
            placement: 'right',
            title: 'Select the Network connection for Rockstor. If you leave the selection blank, service will listen on all interfaces.<b>WARNING!!!</b> UI may become inaccessible after changing the interface. It should be available on the new interface IP/Hostname after a momentary pause.'
        });
        this.$('#rockstor-form #listener_port').tooltip({
            html: true,
            placement: 'right',
            title: 'While default port(443) is recommended for most users, advanced users can change it to access UI on a different port. <b>Changing the port will make UI inaccessible.</b> After a momentary pause, it should be available on the new port.'
        });
        this.$('#shellinaboxd-form #shelltype').tooltip({
            html: true,
            placement: 'right',
            title: '<strong>LOGIN</strong> is default Shell In a Box connection method, like a login via console (root direct login not allowed, su required)<br/> \
        <strong>SSH</strong> connection with root user allowed. Less secure for system'
        });
        this.$('#shellinaboxd-form #css').tooltip({
            html: true,
            placement: 'right',
            title: 'Choose between Black on White or White on Black layout'
        });
        this.$('#shellinaboxd-form #detach').tooltip({
            html: true,
            placement: 'left',
            title: 'Remember to allow Rockstor server on popup blockers to avoid annoying messages'
        });

        this.validator = this.$('#' + this.formName).validate({
            onfocusout: false,
            onkeyup: false,
            rules: this.rules[this.serviceName],

            submitHandler: function() {
                var button = _this.$('#submit');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var data;
                if (_this.formName == 'snmpd-form') {
                    var optionsText = _this.$('#options').val();
                    var entries = [];
                    if (!_.isNull(optionsText) && optionsText.trim() != '') entries = optionsText.trim().split('\n');
                    var params = (_this.$('#' + _this.formName).getJSON());
                    params.aux = entries;
                    data = JSON.stringify({
                        config: params
                    });
                } else {
                    data = JSON.stringify({
                        config: _this.$('#' + _this.formName).getJSON()
                    });
                }

                var jqxhr = $.ajax({
                    url: '/api/sm/services/' + _this.serviceName + '/config',
                    type: 'POST',
                    contentType: 'application/json',
                    dataType: 'json',
                    data: data
                });

                jqxhr.done(function() {
                    enableButton(button);
                    $('#services_modal').modal('hide');
                    app_router.navigate('/services', {
                        trigger: true
                    });
                });

                jqxhr.fail(function(xhr, status, error) {
                    enableButton(button);
                });

            }
        });

        this.toggleNutFields();
        return this;
    },

    cancel: function(event) {

        event.preventDefault();
        $('#services_modal').modal('hide');
    },

    toggleFormFields: function() {

        if (this.$('#security').val() == 'ads') {
            this.$('#realm').removeAttr('disabled');
        } else {
            this.$('#realm').attr('disabled', 'true');
        }
        if (this.$('#security').val() == 'ads' ||
            this.$('#security').val() == 'domain') {
            this.$('#templateshell').removeAttr('disabled');
        } else {
            this.$('#templateshell').attr('disabled', 'true');
        }
    },

    toggleNutFields: function() {

        if (this.$('#mode').val() == 'standalone') {
            this.$('#monitor-mode').hide();
            this.$('#upsmon').attr('value', 'master');
            this.$('#ups-name').hide();
            this.$('#upsname').attr('value', 'ups');
            this.$('#ups-description').hide();
            this.$('#desc').attr('value', 'Rockstor UPS');
            this.$('#nut-driver').show();
            this.$('#ups-port').show();
            this.$('#nut-server').hide();
            this.$('#nutserver').attr('value', 'localhost');
        } else if (this.$('#mode').val() == 'netserver') {
            this.$('#monitor-mode').show();
            this.$('#ups-name').show();
            this.$('#ups-description').show();
            this.$('#nut-server').hide();
            this.$('#nutserver').attr('value', 'localhost');
            this.$('#nut-driver').show();
            this.$('#ups-port').show();
        } else { // probably has value of netclient or unknown
            this.$('#monitor-mode').hide();
            this.$('#upsmon').attr('value', 'slave');
            this.$('#ups-name').show();
            this.$('#ups-description').show();
            this.$('#nut-driver').hide();
            this.$('#driver').attr('value', 'nutclient');
            this.$('#ups-port').hide();
            this.$('#port').attr('value', 'auto');
            this.$('#nut-server').show();
        }
    },

    toggleCertUrl: function() {

        var cbox = this.$('#enabletls');
        if (cbox.prop('checked')) {
            this.$('#cert-ph').css('visibility', 'visible');
        } else {
            this.$('#cert-ph').css('visibility', 'hidden');
        }
    },

    initHandlebarHelpers: function() {

        //ShellInABox
        Handlebars.registerHelper('display_shelltype_options', function() {

            var html = '',
                _this = this;
            var avail_shells = ['LOGIN', 'SSH'];
            _.each(avail_shells, function(shell, index) {
                if (shell == _this.config.shelltype) {
                    html += '<option value="' + shell + '" selected="selected">';
                    html += shell + '</option>';
                } else {
                    html += '<option value="' + shell + '">' + shell + '</option>';
                }
            });
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('display_shellstyle_options', function() {

            var html = '',
                _this = this;
            var avail_styles = {
                'white-on-black': 'White on Black',
                'black-on-white': 'Black on White'
            };
            _.each(avail_styles, function(key, val) {
                if (val == _this.config.css) {
                    html += '<option value="' + val + '" selected="selected">';
                    html += key + '</option>';
                } else {
                    html += '<option value="' + val + '">' + key + '</option>';
                }
            });
            return new Handlebars.SafeString(html);
        });

        //Samba Config page
        Handlebars.registerHelper('display_smb_params', function() {

            var params = [],
                _this = this;
            _.each(_this.config, function(val, key) {
                if (key != 'workgroup') {
                    params.push(key + ' = ' + val);
                }
            });
            return params.join('\n');
        });

        Handlebars.registerHelper('isEnabledAD', function(opts) {

            var _this = this;
            if (_this.adStatus == 0) {
                return opts.fn(this);
            }
            return opts.inverse(this);
        });

        //NUT-UPS
        Handlebars.registerHelper('display_nutMode_options', function() {

            var html = '',
                _this = this;
            var nutModeTypes = ['standalone', 'netserver', 'netclient'];
            _.each(nutModeTypes, function(mode, index) {
                if (mode == _this.config.mode) {
                    html += '<option value="' + mode + '" selected="selected">';
                    html += mode + '</option>';
                } else {
                    html += '<option value="' + mode + '">' + mode + '</option>';
                }
            });
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('display_monitorMode_options', function() {

            var html = '',
                _this = this;
            var nutMonitorTypes = ['master', 'slave'];
            _.each(nutMonitorTypes, function(upsmon, index) {
                if (upsmon == _this.config.upsmon) {
                    html += '<option value="' + upsmon + '" selected="selected">';
                    html += upsmon + '</option>';
                } else {
                    html += '<option value="' + upsmon + '">' + upsmon + '</option>';
                }
            });
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('display_nutDriver_options', function() {

            var html = '',
                _this = this;
            var nutDriverTypes = ['apcsmart', 'apcsmart-old', 'apcupsd-ups', 'bcmxcp', 'bcmxcp_usb', 'belkin', 'belkinunv', 'bestfcom', 'bestfortress', 'bestuferrups', 'bestups', 'blazer_ser', 'blazer_usb', 'dummy-ups', 'etapro', 'everups', 'gamatronic', 'genericups', 'isbmex', 'ivtscd', 'liebert', 'liebert-esp2', 'masterguard', 'metasys', 'mge-shut', 'mge-utalk', 'microdowell', 'nutclient', 'nutdrv_qx', 'oldmge-shut', 'oneac', 'optiups', 'powercom', 'powerpanel', 'rhino', 'richcomm_usb', 'riello_ser', 'riello_usb', 'safenet', 'skel', 'snmp-ups', 'solis', 'tripplite', 'tripplite_usb', 'tripplitesu', 'upscode2', 'usbhid-ups', 'victronups'];
            _.each(nutDriverTypes, function(driver, index) {
                if (driver == _this.config.driver) {
                    html += '<option value="' + driver + '" selected="selected">';
                    html += driver + '</option>';
                } else {
                    html += '<option value="' + driver + '">' + driver + '</option>';
                }
            });
            return new Handlebars.SafeString(html);
        });

        // NUT-UPS helper to fill dropdown with shutdown timing values
        // eg by dynamically generating lines of the following form:
        // <option value="60">After 1 minute</option>
        Handlebars.registerHelper('display_nutShutdownTimer_options', function() {

            var html = '',
                _this = this;
            if (_this.config.shutdowntimer == null) {
                // if no previous setting then default to 0 = "when Battery Low"
                _this.config.shutdowntimer = '0';
            }
            for (var timeString in this.nutShutdownTimes) {
                if (this.nutShutdownTimes[timeString] == _this.config.shutdowntimer) {
                    // we have found our current setting so mark it selected
                    html += '<option value="' + this.nutShutdownTimes[timeString] + '" selected="selected">';
                    html += timeString + '</option>';
                } else {
                    html += '<option value="' + this.nutShutdownTimes[timeString] + '">' + timeString + '</option>';
                }
            }
            return new Handlebars.SafeString(html);
        });

        //Replication
        Handlebars.registerHelper('display_networkInterface_options', function() {

            var html = '',
                _this = this;
            this.network.each(function(ni, index) {
                var niName = ni.get('name');
                var niLongName = niName + ' [IP: ' + ni.get('ipv4_addresses') + ']';
                if (!ni.get('master')) {
                    if (niName == _this.config.network_interface) {
                        html += '<option value="' + niName + '" selected="selected"> ' + niLongName + '</option>';
                    } else {
                        html += '<option value="' + niName + '">' + niLongName + '</option>';
                    }
                }
            });
            return new Handlebars.SafeString(html);
        });


        //Rockon template
        Handlebars.registerHelper('display_rockon_shares', function() {

            var html = '',
                _this = this;
            if (this.shares.length === 0) {
                html += '<p>You currently have no Shares. You will need a share to run the Rock-ons service.</p>';
                html += '<a href="#add_share">Add a Share</a>';
            } else {
                html += '<select class="form-control" name="root_share" id="root_share" data-placeholder="Select root share">';
                html += '<option></option>';
                this.shares.each(function(share, index) {
                    var shareName = share.get('name');
                    if (shareName == _this.config.root_share) {
                        html += '<option value="' + shareName + '" selected="selected">  ' + shareName + ' </option>';
                    } else {
                        html += '<option value="' + shareName + '">' + shareName + ' </option>';
                    }
                });
                html += '</select>';
            }
            return new Handlebars.SafeString(html);
        });
    }
});
