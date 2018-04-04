/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
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

PaginationMixin = {
    events: {
        'click .go-to-page': 'goToPage',
        'click .prev-page': 'prevPage',
        'click .next-page': 'nextPage'
    },
    goToPage: function(event) {
        if (event) event.preventDefault();
        this.collection.goToPage(parseInt($(event.currentTarget).attr('data-page')));
    },
    prevPage: function(event) {
        if (event) event.preventDefault();
        this.collection.prevPage();
    },
    nextPage: function(event) {
        if (event) event.preventDefault();
        this.collection.nextPage();
    }
};

RockstorLayoutView = Backbone.View.extend({
    tagName: 'div',
    className: 'layout',

    initialize: function() {
        this.subviews = {};
        this.dependencies = [];
    },

    fetch: function(callback, context) {
        var allDependencies = [];
        _.each(this.dependencies, function(dep) {
            allDependencies.push(dep.fetch({
                silent: true
            }));
        });
        $.when.apply($, allDependencies).done(function() {
            if (callback) callback.apply(context);
        });
    },

    renderDataTables: function(customs) {
        var DataTable_obj = {
            'iDisplayLength': 15,
            'aLengthMenu': [
                [15, 30, 45, -1],
                [15, 30, 45, 'All']
            ],            
        };
        if (typeof customs == 'object'){
            _.extend(DataTable_obj, customs);
        }
        $('table.data-table').DataTable(DataTable_obj);
    },

});


// RockstorModuleView

RockstorModuleView = Backbone.View.extend({

    tagName: 'div',
    className: 'module',
    requestCount: 0,

    initialize: function() {
        this.subviews = {};
        this.dependencies = [];
    },

    fetch: function(callback, context) {
        var allDependencies = [];
        _.each(this.dependencies, function(dep) {
            allDependencies.push(dep.fetch({
                silent: true
            }));
        });
        $.when.apply($, allDependencies).done(function() {
            if (callback) callback.apply(context);
        });
    },

    render: function() {
        $(this.el).html(this.template({
            module_name: this.module_name,
            model: this.model,
            collection: this.collection
        }));

        return this;
    }
});

RockStorWidgetView = Backbone.View.extend({
    tagName: 'div',
    className: 'widget',

    events: {
        'click .configure-widget': 'configure',
        'click .resize-widget': 'resize',
        'click .close-widget': 'close',
        'click .download-widget': 'download'
    },

    initialize: function() {
        this.maximized = this.options.maximized;
        this.name = this.options.name;
        this.displayName = this.options.displayName;
        this.parentView = this.options.parentView;
        this.dependencies = [];
    },

    render: function() {
        $(this.el).attr('id', this.name + '_widget');
    },

    configure: function(event) {
        if (!_.isUndefined(event) && !_.isNull(event)) {
            event.preventDefault();
        }
    },

    resize: function(event) {
        if (!_.isUndefined(event) && !_.isNull(event)) {
            event.preventDefault();
        }
        var c = $(this.el).closest('div.widgets-container');
        var w = $(this.el).closest('div.widget-ph'); // current widget
        var widgetDef = RockStorWidgets.findByName(this.name);
        if (!this.maximized) {
            // Maximizing
            // Remember current position
            this.originalPosition = w.index();
            // remove list item from current position
            w.detach();
            // insert at first position in the list
            c.prepend(w);
            // resize to max
            w.attr('data-ss-colspan', widgetDef.maxCols);
            w.attr('data-ss-rowspan', widgetDef.maxRows);
            this.maximized = true;
        } else {
            // Restoring
            w.detach();
            w.attr('data-ss-colspan', widgetDef.cols);
            w.attr('data-ss-rowspan', widgetDef.rows);
            // find current list item at original index
            if (_.isNull(this.originalPosition) ||
                _.isUndefined(this.originalPosition)) {
                this.originalPosition = 0;
            }
            curr_w = c.find('div.widget-ph:eq(' + this.originalPosition + ')');
            // insert widget at original position
            if (curr_w.length > 0) {
                // if not last widget
                curr_w.before(w);
            } else {
                c.append(w);
            }
            this.maximized = false;
        }
        // trigger rearrange so shapeshift can do its job
        c.trigger('ss-rearrange');
        this.parentView.saveWidgetConfiguration();
    },

    close: function(event) {
        if (!_.isUndefined(event) && !_.isNull(event)) {
            event.preventDefault();
        }
        this.parentView.removeWidget(this.name, this);
    },

    download: function(event) {
        if (!_.isUndefined(event) && !_.isNull(event)) {
            event.preventDefault();
        }
    },

    cleanup: function() {
        logger.debug('In RockStorWidgetView close');
    },

    fetch: function(callback, context) {
        var allDependencies = [];
        _.each(this.dependencies, function(dep) {
            allDependencies.push(dep.fetch({
                silent: true
            }));
        });
        $.when.apply($, allDependencies).done(function() {
            if (callback) callback.apply(context);
        });
    }

});


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            var csrftoken = getCookie('csrftoken');
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        }
    }
});

