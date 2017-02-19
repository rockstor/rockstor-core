/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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

InitView = RockstorLayoutView.extend({

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
    },

    scanNetwork: function() {
        var _this = this;
        $.ajax({
            url: '/api/network/refresh',
            type: 'POST',
            dataType: 'json',
            success: function(data, status, xhr) {
                _this.networkInterfaces.fetch();
            }
        });
    },

    saveAppliance: function() {
        var _this = this;
        // create current appliance if not created already
        if (this.appliances.length > 0) {
            var current_appliance = this.appliances.find(function(appliance) {
                return appliance.get('current_appliance') == true;
            });
        }
        if (_.isUndefined(current_appliance)) {
            var new_appliance = new Appliance();
            new_appliance.save({
                hostname: RockStorGlobals.hostname,
                ip: RockStorGlobals.ip,
                current_appliance: true
            }, {
                success: function(model, response, options) {
                    setup_done = true;
                    _this.scanDisks();
                },
                error: function(model, xhr, options) {
                    var msg = xhr.responseText;
                    try {
                        msg = JSON.parse(msg).detail;
                    } catch (err) {
                        console.log(err);
                    }
                }
            });
        } else {
            app_router.navigate('home', {
                trigger: true
            });
        }
    },

    scanDisks: function() {
        var _this = this;
        $.ajax({
            url: '/api/disks/scan',
            type: 'POST'
        }).done(function() {
            _this.goToRoot();
        });
    },

    goToRoot: function() {
        window.location.replace('/');

    },

});


LoginView = InitView.extend({
    tagName: 'div',

    events: {
        'click #sign_in': 'login',
    },

    initialize: function() {
        this.login_template = window.JST.home_login_template;
        this.user_create_template = window.JST.home_user_create_template;
        this.networkInterfaces = new NetworkConnectionCollection();
        this.networkInterfaces.pageSize = RockStorGlobals.maxPageSize;
        this.networkInterfaces.on('reset', this.saveAppliance, this);
        this.appliances = new ApplianceCollection();

    },

    render: function() {
        var _this = this;
        if (!RockStorGlobals.setup_user) {
            $(this.el).append(this.user_create_template());
            this.validator = this.$('#user-create-form').validate({
                onfocusout: false,
                onkeyup: false,
                rules: {
                    username: 'required',
                    password: 'required',
                    hostname: 'required',
                    password_confirmation: {
                        required: 'true',
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
                    RockStorGlobals.hostname = _this.$('#hostname').val();

                    var setupUserModel = Backbone.Model.extend({
                        urlRoot: '/setup_user',
                    });
                    var user = new setupUserModel();
                    user.save({
                        username: username,
                        password: password,
                        is_active: true
                    }, {
                        success: function(model, response, options) {
                            _this.makeLoginRequest(username, password);
                        },
                        error: function(model, xhr, options) {}
                    });

                    return false;
                }
            });
        }
        return this;
    },

    login: function(event) {
        if (!_.isUndefined(event) && !_.isNull(event)) {
            event.preventDefault();
        }
        this.makeLoginRequest(this.$('#username').val(), this.$('#password').val());
    },

    makeLoginRequest: function(username, password) {
        var _this = this;
        $.ajax({
            url: '/api/login',
            type: 'POST',
            dataType: 'json',
            data: {
                username: username,
                password: password
            },
            success: function(data, status, xhr) {
                _this.scanNetwork();

            },
            error: function(xhr, status, error) {
                _this.$('.messages').html('<label class="error">Login incorrect!</label>');
            }
        });
    },

});


SetupView = InitView.extend({
    tagName: 'div',

    events: {
        'click #next-page': 'nextPage',
        'click #prev-page': 'prevPage'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.setup_setup;
        this.pages = [null, SetupDisksView, SetupSystemView];
        this.sidebars = [null, 'disks'];
        this.current_page = 1;
        this.current_view = null;
        this.appliances = new ApplianceCollection();
        this.appliances.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.appliances);

        //next three lines are supposed to refresh connection state?
        this.networkInterfaces = new NetworkConnectionCollection();
        this.networkInterfaces.pageSize = RockStorGlobals.maxPageSize;
        this.networkInterfaces.on('reset', this.saveAppliance, this);

    },

    render: function() {
        $(this.el).html(this.template());
        var _this = this;
        this.fetch(this.renderCurrentPage, this);
        return this;
    },

    renderCurrentPage: function() {
        opts = {
            appliances: this.appliances
        };
        this.renderSidebar('setup', this.sidebars[this.current_page]);
        this.current_view = new this.pages[this.current_page](opts);
        this.$('#current-page-inner').html(this.current_view.render().el);

    },

    nextPage: function() {
        if (this.current_page < this.pages.length - 1) {
            this.current_page = this.current_page + 1;
            this.renderCurrentPage();
            this.modifyButtonText();
            this.setCurrentStepTitle(this.current_page, this.current_page - 1);
        } else {
            this.save();
        }
    },

    prevPage: function() {
        if (this.current_page > 1) {
            this.current_page = this.current_page - 1;
            this.renderCurrentPage();
            this.modifyButtonText();
            this.setCurrentStepTitle(this.current_page, this.current_page + 1);
        }
    },

    modifyButtonText: function() {
        if (this.lastPage()) {
            this.$('#next-page').html('Finish');
        } else {
            this.$('#next-page').html('Next');
        }
    },

    lastPage: function() {
        return (this.current_page == (this.pages.length - 1));
    },

    save: function() {
        // hostname is the last page, so check if the form is filled
        this.current_view.$('#set-hostname-form').submit();
        if (!_.isUndefined(RockStorGlobals.hostname) &&
            !_.isNull(RockStorGlobals.hostname)) {
            var button = this.$('#next-page');
            if (buttonDisabled(button)) return false;
            disableButton(button);
            this.scanNetwork();
        }
    },

    setCurrentStepTitle: function(new_step, old_step) {
        old_step_str = old_step + '';
        old_sel_str = '#setup-titles li[data-step="' + old_step_str + '"]';
        this.$(old_sel_str).removeClass('current-step');
        new_step_str = new_step + '';
        new_sel_str = '#setup-titles li[data-step="' + new_step_str + '"]';
        this.$(new_sel_str).addClass('current-step');
    },

    renderSidebar: function(name, selected) {
        var sidenavTemplate = window.JST['common_sidenav_' + name];
        $('#sidebar-inner').html(sidenavTemplate({
            selected: selected
        }));
    }


});