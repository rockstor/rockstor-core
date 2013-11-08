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

ScheduledTasksView = RockstoreLayoutView.extend({
  events: {
    'click .toggle-task': 'toggleEnabled',
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.scheduled_tasks_tasks;
    // add dependencies
    this.collection = new TaskDefCollection();
    this.tasks = new TaskCollection();
    this.dependencies.push(this.collection);
    this.dependencies.push(this.tasks);
    this.taskMap = {};
  },

  render: function() {
    this.fetch(this.renderScheduledTasks, this);
    return this;
  },

  renderScheduledTasks: function() {
    var _this = this;
    
    this.collection.each(function(taskDef, index) {
      var tmp = _this.tasks.filter(function(task) {
        return task.get('task_def') == taskDef.id;
      });
      _this.taskMap[taskDef.id] = _.sortBy(tmp, function(task) {
        return moment(task.get('start')).valueOf();
      }).reverse();
    });
    // remove existing tooltips
    if (this.$('[rel=tooltip]')) { 
      this.$('[rel=tooltip]').tooltip('hide');
    }
    $(this.el).html(this.template({
      scheduledTasks: this.collection,
      taskMap: this.taskMap
    }));
    this.$('[rel=tooltip]').tooltip({ placement: 'bottom'});
   
  },

  toggleEnabled: function(event) {
    var _this = this;
    if (event) { event.preventDefault(); }
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    disableButton(button); 
    var taskId = $(event.currentTarget).attr("data-task-id");
    var enabled = $(event.currentTarget).attr('data-action') == 'enable' 
    ? true : false;
    $.ajax({
      url: '/api/sm/tasks/' + taskId,
      type: 'PUT',
      dataType: 'json',
      data: {enabled: enabled},
      success: function() {
        enableButton(button);
        _this.collection.fetch({
          success: function() {
            _this.renderScheduledTasks();
          }
        });
      },
      error: function(xhr, status, error) {
        enableButton(button);
        var msg = parseXhrError(xhr)
        _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
      }
    });
  },

});

// Add pagination
Cocktail.mixin(ReplicationView, PaginationMixin);


