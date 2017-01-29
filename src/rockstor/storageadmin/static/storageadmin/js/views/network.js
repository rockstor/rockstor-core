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

NetworkView = Backbone.View.extend({

    events: {
        'click a[data-action=delete]': 'deleteConnection',
        'switchChange.bootstrapSwitch': 'switchStatus'
    },

    initialize: function() {
        this.template = window.JST.network_network;
        this.collection = new NetworkConnectionCollection();
        this.collection.on('reset', this.renderNetwork, this);
        this.devices = new NetworkDeviceCollection();
        this.devices.on('reset', this.renderNetwork, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        var _this = this;
        this.collection.fetch();
        this.devices.fetch();
        return this;
    },


    renderNetwork: function() {
        var _this = this;
        this.pc = [];
        this.cc = [];
        for (var i = 0; i < this.collection.length; i++) {
            var c = this.collection.at(i);
            if (c.get('master')) {
                this.cc.push(c.toJSON());
            } else {
                this.pc.push(c.toJSON());
            }
        }

        $(this.el).empty();
        $(this.el).append(this.template({
            collection: this.collection,
            connections: this.collection.toJSON(),
            parent_connections: this.pc,
            child_connections: this.cc,
            devices: this.devices.toJSON()
        }));
        setApplianceName();

        //Initialize bootstrap switch
        this.$('[type=\'checkbox\']').bootstrapSwitch();
        this.$('[type=\'checkbox\']').bootstrapSwitch('onColor', 'success'); //left side text color
        this.$('[type=\'checkbox\']').bootstrapSwitch('offColor', 'danger'); //right side text color
    },

    switchStatus: function(event, state) {
        var connectionId = $(event.target).attr('data-connection-id');
        if (state) {
            this.toggleConnection(connectionId, 'up');
        } else {
            this.toggleConnection(connectionId, 'down');
        }
    },

    toggleConnection: function(connectionId, switchState) {
        var _this = this;
        $.ajax({
            url: 'api/network/connections/' + connectionId + '/' + switchState,
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(connectionId, false);
                _this.render();
            },
            error: function(xhr, status, error) {
                _this.setStatusError(connectionId, xhr);
            }
        });
    },

    setStatusLoading: function(connectionId, show) {
        var statusEl = this.$('div.command-status[data-connection-id="' + connectionId + '"]');
        if (show) {
            statusEl.html('<img src="/static/storageadmin/img/ajax-loader.gif"></img>');
        } else {
            statusEl.empty();
        }
    },

    setStatusError: function(connectionId, xhr) {
        var statusEl = this.$('div.command-status[data-connection-id="' + connectionId + '"]');
        var msg = parseXhrError(xhr);
        // remove any existing error popups
        $('body').find('#' + connectionId + 'err-popup').remove();
        // add icon and popup
        statusEl.empty();
        var icon = $('<i>').addClass('icon-exclamation-sign').attr('rel', '#' + connectionId + '-err-popup');
        statusEl.append(icon);
        var errPopup = this.$('#' + connectionId + '-err-popup');
        var errPopupContent = this.$('#' + connectionId + '-err-popup > div');
        errPopupContent.html(msg);
        statusEl.click(function() {
            errPopup.overlay().load();
        });
    },

    deleteConnection: function(event) {
        if (confirm('Are you sure to delete the connection?')) {
            var _this = this;
            var button = $(event.currentTarget);
            var connectionId = button.attr('id');
            if (buttonDisabled(button)) return false;
            disableButton(button);
            $.ajax({
                url: '/api/network/connections/' + connectionId,
                type: 'DELETE',
                dataType: 'json',
                success: function() {
                    _this.collection.fetch({
                        reset: true
                    });
                    enableButton(button);
                    _this.render();
                },
                error: function(xhr, status, error) {
                    enableButton(button);
                }
            });
        }
    },

    initHandlebarHelpers: function() {
        var _this = this;
        Handlebars.registerHelper('getState', function(state) {
            var html = '';
            if (state == 'activated') {
                html = 'checked';
            }
            return new Handlebars.SafeString(html);
        });
        Handlebars.registerHelper('belongsToConnection', function(connectionId, deviceConnectionId) {
            if (connectionId == deviceConnectionId) {
                return true;
            }
            for (var i = 0; i < _this.cc.length; i++) {
                if (_this.cc[i].master == connectionId &&
                    _this.cc[i].id == deviceConnectionId) {
                    return true;
                }
            }
            return false;
        });
        Handlebars.registerHelper('hasChildren', function(connection, opts) {
            for (var i = 0; i < _this.cc.length; i++) {
                if (_this.cc[i].master == connection.id) {
                    return opts.fn(this);
                }
            }
            return opts.inverse(this);
        });
    }

});