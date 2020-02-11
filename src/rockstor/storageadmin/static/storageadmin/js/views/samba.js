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

SambaView = RockstorLayoutView.extend({
    events: {
        'switchChange.bootstrapSwitch': 'switchStatus',
        'click .delete-samba-export': 'deleteSambaExport'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.samba_samba;
        this.module_name = 'samba';
        this.collection = new SambaCollection();
        this.dependencies.push(this.collection);
        this.serviceName = 'smb';
        this.service = new Service({
            name: this.serviceName
        });
        this.dependencies.push(this.service);
        this.shares = new ShareCollection();
        this.dependencies.push(this.shares);
        this.updateFreq = 5000;
        this.collection.on('reset', this.renderSamba, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        var _this = this;
        this.fetch(this.renderSamba, this);
        return this;
    },

    renderSamba: function() {
        this.freeShares = this.shares.reject(function(share) {
            var s = this.collection.find(function(sambaShare) {
                return (sambaShare.get('share') == share.get('name'));
            });
            return !_.isUndefined(s);
        }, this);

        //check if there are shares in the system
        var sharesExistBool = false;
        if (this.shares.length > 0) {
            sharesExistBool = true;
        }
        //check if there are free shares not associated with samba.
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
            samba: this.collection.toJSON(),
            collection: this.collection,
            collectionNotEmpty: !this.collection.isEmpty(),
            service: this.service,
            freeShares: this.freeShares,
            sharesNotEmpty: verifySharesBool
        }));

        this.renderDataTables();

        //initalize Bootstrap Switch
        this.$('[type=\'checkbox\']').bootstrapSwitch();
        this.$('input[name="samba-export-checkbox"]').bootstrapSwitch('state', this.service.get('status'), true);
        this.$('[type=\'checkbox\']').bootstrapSwitch('onColor', 'success'); //left side text color
        this.$('[type=\'checkbox\']').bootstrapSwitch('offColor', 'danger'); //right side text color

        // Display NFS Export Service Warning
        if (!this.service.get('status')) {
            this.$('#samba-warning').show();
        } else {
            this.$('#samba-warning').hide();
        }
    },

    switchStatus: function(event, state) {
        if (!this.service.get('config')) {
            app_router.navigate('services/smb/edit', {
                trigger: true,
            });
        } else {
            if (state) {
                this.startService();
            } else {
                this.stopService();
            }
        }
    },

    deleteSambaExport: function(event) {
        var _this = this;
        if (event) event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        if (confirm('Delete samba export... Are you sure? ')) {
            disableButton(button);
            var id = $(event.currentTarget).data('id');
            $.ajax({
                url: '/api/samba/' + id,
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
            url: '/api/sm/services/smb/start',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(_this.serviceName, false);
                _this.$('#samba-warning').hide();
            },
            error: function(xhr, status, error) {
                _this.setStatusError(_this.serviceName, xhr);
                _this.$('#samba-warning').show();
            }
        });
    },

    stopService: function() {
        var _this = this;
        this.setStatusLoading(this.serviceName, true);
        $.ajax({
            url: '/api/sm/services/smb/stop',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(_this.serviceName, false);
                _this.$('#samba-warning').show();
            },
            error: function(xhr, status, error) {
                _this.setStatusError(_this.serviceName, xhr);
                _this.$('#samba-warning').hide();
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
        Handlebars.registerHelper('getAdminUsers', function(adminUsers) {
            var html = '';
            var userNames = _.reduce(adminUsers, function(s, user, i, list) {
                if (i < (list.length - 1)) {
                    return s + user.username + ',';
                } else {
                    return s + user.username;
                }
            }, '');
            if (userNames.length != 0) {
                html += userNames;
            } else {
                html += '&nbsp;--';
            }
            return new Handlebars.SafeString(html);
        });
    }
});
