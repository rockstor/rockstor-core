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

NFSExportsView = RockstorLayoutView.extend({
    events: {
        'click .delete-nfs-export': 'deleteNfsExport',
        'switchChange.bootstrapSwitch': 'switchStatus',
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.nfs_nfs_exports;
        this.module_name = 'nfs_exports';
        this.collection = new NFSExportGroupCollection();
        this.dependencies.push(this.collection);
        this.appliances = new ApplianceCollection();
        this.dependencies.push(this.appliances);
        this.serviceName = 'nfs';
        this.service = new Service({
            name: this.serviceName
        });
        this.dependencies.push(this.service);
        this.updateFreq = 5000;
        this.collection.on('reset', this.renderNFSExportGroups, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        var _this = this;
        this.fetch(this.renderNFSExportGroups, this);
        return this;
    },

    renderNFSExportGroups: function() {
        var currentAppliance = this.appliances.find(function(appliance) {
            return appliance.get('current_appliance') == true;
        });
        $(this.el).html(this.template({
            collection: this.collection,
            nfsCollection: this.collection.toJSON(),
            collectionNotEmpty: !this.collection.isEmpty(),
            service: this.service,
            currentAppliance: currentAppliance,
            currentApplianceIp: currentAppliance.get('ip')
        }));

        this.renderDataTables();

        //initalize Bootstrap Switch
        this.$('[type=\'checkbox\']').bootstrapSwitch();
        this.$('input[name="nfs-export-checkbox"]').bootstrapSwitch('state', this.service.get('status'), true);
        this.$('[type=\'checkbox\']').bootstrapSwitch('onColor', 'success'); //left side text color
        this.$('[type=\'checkbox\']').bootstrapSwitch('offColor', 'danger'); //right side text color

        // Display NFS Export Service Warning
        if (!this.service.get('status')) {
            this.$('#nfs-warning').show();
        } else {
            this.$('#nfs-warning').hide();
        }
    },

    switchStatus: function(event, state) {
        if (state) {
            this.startService();
        } else {
            this.stopService();
        }
    },

    deleteNfsExport: function(event) {
        var _this = this;
        if (event) event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        if (confirm('Delete nfs-export... Are you sure? ')) {
            disableButton(button);
            var id = $(event.currentTarget).data('id');
            $.ajax({
                url: '/api/nfs-exports/' + id,
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
            url: '/api/sm/services/nfs/start',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(_this.serviceName, false);
                _this.$('#nfs-warning').hide();
            },
            error: function(xhr, status, error) {
                _this.setStatusError(_this.serviceName, xhr);
                _this.$('#nfs-warning').show();
            }
        });
    },

    stopService: function() {
        var _this = this;
        this.setStatusLoading(this.serviceName, true);
        $.ajax({
            url: '/api/sm/services/nfs/stop',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.setStatusLoading(_this.serviceName, false);
                _this.$('#nfs-warning').show();
            },
            error: function(xhr, status, error) {
                _this.setStatusError(_this.serviceName, xhr);
                _this.$('#nfs-warning').hide();
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
        Handlebars.registerHelper('showNfsShares', function(index, nfsExports) {
            if (index < (nfsExports.length - 1)) {
                return ',';
            }
        });

        Handlebars.registerHelper('showWritableOption', function(editable) {
            return editable == 'rw' ? 'no' : 'yes';
        });
    }

});