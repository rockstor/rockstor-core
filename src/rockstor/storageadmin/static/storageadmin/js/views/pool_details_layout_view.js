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

PoolDetailsLayoutView = RockstorLayoutView.extend({

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.poolName = this.options.poolName;
    this.template = window.JST.pool_pool_details_layout;
    this.select_disks_template = window.JST.disk_select_disks_template;
    this.scrubTemplate = window.JST.pool_pool_scrub;
    this.pool = new Pool({poolName: this.poolName});
    this.dependencies.push(this.pool);
    this.disks = new DiskCollection();
    this.disks.pageSize = RockStorGlobals.maxPageSize;
  },

  events: {
    'click #delete-pool': 'deletePool',
    'click #scrub-pool-start': 'scrubPoolStart',
    'click #scrub-pool-refresh': 'scrubPoolRefresh',
  },

  render: function() {
    this.getScrubStatus();
    this.fetch(this.renderSubViews, this);
    return this;
  },

  getScrubStatus: function() {
    this.scrubStatus = 'finished';
    this.scrubPercent = 100;
    $.ajax({
      url: '/api/pools/' + this.pool.get('poolName') + '/scrub/status',
      type: 'POST',
      success: function(data, textStatus, jqXHR) {
        if (data != null) {
            this.scrubStatus = data.status;
            this.scrubPercent = data.kb_scrubbed;
        }
      },
      error: function(xhr, status, error) {
      }
    });
  },

  renderSubViews: function() {
    $(this.el).append(this.template({pool: this.pool}));
    this.subviews['pool-info'] = new PoolInfoModule({ model: this.pool });
    this.subviews['pool-usage'] = new PoolUsageModule({ model: this.pool });
    this.pool.on('change', this.subviews['pool-info'].render, this.subviews['pool-info']);
    this.pool.on('change', this.subviews['pool-usage'].render, this.subviews['pool-usage']);
    this.$('#ph-pool-info').append(this.subviews['pool-info'].render().el);
    this.$('#ph-pool-usage').append(this.subviews['pool-usage'].render().el);
    this.$('#ph-scrub-button').html(this.scrubTemplate({status: this.scrubStatus,
		  percent: this.scrubPercent}));
    this.attachActions();
  },

  attachActions: function() {
    var _this = this;
    this.$('#resize-pool-popup').click(function() {
      _this.disks.fetch({
        success: function(collection, response) {
          _this.$('#disks-to-add').html(_this.select_disks_template({disks: _this.disks, poolName: _this.poolName}));
          _this.$('#alert-msg').empty();
          $('#resize-pool-form').overlay().load();
        }});
    });
    this.$('#resize-pool').click(function() {
      var disk_names = [];
      var err_msg = "Please select atleast one disk";
      var n = _this.$(".disknew:checked").length;
      var m = _this.$(".diskadded:unchecked").length;
      if(n > 0){
        _this.$(".disknew:checked").each(function(i) {
          if (i < n) {
            disk_names.push($(this).val());
          }
        });
        $.ajax({
          url: '/api/pools/'+_this.pool.get('name')+'/add',
          type: 'PUT',
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify({"disks": disk_names}),
          success: function() {
            _this.$('#resize-pool-form').overlay().close();
            _this.pool.fetch();
          },
          error: function(request, status, error) {
            _this.$('#alert-msg').html("<font color='red'>"+request.responseText+"</font>");
          }
        });
      } else if(m > 0) {
        _this.$(".diskadded:unchecked").each(function(i) {
          if (i < m) {
            disk_names.push($(this).val());
          }
        });
        $.ajax({
          url: '/api/pools/'+_this.pool.get('name')+'/remove',
          type: 'PUT',
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify({"disks": disk_names}),
          success: function() {
            _this.$('#resize-pool-form').overlay().close();
            _this.pool.fetch();
          },
          error: function(request, status, error) {
            _this.$('#alert-msg').html("<font color='red'>"+request.responseText+"</font>");
          }
        });
      } else if(n <= 0) {
        _this.$('#alert-msg').html("<font color='red'>"+err_msg+"</font>");
      }
    });
    this.$('#resize-pool-form').overlay({ load: false });
  },

  deletePool: function() {
    var button = this.$('#delete-pool');
    if (buttonDisabled(button)) return false;
    if(confirm("Delete pool: "+ this.pool.get('name') + "... Are you sure?")){
      disableButton(button);
      $.ajax({
        url: "/api/pools/" + this.pool.get('name'),
        type: "DELETE",
        dataType: "json",
        data: { "name": this.pool.get('name') },
        success: function() {
          app_router.navigate('pools', {trigger: true});
        },
        error: function(xhr, status, error) {
          enableButton(button);
        }
      });
    }
  },

  scrubPoolStart: function() {
    $.ajax({
      url: '/api/pools/'+this.pool.get('name')+'/scrub',
      type: 'POST',
      success: function() {
        this.scrubStatus = 'started';
        this.scrubPercent = 0;
        this.$('#ph-scrub-button').html(this.scrubTemplate({status: this.scrubStatus,
            percent: this.scrubPercent}));
      },
      error: function(jqXHR) {
      }
    });
  },

  cleanup: function() {
    if (!_.isUndefined(this.statusIntervalId)) {
	window.clearInterval(this.statusIntervalId);
    }
  },

  scrubPoolRefresh: function() {
    this.getScrubStatus();
    this.$('#ph-scrub-button').html(this.scrubTemplate({status: this.scrubStatus,
        percent: this.scrubPercent}));
  },

});
