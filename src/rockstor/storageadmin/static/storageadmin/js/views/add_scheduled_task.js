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
		"change #task_type": "renderOptionalFields"
	},

	initialize: function() {
		this.constructor.__super__.initialize.apply(this, arguments);
		this.template = window.JST.scheduled_tasks_add_task;
		this.snapshotFieldsTemplate = window.JST.scheduled_tasks_snapshot_fields;
		this.scrubFieldsTemplate = window.JST.scheduled_tasks_scrub_fields;
		this.shares = new ShareCollection();
		this.pools = new PoolCollection();
		this.shares.pageSize = RockStorGlobals.maxPageSize;
		this.pools.pageSize = RockStorGlobals.maxPageSize;
		this.dependencies.push(this.shares);
		this.dependencies.push(this.pools);
		this.taskDefId = this.options.taskDefId;
		if (!_.isUndefined(this.taskDefId) && !_.isNull(this.taskDefId)) {
			this.taskDef = new TaskDef({id: this.taskDefId});
			this.dependencies.push(this.taskDef);
		}
		if(this.taskDefId == null){
			this.taskDefIdNull = true;
		}else{
			this.taskDefIdNull = false;
		}
		this.initHandlebarHelpers();
	},

	render: function() {
		this.fetch(this.renderNewScheduledTask, this);
		return this;
	},

	renderNewScheduledTask: function() {
		if(this.taskDef){
		var taskObj = {name: this.taskDef.get('name'),
				type: this.taskDef.get('task_type'),
				share: this.taskDef.share(),
				prefix: this.taskDef.prefix(),
				pool: this.taskDef.pool(),
				maxCount: this.taskDef.max_count(),
				visible: this.taskDef.visible(),
				enabled: this.taskDef.get('enabled'),
		};
		var isSnapshot = false;
		if(taskObj.type == 'snapshot'){
			isSnapshot = true;
		}
	}
		var _this = this;
		$(this.el).html(this.template({
			shares: this.shares,
			pools: this.pools,
			taskTypes: ['snapshot', 'scrub'],
			taskDef: this.taskDef,
			taskObj: taskObj,
			taskDefId: this.taskDefId,
			taskDefIdNull: this.taskDefIdNull,
			isSnapshot: isSnapshot,
		}));
		if (!_.isUndefined(this.taskDefId) && !_.isNull(this.taskDefId)) {
			var crontab = this.taskDef.get('crontab');
			$('#cron').cron("value", crontab);
			var crontabwindow = _.isNull(this.taskDef.get('crontabwindow')) ? "*-*-*-*-*-*" : this.taskDef.get('crontabwindow'); // render execution window, on null set to *-*-*-*-*-*
			$('#cron-window').cron_window("value", crontabwindow);
		}
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
							return (_this.$('#task_type').val() == 'snapshot');
						}
					}
				},
				'meta.prefix': {
					required: {
						depends: function(element) {
							return (_this.$('#task_type').val() == 'snapshot');
						}
					}
				},
				'meta.max_count': {
					number: true,
					min: 1,
					required: {
						depends: function(element) {
							return (_this.$('#task_type').val() == 'snapshot');
						},

					}
				},
				pool: {
					required: {
						depends: function(element) {
							return (_this.$('#task_type').val() == 'scrub');
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
					var req_type = 'POST';
				} else {
					var url = '/api/sm/tasks/' + _this.taskDefId;
					var req_type = 'PUT';
				}
				data.crontab = $("#cron").cron("value");
				data.crontabwindow = $("#cron-window").cron_window("value"); // post execution window value
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
			taskType = this.$('#task_type').val();
		} else {
			taskType = this.taskDef.get('task_type');
		}
		if (taskType == 'snapshot') {
			this.$('#optional-fields').html(this.snapshotFieldsTemplate({
				shares: this.shares,
				taskDef: this.taskDef,
				taskDefId: this.taskDefId,
				taskDefIdNull: this.taskDefIdNull,
				taskMaxCount: this.taskMaxCount,
			}));
		} else {
			this.$('#optional-fields').html(this.scrubFieldsTemplate({
				pools: this.pools,
				taskDef: this.taskDef,
				taskDefId: this.taskDefId,
				taskDefIdNull: this.taskDefIdNull,
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
	},

	initHandlebarHelpers: function(){
		Handlebars.registerHelper('display_snapshot_shares', function(){
			var html = '';
			this.shares.each(function(share, index) {
				html += '<option value="' + share.get('name') + '"> ' + share.get('name') + '</option>';
			});
			return new Handlebars.SafeString(html);
		});

		Handlebars.registerHelper('display_scrub_pools', function(){
			var html = '';
			this.pools.each(function(pool, index) {
				html += '<option value="' + pool.get('name') + '"> ' + pool.get('name') + '</option>';
			});
			return new Handlebars.SafeString(html);
		});

	}

});
