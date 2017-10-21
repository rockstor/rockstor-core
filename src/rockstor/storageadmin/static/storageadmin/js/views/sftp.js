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

SFTPView = RockstorLayoutView.extend({
    events: {
        'switchChange.bootstrapSwitch': 'switchStatus',
        'click .delete-sftp-share': 'deleteSFTP'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.sftp_sftp;
        this.module_name = 'sftp';
        this.collection = new SFTPCollection();
        this.dependencies.push(this.collection);
        this.serviceName = 'sftp';
        this.service = new Service({
            name: this.serviceName
        });
        this.dependencies.push(this.service);
        this.shares = new ShareCollection();
        this.dependencies.push(this.shares);
        this.updateFreq = 5000;
        this.initHandlebarHelpers();
    },

    render: function() {
        var _this = this;
        this.fetch(this.renderSFTP, this);
        return this;
    },

    renderSFTP: function() {
        this.freeShares = this.shares.reject(function(share) {
            var s = this.collection.find(function(sftpShare) {
                return (sftpShare.get('share') == share.get('name'));
            });
            return !_.isUndefined(s);
        }, this);

        //check if there are shares in the system
        var sharesExistBool = false;
        if (this.shares.length > 0) {
            sharesExistBool = true;
        }
        //check if there are free shares not associated with afp.
        var freeSharesBool = false;
        if (this.freeShares) {
            freeSharesBool = true;
        }
        //set a variable to true if both conditions are satisfied
        var verifySharesBool = false;
        if (freeSharesBool && sharesExistBool) {
            verifySharesBool = true;
        }

        $(this.el).html(this.template({
            sftpShare: this.collection.toJSON(),
            collection: this.collection,
            collectionNotEmpty: !this.collection.isEmpty(),
            freeShares: this.freeShares,
            sharesNotEmpty: verifySharesBool,
            service: this.service
        }));

        this.renderDataTables();

        //initalize Bootstrap Switch
        this.$('[type=\'checkbox\']').bootstrapSwitch();
        this.$('input[name="sftp-service-checkbox"]').bootstrapSwitch('state', this.service.get('status'), true);
        this.$('[type=\'checkbox\']').bootstrapSwitch('onColor', 'success'); //left side text color
        this.$('[type=\'checkbox\']').bootstrapSwitch('offColor', 'danger'); //right side text color

        // Display NFS Export Service Warning
        if (!this.service.get('status')) {
            this.$('#sftp-warning').show();
        } else {
            this.$('#sftp-warning').hide();
        }

    },

    switchStatus: function(event, state) {
        if (state) {
            this.startService();
        } else {
            this.stopService();
        }
    },

    deleteSFTP: function(event) {
        var _this = this;
        if (event) event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        if (confirm('Delete sftp entry ... Are you sure? ')) {
            disableButton(button);
            var id = $(event.currentTarget).data('id');

            $.ajax({
                url: '/api/sftp/' + id,
                type: 'DELETE',
                dataType: 'json',
                contentType: 'application/json',
                success: function() {
                    _this.render();
                },
                error: function(xhr, status, error) {
                    enableButton(button);
                }
            });

        }
    },
    startService: function() {
        var _this = this;
        this.setStatusLoading(this.serviceName, true);
        $.ajax({
            url: '/api/sm/services/sftp/start',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(_this.serviceName, false);
                _this.$('#sftp-warning').hide();
            },
            error: function(xhr, status, error) {
                _this.setStatusError(_this.serviceName, xhr);
                _this.$('#sftp-warning').show();
            }
        });
    },

    stopService: function() {
        var _this = this;
        this.setStatusLoading(this.serviceName, true);
        $.ajax({
            url: '/api/sm/services/sftp/stop',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(_this.serviceName, false);
                _this.$('#sftp-warning').show();
            },
            error: function(xhr, status, error) {
                _this.setStatusError(_this.serviceName, xhr);
                _this.$('#sftp-warning').hide();
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

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('displaySftpPermission', function(sftpEditable) {
            var html = '';
            if (sftpEditable == 'ro') {
                html += 'yes';
            } else {
                html += 'no';
            }
            return new Handlebars.SafeString(html);
        });
    }

});