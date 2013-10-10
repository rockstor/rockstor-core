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

PaginationMixin = {
  events: {
    "click .go-to-page": "goToPage",
    "click .prev-page": "prevPage",
    "click .next-page": "nextPage",
  },
  goToPage: function(event) {
    if (event) event.preventDefault();
    this.collection.goToPage(parseInt($(event.currentTarget).attr("data-page")));
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

RockstoreLayoutView = Backbone.View.extend({
  tagName: 'div',
  className: 'layout',
  requestCount: 0,

  initialize: function() {
    this.subviews = {};
    this.dependencies = [];
  },

  fetch: function(callback, context) {
    if (this.dependencies.length == 0) {
      if (callback) callback.apply(context);
    }
    var _this = this;
    _.each(this.dependencies, function(dependency) {
      _this.requestCount += 1;
      dependency.fetch({
        success: function(request){
          _this.requestCount -= 1;
          if (_this.requestCount == 0) {
            if (callback) callback.apply(context);
          }
        },
        error: function(request, response) {
          console.log('failed to fetch model in rockstorlayoutview');
          console.log(dependency);
          _this.requestCount -= 1;
          if (_this.requestCount == 0) {
            if (callback) callback.apply(context);
          }
        }
      });
    });
    return this;
  },
});


// RockstoreModuleView

RockstoreModuleView = Backbone.View.extend({
  
  tagName: 'div',
  className: 'module',
  requestCount: 0,

  initialize: function() {
    this.subviews = {};
    this.dependencies = [];
  },

  fetch: function(callback, context) {
    if (this.dependencies.length == 0) {
      if (callback) callback.apply(context);
    }
    var _this = this;
    _.each(this.dependencies, function(dependency) {
      _this.requestCount += 1;
      dependency.fetch({
        success: function(request){
          _this.requestCount -= 1;
          if (_this.requestCount == 0) {
            if (callback) callback.apply(context);
          }
        }
      });
    });
    return this;
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
    'click .download-widget': 'download',
  },

  initialize: function() {
    this.maximized = this.options.maximized;
    this.name = this.options.name;
    this.displayName = this.options.displayName;
    this.parentView = this.options.parentView;
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
      w.attr('data-ss-colspan',widgetDef.maxCols);
      w.attr('data-ss-rowspan',widgetDef.maxRows);
      this.maximized = true;
    } else {
      // Restoring
      w.detach();
      w.attr('data-ss-colspan',widgetDef.cols);
      w.attr('data-ss-rowspan',widgetDef.rows);
      // find current list item at original index
      if (_.isNull(this.originalPosition) || 
          _.isUndefined(this.originalPosition)) {
        this.originalPosition = 0;
      }
      curr_w = c.find("div.widget-ph:eq("+this.originalPosition+")");
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
    logger.debug("In RockStorWidgetView close");
  }

});

RockstoreButtonView = Backbone.View.extend({
  tagName: 'div',
  className: 'button-bar',

  initialize: function() {
    this.actions = this.options.actions;
    this.layout = this.options.layout;
    this.template = window.JST.common_button_bar;

  },
  
  render: function() {
    $(this.el).append(this.template({actions: this.actions}));
    this.attachActions();
    return this;
  },

  attachActions: function() {

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
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

function showError(errorMsg) {
  if (_.isUndefined(errorPopup)) {
    errorPopup = $('#errorPopup').modal({
      show: false
    });
  }
 // $('#errorContent').html("<h3>Error!</h3>");
  var msg = errorMsg;
  try {
    msg = JSON.parse(errorMsg).detail;
  } catch(err) {
  }
  $('#errorContent').html(msg);
  $('#errorPopup').modal('show');
}

errorPopup = undefined;

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
  _this.$('#'+elementName).css('visibility', 'visible');
}

function hideLoadingIndicator(elementName, context) {
  var _this = context;
  _this.$('#'+elementName).css('visibility', 'hidden');
}

function disableButton(button) {
  button.data("executing", true);
  button.attr("disabled", true);
}

function enableButton(button) {
  button.data("executing", false);
  button.attr("disabled", false);
}

function buttonDisabled(button) {
  if (button.data("executing")) {
    return true;
  } else {
    return false;
  }
}

function refreshNavbar() {
  var navbarTemplate = window.JST.common_navbar;
  $("#navbar-links").html(navbarTemplate({
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
  } catch(err) {
  }
  if (typeof(msg)=="string") {
    try {
      msg = JSON.parse(msg);
    } catch(err) {
    }
  }
  return msg;

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
        $('#appliance-name').html(RockStorGlobals.currentAppliance.get('ip')); 
      }
    },
    error: function(request, response) {
      console.log("error while loading appliances");
    }

  });
}

function updateLoadAvg() {
  RockStorGlobals.loadAvgTimer = window.setInterval(function() {
    fetchLoadAvg();
  }, 60000);
  fetchLoadAvg();
  RockStorGlobals.loadAvgDisplayed = true;
}

function fetchLoadAvg() {
  $.ajax({
    url: "/api/commands/uptime?format=json", 
    type: "POST",
    dataType: "json",
    global: false, // dont show global loading indicator
    success: function(data, status, xhr) {
      displayLoadAvg(data);
    },
    error: function(xhr, status, error) {
      console.log(error);
    }
  });
}

function displayLoadAvg(data) {
  var n = parseInt(data);
  var secs = n % 60;
  var mins = Math.round(n/60) % 60;
  var hrs = Math.round(n / (60*60)) % 24;
  var days = Math.round(n / (60*60*24)) % 365;
  var yrs = Math.round(n / (60*60*24*365));
  var str = 'Uptime: ';
  if (yrs == 1) {
    str += yrs + ' year, ';
  } else if (yrs > 1) {
    str += yrs + ' years, ';
  }
  if (days == 1) {
    str += days + ' day, '; 
  } else {
    str += days + ' days, ';
  }
  str += hrs + ':' + mins;  
  $('#appliance-loadavg').html(str);
}

function fetchDependencies(dependencies, callback, context) {
  if (dependencies.length == 0) {
    if (callback) callback.apply(context);
  }
  var requestCount = dependencies.length;
  _.each(dependencies, function(dependency) {
    dependency.fetch({
      success: function(request){
        requestCount -= 1;
        if (requestCount == 0) {
          if (callback) callback.apply(context);
        }
      },
      error: function(request, response) {
        console.log('failed to fetch model in fetchDependencies');
        requestCount -= 1;
        if (requestCount == 0) {
          if (callback) callback.apply(context);
        }
      }
    });
  });
}

RockStorProbeMap = [];
RockStorGlobals = {
  navbarLoaded: false,
  applianceNameSet: false,
  currentAppliance: null,

}

var RS_DATE_FORMAT = 'h:mm:ss a ddd MMM DD YYYY';

// Constants
probeStates = {
  STOPPED: 'stopped', 
  CREATED: 'created',
  RUNNING: 'running', 
  ERROR: 'error',
};

