/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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
LogsView = RockstorLayoutView.extend({
    events: {
        'click .logs-item': 'LogBaskets',
        'click #live-log': 'LoadServerLogs',
        'click #download-logs': 'SubmitDownloadQueue',
        'click #reader-logs': 'SubmitReaderLogDownload',
        'click #modal_resize': 'ModalSwitchSize',
        'click #code_increase_size, #code_decrease_size': 'ModalResizeText',
        'change #read_type, #logs_options': 'RequestLogSize',
        'hidden.bs.modal #log_reader': 'ModalClose'
    },

    initialize: function() {
        RockStorSocket.logManager = io.connect('/logmanager', {
            'secure': true,
            'force new connection': true
        });
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.logs_logs;
        this.avail_logs;
        this.initHandlebarHelpers();
        this.download_basket = [];
    },

    render: function() {
        this.$el.html(this.template);
        this.$('[rel=tooltip]').tooltip({
            placement: 'top'
        });
        this.$('#download-logs').hide();
        RockStorSocket.addListener(this.getLogContent, this, 'logManager:logcontent');
        RockStorSocket.addListener(this.getLogSize, this, 'logManager:logsize');
        RockStorSocket.addListener(this.getLogsArchive, this, 'logManager:logsdownload');
        RockStorSocket.addListener(this.getRotatedLogs, this, 'logManager:rotatedlogs');
        return this;
    },

    getRotatedLogs: function(data) {
        //Handles rotated logs list got on connection to data_collector
        var _this = this;
        var reader_options = '<optgroup label="Rotated Logs">';
        var downloader_divs = '';
        $.each(data.rotated_logs_list, function(index, val) {
            //If rotated log is compress we don't add it to logs available for reading
            //example: usually nginx rotated logs
            var rotated_log_descriptor = val.log.replace(val.logfamily, _this.avail_logs[val.logfamily]);
            if (val.log.indexOf('.gz') < 0) reader_options += '<option value="' + val.log + '">' + rotated_log_descriptor + '</option>';
            downloader_divs += '<div class="logs-item" log="' + val.log + '" rotated="true">';
            downloader_divs += '<i class="fa fa-gears" aria-hidden="true"></i> ' + rotated_log_descriptor + '</div>';
        });
        reader_options += '</optgroup>';
        $('#logs_options').append(reader_options);
        $('#avail_logs').append(downloader_divs);
    },

    ModalClose: function(event) {
        //When LogReader modal window close emit to ensure any running tail -f get killed
        RockStorSocket.logManager.emit('livereading', 'kill');
    },

    ModalSwitchSize: function(event) {
        //LogReader modal window func to move small/large and viceversa
        event.preventDefault();
        var modal_container = $('#log_reader').children().first();
        var resize_icon = $(event.currentTarget).children().first();
        if (modal_container.hasClass('modal-lg')) {
            modal_container.removeClass('modal-lg');
            resize_icon.switchClass('glyphicon-resize-small', 'glyphicon-resize-full');
        } else {
            modal_container.addClass('modal-lg');
            resize_icon.switchClass('glyphicon-resize-full', 'glyphicon-resize-small');
        }
    },

    ModalResizeText: function(event) {
        //LogReader modal window func to resize code text size
        event.preventDefault();
        var resize_emitter = event.currentTarget.id;
        var size_delta = resize_emitter == 'code_increase_size' ? 1 : -1;
        var code_font_size = parseInt($('#system_log').css('font-size'));
        $('#system_log').css('font-size', code_font_size + size_delta);
    },

    getLogsArchive: function(data) {
        //Handle Logs tar archive based
        //If request sent from Archive builder show a link for download
        //Otherwise if from LogReader link auto-download archive
        var _this = this;
        if (data.recipient == 'download_response') {
            var response_text = 'Logs Archive ready for download - ';
            response_text += '<a href="' + data.archive_name + '" download>Click to download</a>';
            $('#' + data.recipient).html(response_text);
        } else {
            //On Log Reader we use a fake hidden link and after log download request
            //we trigger a click on it
            $('#reader-log-download').attr('href', data.archive_name);
            $('#reader-log-download')[0].click();
        }
    },

    getLogContent: function(data) {
        //When data is pushed from backend data_collector add it to LogReader and autoscroll to the end
        var _this = this;
        _this.updateLogProgress(data.current_rows, data.total_rows);
        $('#system_log').append(data.chunk_content);
        $('#system_log').closest('pre').scrollTop($('#system_log').closest('pre')[0].scrollHeight + 100);
        if ($('#logsize').text().length == 0) {
            $('#logsize').text((parseInt(data.content_size) / 1024).toFixed(2) + 'kB');
        }
    },

    getLogSize: function(data) {
        //Get log file size while selecting reader (cat,tail, etc) and log
        //If log file size greater than 500kB && reader is cat alerts user about possible long reading time
        log_size = (parseInt(data) / 1024).toFixed(2);
        if (log_size > 500) {
            var size_warning = '<div class="alert alert-warning logsizealert">';
            size_warning += '<strong>Warning!</strong>&nbsp;Log size is greater than 500kB (';
            size_warning += log_size + ' kB) and reading with cat could take a while</div>';
            $(size_warning).appendTo('#reader-block').hide().fadeIn(500);
        }
    },

    RequestLogSize: function(event) {
        //Call backend data_collector and ask for current log size
        $('.logsizealert').fadeOut(100, function() {
            $(this).remove();
        });
        if ($('#read_type').val() == 'cat') {
            current_log = $('#logs_options').val();
            RockStorSocket.logManager.emit('getfilesize', current_log);
        }
    },

    updateLogProgress: function(partial, total) {
        //Nicely update progressbar in LogReader modal
        $('#reader_progress').addClass('progress-bar-striped');
        current_rows = parseInt(partial);
        total_rows = parseInt(total);
        current_percent = (current_rows / total_rows * 100).toFixed(2);
        $('#reader_progress').attr('aria-valuenow', current_percent);
        $('#reader_progress').width(current_percent + '%');
        $('#reader_progress').text(current_percent + '%');
        if (current_rows == total_rows) {
            $('#reader_progress').removeClass('progress-bar-striped');
            $('#live-log').removeClass('disabled'); // Log totally rendered, enable again live log request button
        }
    },

    ShowLogDownload: function() {
        var download_queue = $('#download_logs').children();
        if (download_queue.length > 0) {
            $('#download-logs').show();
        } else {
            $('#download-logs').hide();
        }
    },

    SubmitReaderLogDownload: function(event) {
        _this = this;
        event.preventDefault();
        var log_file = $('#logs_options').val();
        log_file = log_file.split();
        RockStorSocket.logManager.emit('downloadlogs', log_file, 'reader_response');
    },

    SubmitDownloadQueue: function(event) {
        _this = this;
        _this.download_basket = [];
        $('#download_response').empty();
        var download_queue = $('#download_logs').children();
        download_queue.each(function() {
            _this.download_basket.push($(this).attr('log'));
        });
        $('#download-logs').blur();
        RockStorSocket.logManager.emit('downloadlogs', _this.download_basket, 'download_response');
    },

    LogBaskets: function(event) {
        //This function serves divs switching between Available Logs and Logs download queue
        var _this = this;
        event.preventDefault();
        $('#download_response').empty();
        var parent_div = $(event.currentTarget).parent().attr('id');
        var dest_div = parent_div == 'avail_logs' ? '#download_logs' : '#avail_logs';
        var is_rotated = ($(event.currentTarget).attr('rotated') === 'true');
        $(event.currentTarget).fadeTo(500, 0, function() {
            //If selected log is a rotated one append to list bottom
            //otherwise append to top
            if (is_rotated) {
                $(dest_div).append(event.currentTarget);
            } else {
                $(dest_div).prepend(event.currentTarget);
            }
            $(event.currentTarget).fadeTo(500, 1);
            _this.ShowLogDownload();
        });
    },

    LoadServerLogs: function() {
        //On user action for log reading append some info to LogReader modal, open it and ask backend for data
        $('#live-log').addClass('disabled'); // prevent users from submitting multiple reading requests same time
        $('#logsize').empty();
        var _this = this;
        var read_type = $('#read_type').val();
        var logs_options = $('#logs_options').val();
        var log_file = $('#logs_options option:selected').text();
        var read_tool = $('#read_type option:selected').text();
        var modal_title = '<b>Selected log:</b>&nbsp; <span>' + log_file + '</span>';
        modal_title += '<br/><b>Reader type:</b>&nbsp; <span>' + read_tool + '</span>';
        $('#LogReaderLabel').html(modal_title);
        $('#system_log').empty();
        _this.ShowLogReader();
        RockStorSocket.logManager.emit('readlog', read_type, logs_options);
    },

    ShowLogReader: function() {
        $('#log_reader').modal({
            keyboard: false,
            show: false,
            backdrop: 'static'
        });
        $('#log_reader').modal('show');
    },

    cleanup: function() {
        RockStorSocket.removeOneListener('logManager');
    },

    initHandlebarHelpers: function() {
        var _this = this;
        _this.avail_logs = {
            'rockstor': 'Rockstor Logs',
            'supervisord': 'Supervisord (Process monitor)',
            'dmesg': 'Dmesg (Kernel)',
            'nmbd': 'Nmbd (Samba)',
            'smbd': 'Smbd (Samba)',
            'winbindd': 'Winbindd (Samba)',
            'nginx': 'Nginx (WebUI)',
            'nginx_stdout': 'Nginx stdout (WebUI)',
            'nginx_stderr': 'Nginx stderr (WebUI)',
            'gunicorn': 'Gunicorn (WebUI)',
            'gunicorn_stdout': 'Gunicorn stdout (WebUI)',
            'gunicorn_stderr': 'Gunicorn stderr (WebUI)',
            'yum': 'Yum (System updates)'
        };

        Handlebars.registerHelper('print_logs_divs', function() {
            var html = '';
            $.each(_this.avail_logs, function(key, val) {
                html += '<div class="logs-item" log="' + key + '" rotated="false">';
                html += '<i class="fa fa-gear" aria-hidden="true"></i> ' + val + '</div>';
            });
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('print_logs_options', function() {
            var html = '<optgroup label="Current Logs">';
            $.each(_this.avail_logs, function(key, val) {
                html += '<option value="' + key + '">' + val + '</option>';
            });
            html += '</optgroup>';
            return new Handlebars.SafeString(html);
        });

    }
});

Cocktail.mixin(LogsView, PaginationMixin);