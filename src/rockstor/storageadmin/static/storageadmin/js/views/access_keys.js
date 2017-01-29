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

AccessKeysView = RockstorLayoutView.extend({
    events: {
        'click a[data-action=delete]': 'deleteAccessKey'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.access_keys_access_keys;
        this.collection = new AccessKeyCollection();
        this.dependencies.push(this.collection);
        this.collection.on('reset', this.renderAccessKeys, this);
    },

    render: function() {
        this.fetch(this.renderAccessKeys, this);
        return this;
    },

    renderAccessKeys: function() {
        $(this.el).html(this.template({
            accessKeys: this.collection.toJSON(),
            collection: this.collection,
            collectionNotEmpty: !this.collection.isEmpty(),
        }));

        this.renderDataTables();
    },

    deleteAccessKey: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        var name = button.attr('data-name');
        var id = button.attr('data-id');
        if (confirm('Delete access key:  ' + name + ' ...Are you sure?')) {
            disableButton(button);
            $.ajax({
                url: '/api/oauth_app/' + id,
                type: 'DELETE',
                dataType: 'json',
                success: function() {
                    _this.collection.fetch({
                        reset: true
                    });
                    enableButton(button);
                },
                error: function(xhr, status, error) {
                    enableButton(button);
                }
            });
        }

    },
});