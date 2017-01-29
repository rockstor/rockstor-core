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

AddGroupView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel'
    },

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        // set template
        this.template = window.JST.users_add_group;
        this.groupname = this.options.groupname;
        this.group = new Group({
            groupname: this.groupname
        });
        this.dependencies.push(this.group);
    },

    render: function() {
        this.fetch(this.renderExportForm, this);
        return this;
    },

    renderExportForm: function() { //#start renderExportForm
        var _this = this;
        $(this.el).html(this.template({
            groupname: this.groupname,
            group: this.group.toJSON()

        }));

        this.$('#group-create-form :input').tooltip({
            placement: 'right'
        });

        this.validator = this.$('#group-create-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                groupname: 'required',
                gid: {
                    number: true

                }
            },

            submitHandler: function() {
                var groupname = _this.$('#groupname').val();
                var gid = _this.$('#gid').val() || null;
                var group;
                if (_this.groupname != null && _this.group != null) {
                    group = new Group({
                        groupname: _this.groupname
                    });
                    group.save(null, {
                        success: function(model, response, options) {
                            app_router.navigate('groups', {
                                trigger: true
                            });
                        },
                        error: function(model, xhr, options) {}
                    });
                } else {
                    var tmpGroupModel = Backbone.Model.extend({
                        urlRoot: '/api/groups'
                    });
                    group = new tmpGroupModel();
                    group.save({
                        groupname: groupname,
                        gid: gid
                    }, {
                        success: function(model, response, options) {
                            _this.$('#group-create-form :input').tooltip('hide');
                            app_router.navigate('groups', {
                                trigger: true
                            });
                        },
                        error: function(model, xhr, options) {
                            _this.$('#group-create-form :input').tooltip('hide');
                        }
                    });
                }
                return false;
            },
        });
        return this;
    },

    cancel: function() {
        app_router.navigate('groups', {
            trigger: true
        });
    }

});