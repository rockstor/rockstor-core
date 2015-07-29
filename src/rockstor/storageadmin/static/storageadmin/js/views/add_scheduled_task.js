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


AddScheduledTaskView = RockstorLayoutView.extend({
    events: {
	"click #js-cancel": "cancel",
	"change #task-type": "renderOptionalFields",
    },

    initialize: function() {
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.scheduled_tasks_add_task;
	this.snapshotFieldsTemplate = window.JST.scheduled_tasks_snapshot_fields;
	this.scrubFieldsTemplate = window.JST.scheduled_tasks_scrub_fields;
	this.shares = new ShareCollection();
	this.pools = new PoolCollection();
	this.dependencies.push(this.shares);
	this.dependencies.push(this.pools);
	this.taskDefId = this.options.taskDefId;
	if (!_.isUndefined(this.taskDefId) && !_.isNull(this.taskDefId)) {
	    this.taskDef = new TaskDef({id: this.taskDefId});
	    this.dependencies.push(this.taskDef);
	}
    },

    render: function() {
	this.fetch(this.renderNewScheduledTask, this);
	return this;
    },

    renderNewScheduledTask: function() {
	var _this = this;
	$(this.el).html(this.template({
	    shares: this.shares,
	    pools: this.pools,
	    taskTypes: ['snapshot', 'scrub'],
	    taskDef: this.taskDef,
	    taskDefId: this.taskDefId
	}));
	this.renderOptionalFields();
	this.$('#start_date').datepicker();
	this.validator = $('#scheduled-task-create-form').validate({
	    onfocusout: false,
	    onkeyup: false,
	    rules: {
		name: 'required',
		start_date: 'required',
		frequency: {
		    required: true,
		    number: true,
		    min: 1
		},
		share: {
		    required: {
			depends: function(element) {
			    return (_this.$('#task-type').val() == 'snapshot');
			}
		    }
		},
		prefix: {
		    required: {
			depends: function(element) {
			    return (_this.$('#task-type').val() == 'snapshot');
			}
		    }
		},
		'meta.max_count': {
		    number: true,
		    min: 1,
		    required: {
			depends: function(element) {
			    return (_this.$('#task-type').val() == 'snapshot');
			},

		    }
		},
		'meta.visible': {
		    required: {
			depends: function(element) {
			    return (_this.$('#task-type').val() == 'snapshot');
			},
		    }
		},
		pool: {
		    required: {
			depends: function(element) {
			    return (_this.$('#task-type').val() == 'scrub');
			}
		    }
		}
	    },
	    submitHandler: function() {
		var button = $('#create-scheduled-task');
		if (buttonDisabled(button)) return false;
		disableButton(button);
		var data = _this.$('#scheduled-task-create-form').getJSON();
		if (_this.taskDefId == null) {
		    var url = '/api/sm/tasks/';
		    var req_type='POST';
		} else {
		    var url = '/api/sm/tasks/' + _this.taskDefId;
		    var req_type='PUT';
		}
		var cron_str = $("#cron").cron("value");
		console.log('crontab entry', cron_str);
		data.crontab = cron_str;
		$.ajax({
		    url: url,
		    type: req_type,
		    dataType: 'json',
		    contentType: 'application/json',
		    data: JSON.stringify(data),
		    success: function() {
			enableButton(button);
			app_router.navigate('scheduled-tasks', {trigger: true});
		    },
		    error: function(xhr, status, error) {
			enableButton(button);
		    }
		});
		return false;
	    }
	});
    },

    renderOptionalFields: function() {
	var taskType = null;
	if (this.taskDefId == null) {
	    taskType = this.$('#task-type').val();
	} else {
	    taskType = this.taskDef.get('task_type')
	}
	if (taskType == 'snapshot') {
	    this.$('#optional-fields').html(this.snapshotFieldsTemplate({
		shares: this.shares,
		taskDef: this.taskDef,
		taskDefId: this.taskDefId
	    }));
	} else {
	    this.$('#optional-fields').html(this.scrubFieldsTemplate({
		pools: this.pools,
		taskDef: this.taskDef,
		taskDefId: this.taskDefId
	    }));
	}
	// Reattach tooltips
	this.$('#scheduled-task-create-form :input').tooltip({
	    placement: 'right'
	});
    },

    cancel: function(event) {
	event.preventDefault();
	app_router.navigate('scheduled-tasks', {trigger: true});
    }

});
