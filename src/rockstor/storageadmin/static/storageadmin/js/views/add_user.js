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

AddUserView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel'
    },

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        // set template
        this.template = window.JST.users_add_user;
        this.username = this.options.username;
        if (!_.isUndefined(this.username)) {
            this.user = new User({
                username: this.username
            });
            this.dependencies.push(this.user);
        } else {
            this.user = new User();
        }
        this.groups = new GroupCollection();
        this.groups.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.groups);
    },

    render: function() {
        this.fetch(this.renderUserForm, this);
        return this;
    },

    renderUserForm: function() {
        var _this = this;
        $(this.el).html(this.template({
            username: this.username,
            user: this.user.toJSON(),
            groups: this.groups.toJSON(),
            shells: ['/bin/bash', '/sbin/nologin']

        }));

        this.$('#user-create-form :input').tooltip({
            placement: 'right'
        });
        this.$('#group').select2();

        this.validator = this.$('#user-create-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                username: 'required',
                password: {
                    required: {
                        depends: function(element) {
                            return _this.username == null || _this.username == undefined;
                        }
                    }
                },
                password_confirmation: {
                    required: {
                        depends: function(element) {
                            return _this.username == null || _this.username == undefined;
                        }
                    },
                    equalTo: '#password'
                }
            },
            messages: {
                password_confirmation: {
                    equalTo: 'The passwords do not match'
                }
            },

            submitHandler: function() {
                var username = _this.$('#username').val();
                var password = _this.$('#password').val();
                var admin = _this.$('#admin').prop('checked');
                var shell = _this.$('#shell').val();

                var public_key = _this.$('#public_key').val();
                if (_.isEmpty(public_key)) {
                    public_key = null;
                }
                var uid = _this.$('#uid').val();
                if (_.isEmpty(uid)) {
                    uid = null;
                }
                var group = _this.$('#group').val();
                if (group == 'Autogenerate') {
                    group = null;
                }
                var email = _this.$('#email').val();
                if (_.isEmpty(email)) {
                    email = null;
                }
                if (_this.username != null && _this.username != undefined) {
                    if (!_.isEmpty(password)) {
                        _this.user.set({
                            password: password
                        });
                    } else {
                        _this.user.unset('password');
                    }
                    if (!_.isEmpty(public_key)) {
                        _this.user.set({
                            public_key: public_key
                        });
                    } else {
                        _this.user.unset('public_key');
                    }

                    _this.user.set({
                        admin: admin
                    });
                    _this.user.set({
                        group: group
                    });
                    _this.user.set({
                        shell: shell
                    });
                    _this.user.set({
                        email: email
                    });
                    _this.user.save(null, {
                        success: function(model, response, options) {
                            app_router.navigate('users', {
                                trigger: true
                            });
                        },
                        error: function(model, xhr, options) {}
                    });
                } else {
                    // create a dummy user model class that does not have idAttribute
                    // = username, so backbone will treat is as a new object,
                    // ie isNew will return true
                    var tmpUserModel = Backbone.Model.extend({
                        urlRoot: '/api/users'
                    });
                    var user = new tmpUserModel();
                    user.save({
                        username: username,
                        password: password,
                        admin: admin,
                        group: group,
                        shell: shell,
                        uid: uid,
                        public_key: public_key,
                        email: email
                    }, {
                        success: function(model, response, options) {
                            _this.$('#user-create-form :input').tooltip('hide');
                            app_router.navigate('users', {
                                trigger: true
                            });
                        },
                        error: function(model, xhr, options) {
                            _this.$('#user-create-form :input').tooltip('hide');
                        }
                    });
                }
                return false;
            }
        });
        return this;
    },

    cancel: function(event) {
        event.preventDefault();
        app_router.navigate('users', {
            trigger: true
        });
    }

});