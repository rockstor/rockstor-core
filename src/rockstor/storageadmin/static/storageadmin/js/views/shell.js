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

ShellView = RockstorLayoutView.extend({
    events: {
        'switchChange.bootstrapSwitch': 'switchStatus',
        'click #fullscreen': 'FullScreenSwitch'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.shell_shell;
        this.serviceName = 'shellinaboxd';
        this.service = new Service({
            name: this.serviceName
        });
        this.dependencies.push(this.service);
    },

    render: function() {
        var _this = this;
        this.fetch(this.renderShell, this);
        return this;
    },

    renderShell: function() {

        $(this.el).html(this.template({
            service: this.service
        }));

        //initalize Bootstrap Switch
        this.$('[type=\'checkbox\']').bootstrapSwitch();
        this.$('input[name="shell-export-checkbox"]').bootstrapSwitch('state', this.service.get('status'), true);
        this.$('[type=\'checkbox\']').bootstrapSwitch('onColor', 'success'); //left side text color
        this.$('[type=\'checkbox\']').bootstrapSwitch('offColor', 'danger'); //right side text color

        // Display Shell In a Box Service Warning
        if (!this.service.get('status')) {
            this.$('#shell-warning').show();
            this.$('div[name="shell-container"]').show();
        } else {
            this.$('#rockstor-shell')[0].src = '/shell';
            this.$('#rockstor-shell').show();
            this.$('#fullscreen').show();
        }
    },

    FullScreenSwitch: function() {
        //nicely switch our console between normal size and fullscreen
        //fullscreen requires crossbrowser checks
        //Back to normal size just with ESC, as suggested by browser
        var rockstor_shell = this.$('#rockstor-shell')[0];
        if (rockstor_shell.requestFullscreen) {
            rockstor_shell.requestFullscreen();
        } else if (rockstor_shell.webkitRequestFullscreen) {
            rockstor_shell.webkitRequestFullscreen();
        } else if (rockstor_shell.mozRequestFullScreen) {
            rockstor_shell.mozRequestFullScreen();
        } else if (rockstor_shell.msRequestFullscreen) {
            rockstor_shell.msRequestFullscreen();
        }
    },

    switchStatus: function(event, state) {
        if (state) {
            this.startService();
        }
    },

    startService: function() {
        var _this = this;
        this.setStatusLoading(this.serviceName, true);
        $.ajax({
            url: '/api/sm/services/shellinaboxd/start',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(_this.serviceName, false);
                _this.$('div[name="shell-container"]').hide();
                _this.$('#shell-warning').hide();
                _this.$('#rockstor-shell')[0].src = '/shell';
                _this.$('#rockstor-shell').show();
                _this.$('#fullscreen').show();

            },
            error: function(xhr, status, error) {
                _this.setStatusError(_this.serviceName, xhr);
                _this.$('div[name="shell-container"]').show();
                _this.$('#shell-warning').show();
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

Cocktail.mixin(ShellView, PaginationMixin);