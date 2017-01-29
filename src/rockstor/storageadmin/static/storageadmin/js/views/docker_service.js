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

DockerServiceView = Backbone.View.extend({
    events: {
        'switchChange.bootstrapSwitch': 'switchStatus',
    },

    initialize: function() {
        this.template = window.JST.rockons_docker_service;
        this.serviceName = 'docker';
        this.service = new Service({
            name: this.serviceName
        });
        this.parentView = this.options.parentView;
        this.updateFreq = 30000;
    },

    render: function() {
        var _this = this;
        this.service.fetch({
            success: function(collection, response, options) {
                _this.renderPage();
            }
        });
        return this;
    },

    renderPage: function() {
        $(this.el).html(this.template({
            service: this.service
        }));

        //initalize Bootstrap Switch
        this.$('[type=\'checkbox\']').bootstrapSwitch();
        if (typeof this.current_status == 'undefined') {
            this.current_status = this.service.get('status');
        }
        this.$('input[name="rockon-service-checkbox"]').bootstrapSwitch('state', this.current_status, true);
        this.$('[type=\'checkbox\']').bootstrapSwitch('onColor', 'success'); //left side text color
        this.$('[type=\'checkbox\']').bootstrapSwitch('offColor', 'danger'); //right side text color

        return this;
    },

    switchStatus: function(event, state) {
        if (!this.service.get('config')) {
            app_router.navigate('services/docker/edit', {
                trigger: true
            });
        } else {
            if (state) {
                this.startService();
            } else {
                this.stopService();
            }
        }
    },

    startService: function() {
        var _this = this;
        var serviceName = this.serviceName;
        this.setStatusLoading(serviceName, true);
        $.ajax({
            url: '/api/sm/services/docker/start',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                location.reload(true);
                _this.setStatusLoading(serviceName, false);
            },
            error: function(xhr, status, error) {
                _this.setStatusError(serviceName, xhr);
            }
        });
    },

    stopService: function() {
        var _this = this;
        var serviceName = this.serviceName;
        this.setStatusLoading(serviceName, true);
        $.ajax({
            url: '/api/sm/services/docker/stop',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                location.reload(true);
                _this.setStatusLoading(serviceName, false);
            },
            error: function(xhr, status, error) {
                _this.setStatusError(serviceName, xhr);
            }
        });
    },

    setStatusLoading: function(serviceName, show) {
        var statusEl = this.$('div.command-status[data-service-name="' + serviceName + '"]');
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
        statusEl.click(function() {
            errPopup.overlay().load();
        });
    },

});