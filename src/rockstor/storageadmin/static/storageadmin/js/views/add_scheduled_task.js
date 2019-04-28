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


AddScheduledTaskView = RockstorLayoutView.extend({
    events: {
        'click #js-cancel': 'cancel',
        'change #task_type': 'renderOptionalFields',
        'click #wakeup': 'switchRtcFields',
        'click #ping_scan': 'switchPingScanFields'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.scheduled_tasks_add_task;
        this.snapshotFieldsTemplate = window.JST.scheduled_tasks_snapshot_fields;
        this.scrubFieldsTemplate = window.JST.scheduled_tasks_scrub_fields;
        this.shutdownFieldsTemplate = window.JST.scheduled_tasks_shutdown_fields;
        this.shares = new ShareCollection();
        this.pools = new PoolCollection();
        this.shares.pageSize = RockStorGlobals.maxPageSize;
        this.pools.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.shares);
        this.dependencies.push(this.pools);
        this.taskDefId = this.options.taskDefId;
        this.taskTypes = [
            {name: 'scrub', description: 'Btrfs Scrub'},
            {name: 'snapshot', description: 'Btrfs Snapshot'},
            {name: 'reboot', description: 'System Reboot'},
            {name: 'shutdown', description: 'System Shutdown'},
            {name: 'suspend', description: 'System Suspend'}
            //{name: 'custom', description: 'User Custom Task'}
        ];
        if (!_.isUndefined(this.taskDefId) && !_.isNull(this.taskDefId)) {
            this.taskDef = new TaskDef({id: this.taskDefId});
            this.dependencies.push(this.taskDef);
        }
        if (this.taskDefId == null) {
            this.taskDefIdNull = true;
        } else {
            this.taskDefIdNull = false;
        }
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.renderNewScheduledTask, this);
        return this;
    },

    renderNewScheduledTask: function() {
        if (this.taskDef) {
            var taskObj = {
                name: this.taskDef.get('name'),
                type: this.taskDef.get('task_type'),
                share: this.taskDef.share(),
                share_name: this.taskDef.get('share_name'),
                prefix: this.taskDef.prefix(),
                pool: this.taskDef.pool(),
                pool_name: this.taskDef.get('pool_name'),
                maxCount: this.taskDef.max_count(),
                visible: this.taskDef.visible(),
                writable: this.taskDef.writable(),
                enabled: this.taskDef.get('enabled'),
                wakeup: this.taskDef.wakeup(),
                rtcHour: this.taskDef.rtc_hour(),
                rtcMinute: this.taskDef.rtc_minute()
            };
        // Hacking Handlebars registerPartial normal usage
        // Handlebars has registerPartial to help with nested templates
        // inside another template (ex. Person template having sub-templates
        // Job, Hobbies, etc). Handlebars.registerPartial(partial, value) with
        // typeOf(value) == string, while we use value for strings and bools.
        // Previous version of task page had a "master" part plus
        // optional-fields div filled only for new tasks, relaying on a messy
        // general part (if new task -> normal, else render optional-fields)
        // Now we go with full optional-fields use, serving both when adding
        // new tasks and when editing existing tasks

        // Define taskObj fields having booleans (html checked checkboxes)
        // requiring conversion to string value checked
            var bool_fields = ['visible', 'writable', 'enabled', 'wakeup', 'ping_scan'];

        // Loop over taskObj and build Partials like taskObj.key so
        // we just have to move fro {{taskObj.field_name}} to
        // {{> taskObj.field_name}} <- check Handlebars ref for
        // furgher infos. While on loop if we found a bool we fix it,
        // else we have key val to string or empty string, because
        // registerPartial does not accept undefined vals
            _.each(taskObj, function(val, key) {
                var partial_name = 'taskObj.' + key;
                var partial_value;
                if (_.contains(bool_fields, key)) {
                    partial_value = val ? 'checked' : '';
                } else {
                    partial_value = val != null ? val.toString() : '';
                }
                Handlebars.registerPartial(partial_name, partial_value);
            });
        
        }
        var _this = this;
        $(this.el).html(this.template({
            shares: this.shares,
            pools: this.pools,
            taskTypes: this.taskTypes,
            taskDef: this.taskDef,
            taskDefId: this.taskDefId,
            taskDefIdNull: this.taskDefIdNull
        }));
        if (!_.isUndefined(this.taskDefId) && !_.isNull(this.taskDefId)) {
            var crontab = this.taskDef.get('crontab');
            $('#cron').cron('value', crontab);
            var crontabwindow = _.isNull(this.taskDef.get('crontabwindow')) ? '*-*-*-*-*-*' : this.taskDef.get('crontabwindow'); // render execution window, on null set to *-*-*-*-*-*
            $('#cron-window').cron_window('value', crontabwindow);
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
                            return (_this.$('#task_type').val() === 'snapshot');
                        }
                    }
                },
                'meta.share_name': {
                    required: {
                        depends: function(element) {
                            return (_this.$('#task_type').val() === 'snapshot');
                        }
                    }
                },
                'meta.prefix': {
                    required: {
                        depends: function(element) {
                            return (_this.$('#task_type').val() === 'snapshot');
                        }
                    }
                },
                'meta.max_count': {
                    number: true,
                    min: 1,
                    required: {
                        depends: function(element) {
                            return (_this.$('#task_type').val() === 'snapshot');
                        },

                    }
                },
                pool: {
                    required: {
                        depends: function(element) {
                            return (_this.$('#task_type').val() === 'scrub');
                        }
                    }
                },
                'meta.pool_name': {
                    required: {
                        depends: function(element) {
                            return (_this.$('#task_type').val() === 'scrub');
                        }
                    }
                },
                'meta.ping_scan_addresses': {
                    required: {
                        depends: function (element) {
                            return ((_this.$('#task_type').val() === 'shutdown') || (_this.$('#task_type').val() === 'suspend'))
                        }
                    }
                },
                'meta.ping_scan_interval': {
                    number: true,
                    min: 5,
                    required: {
                        depends: function (element) {
                            return ((_this.$('#task_type').val() === 'shutdown') || (_this.$('#task_type').val() === 'suspend'))
                        }
                    }
                },
                'meta.ping_scan_iterations': {
                    number: true,
                    min: 1,
                    required: {
                        depends: function (element) {
                            return ((_this.$('#task_type').val() === 'shutdown') || (_this.$('#task_type').val() === 'suspend'))
                        }
                    }
                }
            },
            submitHandler: function() {
                var button = $('#create-scheduled-task');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var data = _this.$('#scheduled-task-create-form').getJSON();
                var url, req_type;
                if (_this.taskDefId == null) {
                    url = '/api/sm/tasks/';
                    req_type = 'POST';
                } else {
                    url = '/api/sm/tasks/' + _this.taskDefId;
                    req_type = 'PUT';
                }
                data.crontab = $('#cron').cron('value');
                data.crontabwindow = $('#cron-window').cron_window('value'); // post execution window value
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
        if (taskType === 'snapshot') {
            this.$('#optional-fields').html(this.snapshotFieldsTemplate({
                shares: this.shares.toJSON(),
                taskDef: this.taskDef,
                taskDefId: this.taskDefId,
                taskDefIdNull: this.taskDefIdNull,
                taskMaxCount: this.taskMaxCount,
            }));
        } else if (taskType === 'scrub') {
            this.$('#optional-fields').html(this.scrubFieldsTemplate({
                pools: this.pools.toJSON(),
                taskDef: this.taskDef,
                taskDefId: this.taskDefId,
                taskDefIdNull: this.taskDefIdNull,
            }));
        } else if (taskType === 'shutdown' || taskType === 'suspend') {
            this.$('#optional-fields').html(this.shutdownFieldsTemplate({
                taskDef: this.taskDef,
                taskDefId: this.taskDefId,
                taskDefIdNull: this.taskDefIdNull,
            }));
            this.rendergentleSelect('rtc_hour');
            this.rendergentleSelect('rtc_minute');
            /*  if (this.taskDefId == null && taskType == 'suspend') {
                this.$('#wakeup').click()
                                 .prop('disabled', true);
            }*/
            if (this.taskDefId != null && this.taskDef.wakeup()) {
                this.$('#rtc_hour').val(this.taskDef.rtc_hour()).gentleSelect('update');
                this.$('#rtc_minute').val(this.taskDef.rtc_minute()).gentleSelect('update');
                this.$('#wakeup').click();
            }
            if (this.taskDefId != null && this.taskDef.ping_scan()) {
                this.$('#ping_scan_addresses').val(this.taskDef.ping_scan_addresses());
                this.$('#ping_scan_interval').val(this.taskDef.ping_scan_interval());
                this.$('#ping_scan_iterations').val(this.taskDef.ping_scan_iterations());
                this.$('#ping_scan').click();
            }
        } else {
            this.$('#optional-fields').empty();
        }
        // Render warning about rtc wakeup to be checked
        if (taskType === 'shutdown' || taskType === 'suspend') {
            var html = '';
            html += '<div class="alert alert-warning">';
            html += 'Please check and test your system RTC WAKEUP capabilities before setting a suspend/shutdown task</div>';
            this.$('.messages').html(html);
        } else {
            this.$('.messages').empty();
        }
		// Reattach tooltips
        this.$('#scheduled-task-create-form :input').tooltip({
            placement: 'right'
        });
    },

    // Render rtc wake clock selects adding gentleSelect beautifier
    rendergentleSelect: function(field_name) {
        if (field_name === 'rtc_hour') {
            itemwidth = 20;
            columns = 2;
            title = 'Wake up Time: Hour';
        } else {
            itemwidth = 30;
            columns = 4;
            title = 'Wake up Time: Minute';
        }
        this.$('#' + field_name).gentleSelect({
            itemWidth: itemwidth,
            columns: columns,
            title: title
        });
    },

    switchRtcFields: function () {
        // Adding some animation, on enable rtc wake up
        // checked true/false toggle rtc clock fields
        this.$('#rtc_container').fadeToggle(200);
    },

    switchPingScanFields: function () {
        this.$('#ping_scan_container').fadeToggle(200);
    },

    initHandlebarHelpers: function(){

        // Handlebars helper creating rtc clock hours and mins options
        Handlebars.registerHelper('time_select', function(field_name) {
            var html = '';
            var time_iterator;
            if (field_name === 'rtc_hour') {
                time_iterator = 24;
            } else if (field_name === 'rtc_minute') {
                time_iterator = 60;
            }
            for (var i = 0; i < time_iterator; i++) {
                html += '<option value="' + i + '">';
                html += i < 10 ? '0' + i : i;
                html += '</option>';
            }
            return new Handlebars.SafeString(html);
        });
    },

    cancel: function(event) {
        event.preventDefault();
        app_router.navigate('scheduled-tasks', {trigger: true});
    },
});
