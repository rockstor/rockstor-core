RockStorWidgets = {};
RockStorWidgets.max_width = 3;
RockStorWidgets.max_height = 2;

RockStorWidgets.findByName = function(name) {
  return _.find(RockStorWidgets.available_widgets, function(widget) {
    return widget.name == name;
  });
};

RockStorWidgets.findByCategory = function(category) {
  return _.filter(RockStorWidgets.available_widgets, function(widget) {
    return widget.category == category;
  });
};

RockStorWidgets.defaultWidgets = function() {
  var tmp = _.filter(RockStorWidgets.available_widgets, function(widget) {
    return widget.defaultWidget;
  });
  return _.sortBy(tmp, function(w) {
    if (!_.isUndefined(w.position) && !_.isNull(w.position)) {
      return w.position;
    } else {
      return Number.MAX_VALUE;
    }
  });
};

RockStorWidgets.defaultWidgetNames = function(name) {
  return _.map(RockStorWidgets.defaultWidgets(), function(widget) {
    return widget.name;
  });
};

RockStorWidgets.available_widgets = [];

