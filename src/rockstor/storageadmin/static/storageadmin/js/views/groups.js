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

GroupsView = RockstorLayoutView.extend({
    events: {
        'click .delete-group': 'deleteGroup',
        'click .edit-group': 'editGroup'
    },

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.users_groups;
        this.collection = new GroupCollection();
        this.dependencies.push(this.collection);
        this.collection.on('reset', this.renderGroups, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        this.collection.fetch();
        return this;
    },

    renderGroups: function() {
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }

        this.rockstorGroups = this.collection.filter(function(grp) {
            return (grp.get('admin'));
        });
        this.otherSystemGroups = this.collection.filter(function(grp) {
            return (!grp.get('admin'));
        });

        $(this.el).html(this.template({
            collection: this.collection,
            rockstorGroups: this.rockstorGroups,
            otherSystemGroups: this.otherSystemGroups,
        }));
        this.$('[rel=tooltip]').tooltip({
            placement: 'bottom'
        });

        this.renderDataTables();
    },

    deleteGroup: function(event) {
        event.preventDefault();
        var _this = this;
        var groupname = $(event.currentTarget).attr('data-groupname');
        if (confirm('Delete group:  ' + groupname + '. Are you sure?')) {
            $.ajax({
                url: '/api/groups/' + groupname,
                type: 'DELETE',
                dataType: 'json',
                success: function() {
                    _this.collection.fetch();
                },
                error: function(xhr, status, error) {}
            });
        } else {
            return false;
        }
    },

    editGroup: function(event) {
        if (event) event.preventDefault();
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }
        var groupname = $(event.currentTarget).attr('data-groupname');
        app_router.navigate('groups/' + groupname + '/edit', {
            trigger: true
        });
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_groups_table', function(adminBool) {
            var html = '';
            var filteredCollection = null;
            if (adminBool) {
                filteredCollection = this.rockstorGroups;
            } else {
                filteredCollection = this.otherSystemGroups;
            }

            if (filteredCollection == null) {
                html += 'No groups exist';
            } else {
                for (var i = 0; i < filteredCollection.length; i++) {
                    html += '<tr>';
                    html += '<td><i class="fa fa-group"></i> ' + filteredCollection[i].get('groupname') + '</td>';
                    html += '<td>' + filteredCollection[i].get('gid') + '</td>';
                    html += '<td>';
                    html += '<a href="#" class="delete-group" data-groupname="' + filteredCollection[i].get('groupname') + '" rel="tooltip" title="Delete group"><i class="glyphicon glyphicon-trash"></i></a>';
                    html += '</td>';
                    html += '</tr>';
                }

            }
            return new Handlebars.SafeString(html);
        });
    }

});