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

/*
 * View for the homepage/dashboard
 */

var HomeLayoutView = RockstorLayoutView.extend({
    events: {},

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        // set template
        this.template = window.JST.home_home_template;
        // create models and collections
        this.appliances = new ApplianceCollection();
        this.dashboardconfig = new DashboardConfig();
        // add dependencies
        this.dependencies.push(this.appliances);
        this.dependencies.push(this.dashboardconfig);

        this.selectedWidgetNames = [];
        this.widgetViews = []; // widgets add themselves here so that their cleanup routines can be called from this view's cleanup
        this.on('widgetClicked', this.widgetClicked, this);
    },

    render: function() {

        this.fetch(this.renderSubViews, this);
        return this;

    },

    renderSubViews: function() {

        // render template
        $(this.el).empty();
        $(this.el).append(this.template());

        var _this = this;
        $.ajax({
            url: '/setup_user',
            type: 'GET',
            dataType: 'json',
            success: function(data, status, xhr) {
                if (data.new_setup) {
                    $.ajax({
                        url: '/setup_user',
                        type: 'PUT',
                        dataType: 'json',
                        success: function(data, status, xhr) {
                            $('#update-version-modal').modal({
                                keyboard: false,
                                show: false,
                                backdrop: 'static'
                            });
                            $('#update-version-modal').modal('show');

                        },
                        error: function(xhr, status, error) {

                        }
                    });
                } else {
                    var subscriptions = new UpdateSubscriptionCollection();
                    subscriptions.fetch({
                        success: function(collection, response, options) {
                            if (collection.length == 0) {
                                $('#update-channel-modal').modal({
                                    keyboard: false,
                                    show: false,
                                    backdrop: 'static'
                                });
                                $('#update-channel-modal').modal('show');
                            }

                        }
                    });
                }
            },
            error: function(xhr, status, error) {

            }
        });
        $('#update-version-modal #updateYes').click(function(event) {
            $('#update-version-modal').modal('hide');
            app_router.navigate('version', {
                trigger: true
            });

        });
        $('#update-channel-modal #activate').click(function(event) {
            $('#update-channel-modal').modal('hide');
            app_router.navigate('version', {
                trigger: true
            });
        });
        this.widgetsContainer = this.$('.widgets-container');
        // render dashboard widgets
        this.renderWidgets();

        this.dashboardConfigView = new DashboardConfigView({
            parentView: this,
            dashboardconfig: this.dashboardconfig
        });
        $('#dashboard-config-ph').append(this.dashboardConfigView.render().el);
    },

    renderWidgets: function() {
        var _this = this;
        this.widgetsContainer.empty();

        var selectedWidgets = this.dashboardconfig.getConfig();
        this.widgetViews.length = 0;
        // Add widgets to ul (widgetsContainer);
        _.each(selectedWidgets, function(widget, index, list) {
            _this.addWidget(widget, _this.widgetsContainer, _this.widgetViews);
        });
        // call shapeshift to do layout
        this.widgetsContainer.shapeshift({
            align: 'left',
            minColumns: 10,
            gutterX: 5,
            gutterY: 5,
            paddingX: 5,
            paddingY: 5,
            handle: 'div.widget-header'
        });

        // set handler for drop event, when a widget is moved around and
        // the drop completes.
        this.widgetsContainer.on('ss-drop-complete', function(e, selected) {
            _this.saveWidgetConfiguration();
        });
    },

    addWidgetByName: function(widgetName) {
        var widget = RockStorWidgets.findByName(widgetName);
        this.addWidget(widget, this.widgetsContainer, this.widgetViews);
    },

    addWidget: function(widget, container, widgetViews) {
        var div = null;
        var widgetDef = RockStorWidgets.findByName(widget.name);
        var viewName = widgetDef.view;
        if (!_.isUndefined(window[viewName] && !_.isNull(window[viewName]))) {
            // Create widget view
            var view = new window[viewName]({
                displayName: widgetDef.displayName,
                name: widget.name,
                cleanupArray: widgetViews,
                parentView: this,
                maximized: widget.maximized
            });

            // create shapeshift div for widget and render
            div = $('<div>');
            div.attr('class', 'widget-ph');
            if (widget.maximized) {
                div.attr('data-ss-colspan', widgetDef.maxCols);
                div.attr('data-ss-rowspan', widgetDef.maxRows);
            } else {
                div.attr('data-ss-colspan', widgetDef.cols);
                div.attr('data-ss-rowspan', widgetDef.rows);
            }
            div.attr('data-widget-name', widget.name);
            container.append(div);
            var position_div = $('<div class="position"></div>');
            div.append(position_div);
            position_div.append(view.render().el);

            // Add widget view to widget list
            widgetViews.push(view);
        }
    },

    findWidgetView: function(name) {
        var i = 0,
            found = false;
        for (i = 0; i < this.widgetViews.length; i++) {
            if (this.widgetViews[i].name == name) {
                return [this.widgetViews[i], i];
            }
        }
        return [null, null];
    },

    removeWidget: function(name, view) {
        // view cleanup and remove
        view.cleanup();
        view.remove();

        // remove view shapeshift div
        var ssDiv = $(this.el).find('div[data-widget-name="' + name + '"]');
        ssDiv.remove();

        // remove view from widget list
        this.widgetViews = _.reject(this.widgetViews, function(view) {
            return view.name == name;
        });

        // trigger ss rearrange
        this.widgetsContainer.trigger('ss-rearrange');

        // uncheck widget in widget selection list
        this.dashboardConfigView.setCheckbox(name, false);

        // save new widget configuration
        this.saveWidgetConfiguration();
    },

    saveWidgetConfiguration: function() {
        var _this = this;
        var divs = this.widgetsContainer.children('div.widget-ph');
        var tmp = [];
        divs.each(function(index) {
            var div = $(this);
            var name = div.data('widget-name');
            var widget = _.find(_this.widgetViews, function(w) {
                return w.name == name;
            });
            tmp.push({
                name: name,
                position: index,
                maximized: widget.maximized
            });
        });
        this.dashboardconfig.set({
            widgets: JSON.stringify(tmp)
        });
        this.dashboardconfig.save(null, {
            success: function(model, response, options) {},
            error: function(model, xhr, options) {
                logger.debug('error while saving dashboardconfig');
                var msg = xhr.responseText;
                try {
                    msg = JSON.parse(msg).detail;
                } catch (err) {
                    console.log(err);
                }
                logger.debug(msg);
            }
        });
    },

    widgetClicked: function(name, selected) {
        if (selected) {
            this.addWidgetByName(name);
            this.widgetsContainer.trigger('ss-destroy');
            this.widgetsContainer.shapeshift({
                align: 'left',
                minColumns: 10
            });
            this.saveWidgetConfiguration();
        } else {
            var tmp = this.findWidgetView(name);
            var view = tmp[0];
            if (view) {
                this.removeWidget(name, view);
            }
        }
    },

    cleanup: function() {
        _.each(this.widgetViews, function(widget) {
            if (_.isFunction(widget.cleanup)) {
                widget.cleanup();
            }
        });
        this.dashboardConfigView.cleanup();
    },

});