function showApplianceList() {
    var applianceSelectPopup = $('#appliance-select-popup').modal({
        show: false
    });
    $('#appliance-select-content').html((new AppliancesView()).render().el);
    $('#appliance-select-popup').modal('show');

}


function showSuccessMessage(msg) {
    $('#messages').html(msg);
    $('#messages').css('visibility', 'visible');

}

function hideMessage() {
    $('#messages').html('&nbsp;');
    $('#messages').css('visibility', 'hidden');

}

/* Loading indicator */

$(document).ajaxStart(function() {
    $('#loading-indicator').css('visibility', 'visible');
});

$(document).ajaxStop(function() {
    $('#loading-indicator').css('visibility', 'hidden');
});


function showLoadingIndicator(elementName, context) {
    var _this = context;
    _this.$('#' + elementName).css('visibility', 'visible');
}

function hideLoadingIndicator(elementName, context) {
    var _this = context;
    _this.$('#' + elementName).css('visibility', 'hidden');
}

function disableButton(button) {
    button.data('executing', true);
    button.attr('disabled', true);
}

function enableButton(button) {
    button.data('executing', false);
    button.attr('disabled', false);
}

function buttonDisabled(button) {
    if (button.data('executing')) {
        return true;
    } else {
        return false;
    }
}


function refreshNavbar() {
    $.ajax({
        url: 'api/commands/current-user',
        type: 'POST',
        dataType: 'json',
        global: false, // dont show global loading indicator
        success: function(data, status, xhr) {
            var currentUser = data;
            $('#user-name').css({
                textTransform: 'none'
            });
            $('#user-name').html(currentUser + ' ');
        },
        error: function(xhr, status, error) {
            //  $('#user-name').html('Hello, <b> Admin! </b>');
        }
    });

    var navbarTemplate = window.JST.common_navbar;
    $('#navbar-links').html(navbarTemplate({
        logged_in: logged_in

    }));

    $('.dropdown-toggle').dropdown();
}

// Parses error message from ajax request
// Returns the value of the detail attribute as json
// or a string if it cannot be parsed as json
function parseXhrError(xhr) {
    var msg = xhr.responseText;
    try {
        msg = JSON.parse(msg).detail;
    } catch (err) {
        console.log(err);
    }
    if (typeof(msg) == 'string') {
        try {
            msg = JSON.parse(msg);
        } catch (err) {
            console.log(err);
        }
    }
    return msg;
}

function getXhrErrorJson(xhr) {
    var json = {};
    try {
        json = JSON.parse(xhr.responseText);
    } catch (err) {
        console.log(err);
    }
    return json;
}

function setApplianceName() {
    var appliances = new ApplianceCollection();
    appliances.fetch({
        success: function(request) {
            if (appliances.length > 0) {
                RockStorGlobals.currentAppliance =
                    appliances.find(function(appliance) {
                        return appliance.get('current_appliance') == true;
                    });
                $('#appliance-name').html('<i class="fa fa-desktop fa-inverse"></i>&nbsp;Hostname: ' + RockStorGlobals.currentAppliance.get('hostname') + '&nbsp;&nbsp;&nbsp;&nbsp;Mgmt IP: ' + RockStorGlobals.currentAppliance.get('ip'));
            }
        },
        error: function(request, response) {}

    });
}

function fetchDependencies(dependencies, callback, context) {
    if (dependencies.length == 0) {
        if (callback) callback.apply(context);
    }
    var requestCount = dependencies.length;
    _.each(dependencies, function(dependency) {
        dependency.fetch({
            success: function(request) {
                requestCount -= 1;
                if (requestCount == 0) {
                    if (callback) callback.apply(context);
                }
            },
            error: function(request, response) {
                requestCount -= 1;
                if (requestCount == 0) {
                    if (callback) callback.apply(context);
                }
            }
        });
    });
}

