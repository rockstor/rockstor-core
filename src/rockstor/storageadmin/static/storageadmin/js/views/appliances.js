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

AppliancesView = RockstorLayoutView.extend({

    events: {
        'click .delete-appliance': 'deleteAppliance'
    },

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        this.collection = new ApplianceCollection();
        this.template = window.JST.appliances_appliances;
        this.new_appliance_template = window.JST.common_new_appliance;
        this.dependencies.push(this.collection);
        this.collection.on('reset', this.renderApplianceList, this);
    },

    render: function() {
        this.fetch(this.renderApplianceList, this);
        return this;
    },

    renderApplianceList: function() {
        $(this.el).html(this.template({
            collection: this.collection,
            appliances: this.collection.toJSON()
        }));
        this.renderDataTables();

        /* Use X-editable js library for editing the Hostname inline. */

        $.fn.editable.defaults.mode = 'inline';
        var dataAppId = $('#hostname').data('id');
        $('#hostname').editable({
            type: 'text',
            title: 'Edit Hostname',
            //handle an empty input
            validate: function(newHostname) {
                if ($.trim(newHostname) == '') {
                    return 'This field is required';
                }
            },
            success: function(response, newHostname) {
                var data = {
                    'hostname': newHostname
                };
                $.ajax({
                    url: '/api/appliances/' + dataAppId,
                    type: 'PUT',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    success: function() {
                        setApplianceName();
                    },
                });
            }
        });
    },

    newAppliance: function() {
        this.$('#new-appliance-container').html(this.new_appliance_template());
    },

    deleteAppliance: function(event) {
        var _this = this;
        event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        var appliance = new Appliance();
        appliance.set({
            ip: button.attr('id'),
            id: button.attr('data-id')
        });
        if (confirm('Delete appliance:  ' + appliance.get('ip') + ' ...Are you sure?')) {
            disableButton(button);
            appliance.destroy({
                success: function(model, response, options) {
                    enableButton(button);
                    _this.collection.fetch();
                },
                error: function(model, xhr, options) {
                    enableButton(button);
                    var msg = xhr.responseText;
                }
            });
        }
    },
});