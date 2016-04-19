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
	'click .logs-item': 'logbaskets'
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

    logbaskets: function(event) {
	event.preventDefault();
	//_this = event.currentTarget;
	var parent_div = $(event.currentTarget).parent().attr('id');
	var dest_div = parent_div == 'avail_logs' ? '#download_logs' : '#avail_logs';
	$(event.currentTarget).fadeTo(500,0, function(){
		$(dest_div).append(event.currentTarget);
		$(event.currentTarget).fadeTo(500,1);
	});
    },

    initHandlebarHelpers: function(){
      var avail_logs =  {
                        "Rockstor Logs" : "rockstor",
                        "Dmesg" : "dmesg",
                        "Nmbd (Samba)" : "nmbd",
                        "Smbd (Samba)" : "smbd",
                        "Winbindd (Samba)" : "winbindd",
                        "Nginx" : "nginx",
                        "Yum" : "yum"
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