function checkBrowser() {
    var userAgent = navigator.userAgent;
    if (!/firefox/i.test(userAgent) && !/chrome/i.test(userAgent)) {
        $('#browsermsg').html('<div class="alert alert-error"><button type="button" class="close" data-dismiss="alert">&times;</button>The RockStor WebUI is supported only on Firefox or Chrome. Some features may not work correctly.</div>');
    }
    RockStorGlobals.browserChecked = true;
}

RockStorProbeMap = [];
RockStorGlobals = {
    navbarLoaded: false,
    applianceNameSet: false,
    currentAppliance: null,
    maxPageSize: 9000,
    browserChecked: false,
    kernel: null
};

var RS_DATE_FORMAT = 'MMMM Do YYYY, h:mm:ss a';

// Constants
probeStates = {
    STOPPED: 'stopped',
    CREATED: 'created',
    RUNNING: 'running',
    ERROR: 'error'
};

var RockstorUtil = function() {
    var util = {
        // maintain selected object list
        // list is an array of contains models

        // does the list contain a model with attr 'name' with value 'value'
        listContains: function(list, name, value) {
            return _.find(list, function(obj) {
                return obj.get(name) == value;
            });
        },

        // add obj from collection with attr 'name' and value 'value' to list
        addToList: function(list, collection, name, value) {
            list.push(collection.find(function(obj) {
                return obj.get(name) == value;
            }));
        },

        // remove obj with attr 'name' and value 'value'
        removeFromList: function(list, name, value) {
            var i = _.indexOf(_.map(list, function(obj) {
                return obj.get(name);
            }), value);
            if (i != -1) {
                list.splice(i, 1);
            }
        }
    };
    return util;
}();

RockstorWizardPage = Backbone.View.extend({

    initialize: function() {
        this.evAgg = this.options.evAgg;
        this.parent = this.options.parent;
    },

    render: function() {
        $(this.el).html(this.template({
            model: this.model
        }));
        return this;
    },

    save: function() {
        return $.Deferred().resolve();
    }
});

WizardView = Backbone.View.extend({
    tagName: 'div',

    events: {
        'click #next-page': 'nextPage',
        'click #prev-page': 'prevPage'
    },

    initialize: function() {
        this.template = window.JST.wizard_wizard;
        this.pages = null;
        this.currentPage = null;
        this.currentPageNum = -1;
        this.contentEl = '#ph-wizard-contents';
        this.evAgg = _.extend({}, Backbone.Events);
        this.evAgg.bind('nextPage', this.nextPage, this);
        this.evAgg.bind('prevPage', this.prevPage, this);
        this.parent = this.options.parent;
        this.title = this.options.title;
    },

    setPages: function(pages) {
        this.pages = pages;
    },

    render: function() {
        $(this.el).html(this.template({
            title: this.title,
            model: this.model
        }));
        this.nextPage();
        return this;
    },

    nextPage: function() {
        var _this = this;
        var promise = !_.isNull(this.currentPage) ?
            this.currentPage.save() :
            $.Deferred().resolve();
        promise.done(function(result, status, jqXHR) {
            _this.incrementPage();
        });
        promise.fail(function(jqXHR, status, error) {
            console.log(error);
        });
    },

    incrementPageNum: function() {
        this.currentPageNum = this.currentPageNum + 1;
    },

    decrementPageNum: function() {
        this.currentPageNum = this.currentPageNum - 1;
    },

    incrementPage: function() {
        if (!this.lastPage()) {
            this.incrementPageNum();
            this.setCurrentPage();
            this.renderCurrentPage();
        } else {
            this.finish();
        }
    },

    decrementPage: function() {
        if (!this.firstPage()) {
            this.decrementPageNum();
            this.setCurrentPage();
            this.renderCurrentPage();
        }
    },

    setCurrentPage: function() {
        this.currentPage = new this.pages[this.currentPageNum]({
            model: this.model,
            evAgg: this.evAgg
        });
    },

    renderCurrentPage: function() {
        this.$(this.contentEl).html(this.currentPage.render().el);
        this.modifyButtonText();
    },

    prevPage: function() {
        this.decrementPage();
    },

    modifyButtonText: function() {
        if (this.lastPage()) {
            this.$('#next-page').html('Finish');
        } else {
            this.$('#next-page').html('Next');
        }
    },

    firstPage: function() {
        return (this.currentPageNum == 0);
    },

    lastPage: function() {
        return (this.currentPageNum == (this.pages.length - 1));
    },

    finish: function() {
        console.log('finish');
    }
});