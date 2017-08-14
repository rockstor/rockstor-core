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


NetworkConnectionView = RockstorLayoutView.extend({

    events: {
        'click #cancel': 'cancel',
        'change #method': 'renderMethodOptionalFields',
        'change #ctype': 'renderCTypeOptionalFields'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.connectionId = this.options.connectionId || null;
        this.connection = null;
        this.template = window.JST.network_new_connection;
        this.devices = new NetworkDeviceCollection();
        this.devices.on('reset', this.renderDevices, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        this.devices.fetch();
        if (this.connectionId != null) {
            this.connection = new NetworkConnection({
                id: this.connectionId
            });
            this.connection.fetch();
        }
        return this;
    },

    renderDevices: function() {
        var _this = this;
        $(this.el).empty();
        var connection;
        if (this.connection) {
            connection = this.connection.toJSON();
        }
        $(this.el).append(this.template({
            connection: connection,
            devices: this.devices.toJSON(),
            ctypes: ['ethernet', 'team', 'bond'],
            teamProfiles: ['broadcast', 'roundrobin', 'activebackup', 'loadbalance', 'lacp'],
            bondProfiles: ['balance-rr', 'active-backup', 'balance-xor', 'broadcast',
                '802.3ad', 'balance-tlb', 'balance-alb'
            ]
        }));

        if (this.connection) {
            this.renderCTypeOptionalFields();
        }

        this.validator = this.$('#new-connection-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                name: 'required',
                ipaddr: {
                    required: {
                        depends: function(element) {
                            return (_this.$('#method').val() == 'manual');
                        }
                    }
                },
                team_profile: {
                    required: {
                        depends: function(element) {
                            return (_this.$('#ctype').val() == 'team');
                        }

                    }
                },
                bond_profile: {
                    required: {
                        depends: function(element) {
                            return (_this.$('#ctype').val() == 'bond');
                        }

                    }
                },
                devices: {
                    required: {
                        depends: function(element) {
                            return (_this.$('#ctype').val() == 'team');
                        }

                    }
                }
            },
            submitHandler: function() {
                var button = _this.$('#submit');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var cancelButton = _this.$('#cancel');
                disableButton(cancelButton);
                var data = _this.$('#new-connection-form').getJSON();
                var conn = _this.connection;
                if (!_this.connection) {
                    conn = new NetworkConnection();
                }
                conn.save(data, {
                    success: function(model, response, options) {
                        app_router.navigate('network', {
                            trigger: true
                        });
                    },
                    error: function(model, response, options) {
                        enableButton(button);
                        enableButton(cancelButton);
                    }
                });
            }
        });

        this.$('#devices').select2();

        this.$('#name').tooltip({
            html: true,
            placement: 'right',
            title: 'Choose a unique name for this network connection. Eg: Connection1, Team0, Bond0 etc..'
        });
        this.$('#team_profile').tooltip({
            html: true,
            placement: 'right',
            title: '<strong>broadcast</strong> - Simple runner which directs the team device to transmit packets via all ports.<br>' +
                '<strong>roundrobin</strong> - Simple runner which directs the team device to transmits packets in a round-robin fashion.<br>' +
                '<strong>activebackup</strong> - Watches for link changes and selects active port to be used for data transfers.<br>' +
                '<strong>loadbalance</strong> -  To do passive load balancing, runner only sets up BPF hash function which will determine port for packet transmit.' +
                'To do active load balancing, runner moves hashes among available ports trying to reach perfect balance.<br>' +
                '<strong>lacp</strong> - Implements 802.3ad LACP protocol. Can use same Tx port selection possibilities as loadbalance runner.'
        });
        this.$('#device').tooltip({
            html: true,
            placement: 'right',
            title: 'Choose a device to add to the connection. <b>WARNING!!!</b> you are NOT prevented from choosing a device that belongs to another connection. If you do so, the connection that is last activated claims the device.'
        });
        this.$('#ipaddr').tooltip({
            html: true,
            placement: 'right',
            title: 'A usable static IP address(in CIDR notation) for your network. Eg: 192.168.1.10/24. If IP is provided without netmask bit count, eg: 192.168.1.10, then it defaults to 192.168.1.10/32'
        });
        this.$('#gateway').tooltip({
            html: true,
            placement: 'right',
            title: 'IP address of your Gateway.'
        });
        this.$('#dns_servers').tooltip({
            html: true,
            placement: 'right',
            title: 'A comma separated list of DNS server addresses.'
        });
        this.$('#search_domains').tooltip({
            html: true,
            placement: 'right',
            title: 'A comma separated list of DNS search domains.'
        });
        this.$('#mtu').tooltip({
            html: true,
            placement: 'right',
            title: 'Enter a value in [1500-9000] range. Defaults to 1500.'
        });
    },

    // hide fields when selected method is auto
    renderMethodOptionalFields: function() {
        var selection = this.$('#method').val();
        if (selection == 'auto') {
            $('#methodOptionalFields').hide();
        } else {
            $('#methodOptionalFields').show();
        }
    },

    // show/hide respective dropdowns based on selected connection type
    renderCTypeOptionalFields: function() {
        var selection = this.$('#ctype').val();
        if (this.connection) {
            selection = this.connection.get('ctype');
        }
        if (selection == 'team') {
            $('#teamProfiles, #multiDevice').show();
            $('#bondProfiles, #singleDevice').hide();
        } else if (selection == 'ethernet') {
            $('#teamProfiles, #multiDevice #bondProfiles').hide();
            $('#singleDevice').show();
        } else {
            //bond
            $('#teamProfiles, #singleDevice').hide();
            $('#bondProfiles, #multiDevice').show();
        }
    },

    initHandlebarHelpers: function() {
        var _this = this;
        Handlebars.registerHelper('selectedCtype', function(ctype) {
            var html = '';
            if (ctype == _this.connection.get('ctype')) {
                html = 'selected="selected"';
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('selectedTeamProfile', function(profile) {
            var html = '';
            if (profile == _this.connection.get('team_profile')) {
                html = 'selected="selected"';
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('selectedBondProfile', function(profile) {
            var html = '';
            if (profile == _this.connection.get('bond_profile')) {
                html = 'selected="selected"';
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('selectedDevice', function(device) {
            var html = '';
            if (device.cname == _this.connection.get('name')) {
                html = 'selected="selected"';
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('isAuto', function(connection, opts) {
            if (connection.ipv4_method == 'auto') {
                return opts.fn(this);
            }
            return opts.inverse(this);
        });
    },

    cancel: function(event) {
        event.preventDefault();
        app_router.navigate('network', {
            trigger: true
        });
    }

});
