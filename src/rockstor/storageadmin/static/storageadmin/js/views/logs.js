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
    },
    initialize: function() {
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.logs_logs;
	this.initHandlebarHelpers();
    },

    render: function() {
	this.$el.html(this.template);
	this.$('[rel=tooltip]').tooltip({ placement: 'top'});
	return this;
    },

    LogBaskets: function(event) {
	event.preventDefault();
	var parent_div = $(event.currentTarget).parent().attr('id');
	var dest_div = parent_div == 'avail_logs' ? '#download_logs' : '#avail_logs';
	$(event.currentTarget).fadeTo(500,0, function(){
		$(dest_div).append(event.currentTarget);
		$(event.currentTarget).fadeTo(500,1);
	});
    },

    LoadServerLogs: function() {
	var _this = this;
	var read_type = $('#read_type').val();
        var logs_options = $('#logs_options').val();
	var log_file = $('#logs_options option:selected').text();
	var read_tool = $('#read_type option:selected').text();
        var url = '/api/sm/syslogs/';
        url += read_type + '/' + logs_options;
	var modal_title = '<b>Selected log:</b>&nbsp; ' + log_file;
	modal_title += '<br/><b>Reader type:</b>&nbsp;' + read_tool;
	$("#LogReaderLabel").html(modal_title);  
        $.ajax({
         url: url,
         type: 'GET',
         dataType: 'text',
         global: false,
         success: function(data) {
                $('#system_log').text(data);
                _this.ShowLogReader();
         },
        });
    },

    ShowLogReader: function() {
	$('#log_reader').modal({
	    keyboard: true,
            show: false,
            backdrop: 'static'
        });
        $('#log_reader').modal('show');
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
