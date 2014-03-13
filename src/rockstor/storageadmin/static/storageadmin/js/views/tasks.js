
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

TasksView = RockstorLayoutView.extend({
  events: {
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.scheduled_tasks_tasks;
    this.paginationTemplate = window.JST.common_pagination;
    // add dependencies
    this.taskDefId = this.options.taskDefId;
    this.taskDef = new TaskDef({id: this.taskDefId});
    this.dependencies.push(this.taskDef);
    this.collection = new TaskCollection(null, {
      taskDefId: this.taskDefId
    });
    this.collection.pageSize = 10;
    this.dependencies.push(this.collection);
    this.collection.on("reset", this.renderTasks, this);
    // has the replica been fetched? prevents renderReplicaTrails executing
    // (because of collection reset) before replica has been fetched
    this.taskDefFetched = false;  
  },

  render: function() {
    this.fetch(this.firstFetch, this);
    return this;
  },
  
  firstFetch: function() {
    this.taskDefFetched = true;
    this.renderTasks();
  },

  renderTasks: function() {
    if (!this.taskDefFetched) return false;
    var _this = this;
    $(this.el).html(this.template({
      taskDef: this.taskDef,
      tasks: this.collection
    }));
    this.$(".pagination-ph").html(this.paginationTemplate({
      collection: this.collection
    }));
    this.$('[rel=tooltip]').tooltip({ placement: 'bottom'});
  },

});

// Add pagination
Cocktail.mixin(TasksView, PaginationMixin);


