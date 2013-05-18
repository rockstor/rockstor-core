RockStorWidgets = {};

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
  return _.filter(RockStorWidgets.available_widgets, function(widget) {
    return widget.defaultWidget;
  });
};

RockStorWidgets.defaultWidgetNames = function(name) {
  return _.map(RockStorWidgets.defaultWidgets(), function(widget) {
    return widget.name;
  });
};

RockStorWidgets.available_widgets = [ 
  { 
    name: 'sysinfo', 
    displayName: 'System Information', 
    view: 'SysInfoWidget', 
    description: 'System Information',
    defaultWidget: true,
    category: 'Compute'
  },
  { 
    name: 'cpuusage', 
    displayName: 'CPU Utilization', 
    view: 'CpuUsageWidget',
    description: 'CPU Utilization',
    defaultWidget: true,
    category: 'Compute'
  },
  { 
    name: 'sample', 
    displayName: 'Sample Widget', 
    view: 'SampleWidget',
    description: 'A Sample Widget',
    defaultWidget: false,
    category: 'Network'
  },
  { 
    name: 'top_shares_usage', 
    displayName: 'Top Shares By Usage', 
    view: 'SampleWidget',
    description: 'Displays Top Shares by percentage of space used',
    defaultWidget: true,
    category: 'Storage'
  },
];

