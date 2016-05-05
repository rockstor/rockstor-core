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
	'click #reader-logs' : 'SubmitReaderLogDownload',
	'change #read_type, #logs_options' : 'RequestLogSize'
    },

    initialize: function() {
	RockStorSocket.logReader = io.connect('/logmanager', {'secure': true, 'force new connection': true});
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.logs_logs;
	this.initHandlebarHelpers();
	this.download_basket = [];
    },

    render: function() {
	this.$el.html(this.template);
	this.$('[rel=tooltip]').tooltip({ placement: 'top'});
	this.$('#download-logs').hide();
	RockStorSocket.addListener(this.getLogContent, this, 'logReader:logcontent');
	RockStorSocket.addListener(this.getLogSize, this, 'logReader:logsize');
	RockStorSocket.addListener(this.getLogsArchive, this, 'logReader:logsdownload');
	return this;
    },

    getLogsArchive: function(data) {
	var _this = this;
	if (data.recipient == 'download_response') {
		var response_text = 'Logs Archive ready for download - ';
		response_text += '<a href="' + data.archive_name + '">Click to download</a>'
		$('#' + data.recipient).html(response_text);
	} else {
		$(location).attr('href', data.archive_name);
	}
    },

    getLogContent: function(data) {
	var _this = this;
	_this.updateLogProgress(data.current_rows, data.total_rows);
	$('#system_log').append(data.chunk_content);
	$('#system_log').closest('pre').scrollTop($('#system_log').closest('pre')[0].scrollHeight+100);
	if ($('#logsize').text().length == 0) { $('#logsize').text((parseInt(data.content_size)/1024).toFixed(2) + 'kB'); }
    },

    getLogSize: function(data) {
	log_size = (parseInt(data)/1024).toFixed(2);
	if (log_size > 500) {
		var size_warning = '<div class="alert alert-warning logsizealert">';
		size_warning += '<strong>Warning!</strong>&nbsp;Log size is greater than 500kB (';
		size_warning += log_size + ' kB) and reading with cat could take a while</div>';
		$(size_warning).appendTo('#reader-block').hide().fadeIn(500);
	}
    },

    RequestLogSize: function(event) {
        $('.logsizealert').fadeOut(100, function(){ $(this).remove(); });
        if ($('#read_type').val() == 'cat') {
                current_log = $('#logs_options').val();
                RockStorSocket.logReader.emit('getfilesize', current_log);
        }
    },

    updateLogProgress: function(partial, total) {
	$('#reader_progress').addClass('progress-bar-striped');
	current_rows = parseInt(partial);
	total_rows = parseInt(total);
	current_percent = (current_rows/total_rows*100).toFixed(2);
	$('#reader_progress').attr('aria-valuenow', current_percent);
	$('#reader_progress').width(current_percent + '%');
	$('#reader_progress').text(current_percent + '%');
	if (current_rows == total_rows) {
		$('#reader_progress').removeClass('progress-bar-striped');
	}

    },

    ShowLogDownload: function(){
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
	RockStorSocket.logReader.emit('downloadlogs', log_file, 'reader_response');
    },

    SubmitDownloadQueue: function(event){
	_this = this;
	_this.download_basket = [];
	$('#download_response').empty();
	var download_queue = $('#download_logs').children();
	download_queue.each(function(){
		_this.download_basket.push($(this).attr('log'));
	});
	$('#download-logs').blur();
	RockStorSocket.logReader.emit('downloadlogs', _this.download_basket, 'download_response');
    },

    LogBaskets: function(event) {
	var _this = this;
	event.preventDefault();
	$('#download_response').empty();
	var parent_div = $(event.currentTarget).parent().attr('id');
	var dest_div = parent_div == 'avail_logs' ? '#download_logs' : '#avail_logs';
	$(event.currentTarget).fadeTo(500,0, function(){
		$(dest_div).append(event.currentTarget);
		$(event.currentTarget).fadeTo(500,1);
		_this.ShowLogDownload();
	});
    },

    LoadServerLogs: function() {
	$('#logsize').empty();
	var _this = this;
	var read_type = $('#read_type').val();
	var logs_options = $('#logs_options').val();
	var log_file = $('#logs_options option:selected').text();
	var read_tool = $('#read_type option:selected').text();
	var modal_title = '<b>Selected log:</b>&nbsp; <span>' + log_file + '</span>';
	modal_title += '<br/><b>Reader type:</b>&nbsp; <span>' + read_tool + '</span>';
	$("#LogReaderLabel").html(modal_title);
	$('#system_log').empty();
        _this.ShowLogReader();
        RockStorSocket.logReader.emit('readlog', read_type, logs_options);
	RockStorSocket.logReader.emit('getfilesize', logs_options);
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
        RockStorSocket.removeOneListener('logReader');
    },

    initHandlebarHelpers: function(){
      var avail_logs =  {
                        "Rockstor Logs" : "rockstor",
                        "Dmesg (Kernel)" : "dmesg",
                        "Nmbd (Samba)" : "nmbd",
                        "Smbd (Samba)" : "smbd",
                        "Winbindd (Samba)" : "winbindd",
                        "Nginx (WebUI)" : "nginx",
                        "Yum (System updates)" : "yum"
                        };

    Handlebars.registerHelper('print_logs_divs', function(){
      var html = '';
      $.each(avail_logs, function(key, val) {
        html += '<div class="logs-item" log="' + val  + '"><i class="fa fa-gear" aria-hidden="true"></i> ' + key + '</div>';
      });
      return new Handlebars.SafeString(html);
    });

    Handlebars.registerHelper('print_logs_options', function(){
      var html = '';
      $.each(avail_logs, function(key, val) {
        html += '<option value="' + val  + '">' + key + '</option>';
      });
      return new Handlebars.SafeString(html);
    });
  
    }
});

Cocktail.mixin(LogsView, PaginationMixin);
