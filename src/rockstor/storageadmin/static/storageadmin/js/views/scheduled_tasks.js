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

ScheduledTasksView = RockstorLayoutView.extend({
    events: {
        'click .toggle-task': 'toggleEnabled',
        'click a[data-action=delete]': 'deleteTask'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.scheduled_tasks_task_defs;
        this.collection = new TaskDefCollection();
        this.tasks = new TaskCollection();
        this.dependencies.push(this.collection);
        this.dependencies.push(this.tasks);
        this.collection.on('reset', this.renderScheduledTasks, this);
        this.taskMap = {};
        this.initHandlebarHelpers();
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
            collection: this.collection,
            collectionNotEmpty: !this.collection.isEmpty(),
            taskMap: this.taskMap
        }));
        this.$('[rel=tooltip]').tooltip({ placement: 'bottom'});

        this.renderDataTables();
    },

    toggleEnabled: function(event) {
        var _this = this;
        if (event) { event.preventDefault(); }
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var taskId = $(event.currentTarget).attr('data-task-id');
        var enabled = $(event.currentTarget).attr('data-action') == 'enable'
			? true : false;
        $.ajax({
            url: '/api/sm/tasks/' + taskId,
            type: 'PUT',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({enabled: enabled}),
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
            }
        });
    },

    deleteTask: function(event) {
        var _this = this;
        if (event) { event.preventDefault(); }
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        var taskId = $(event.currentTarget).attr('data-task-id');
        var taskName = $(event.currentTarget).attr('data-task-name');
        if(confirm('Delete task:  ' + taskName + '. Are you sure?')){
            $.ajax({
                url: '/api/sm/tasks/' + taskId,
                type: 'DELETE',
                dataType: 'json',
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
                }
            });
        }
    },

    initHandlebarHelpers: function(){
        Handlebars.registerHelper('display_scheduledTasks_table', function(adminBool){
            var html = '',
                _this = this;
            this.collection.each(function(t) {
                var taskId = t.get('id'),
                    taskName = t.get('name'),
                    taskType = t.get('task_type'),
                    jsonMeta = t.get('json_meta'),
                    tId = t.id,
                    taskMapId = _this.taskMap[tId];

                html += '<tr>';
                html += '<td><a href="#edit-scheduled-task/' + taskId + '">' + taskName + '</a></td>';
                html += '<td>' + taskType + '&nbsp;';
                if (taskType == 'snapshot') {
                    // TODO: fix this to go direct to Snapshots tab.
                    html += '(<a href="#shares/' + JSON.parse(jsonMeta).share + '">';
                    html += t.get('share_name') + '</a>)';
                } else if (taskType == 'scrub') {
                    // TODO: fix this to go direct to Scrubs tab.
                    html += '(<a href="#pools/' + JSON.parse(jsonMeta).pool + '">';
                    html += t.get('pool_name') + '</a>)';
                }
                html += '</td>';
                html += '<td>' + prettyCron.toString(t.get('crontab')) + '</td>';
                html += '<td>' + render_cronwindow(t.get('crontabwindow')) + '</td>';
                html += '<td>';
                if (t.get('enabled')) {
                    html += '<input type="checkbox" disabled="true" checked="true"></input>';
                } else {
                    html += '<input type="checkbox" disabled="true"></input>';
                }
                html += '</td>';
                html += '<td>';
                if (taskMapId) {
                    if (taskMapId.length > 0) {
                        var task = taskMapId[0],
                            taskState = task.get('state');

                        if (taskState != 'started' && taskState != 'running' && taskState != 'finished') {
                            html += '<a href="#scheduled-tasks/' + tId + '/log" class="task-log"><i class="glyphicon glyphicon-warning-sign"></i> ' + taskState + '</a>';
                        } else if (taskState == 'finished') {
                            html += '<a href="#scheduled-tasks/' + tId + '/log" class="task-log">' + moment(task.get('end')).fromNow() + '</a>';
                        } else {
                            html += '<a href="#scheduled-tasks/' + tId + '/log" class="task-log">' + taskState + '</a>';
                        }
                    }
                }
                html += '</td>';
                html += '<td>';
                html += '<a href="#edit-scheduled-task/' + taskId + '" <i class= "glyphicon glyphicon-pencil" rel="rooltip" title="Edit"></i></a>&nbsp;';
                html += '<a href="#" data-task-name="' + taskName + '" data-task-id="' + tId + '" data-action="delete"><i class="glyphicon glyphicon-trash" rel="tooltip" title="Delete"></i></a>';

                html += '</td>';
                html += '</tr>';
            });
            return new Handlebars.SafeString(html);
        });
    }
});

//Add pagination
Cocktail.mixin(ScheduledTasksView, PaginationMixin);

//Adding new inline func to render crontabwindow in a nice way and not just like a string

function render_cronwindow(cwindow) {
    var rendercwindow;
    if (!cwindow || cwindow == '*-*-*-*-*-*') {
        rendercwindow = 'Run always'; //render always without other checks
    } else {
        cwindow = cwindow.split('-');
        for (var i = 0; i < 4; i++) {
            if (cwindow[i] != '*' && cwindow[i].length == 1) { cwindow[i] = '0' + cwindow[i]; }
        }
        rendercwindow = '<i class="fa fa-clock-o"/>&nbsp;';
        if (cwindow[0] != '*') { //if hour start isn't always value the same do min start and hour min stop
            rendercwindow += 'from ' + cwindow[0] + ':' + cwindow[1];
            rendercwindow += ' to ' + cwindow[2] + ':' + cwindow[3];
        } else {
            rendercwindow += ' every hour';
        }
        rendercwindow += '&nbsp;-&nbsp;<i class="fa fa-calendar"/>&nbsp;';
        if (cwindow[4] != '*') { //as for hour start, if day start isn't star then day stop too
            var dayname = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
            rendercwindow += dayname[cwindow[4]] + ' to ' + dayname[cwindow[5]];
        } else {
            rendercwindow += ' on every day';
        }
    }
    return rendercwindow;
}
