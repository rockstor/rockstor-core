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
    this.resize_pool_edit_template = window.JST.pool_resize_pool_edit;
    this.resize_pool_info_template = window.JST.pool_resize_pool_info;
    this.compression_info_template = window.JST.pool_compression_info;
    this.compression_info_edit_template = window.JST.pool_compression_info_edit;
    this.pool = new Pool({poolName: this.poolName});
    // create poolscrub models
    this.poolscrubs = new PoolscrubCollection([],{snapType: 'admin'});
    this.poolscrubs.pageSize = 5;
    this.poolscrubs.setUrl(this.poolName);
    // create pool re-balance models
    this.poolrebalances = new PoolRebalanceCollection([],{snapType: 'admin'});
    this.poolrebalances.pageSize = 5;
    this.poolrebalances.setUrl(this.poolName);

    this.dependencies.push(this.pool);
    this.dependencies.push(this.poolscrubs);
    this.dependencies.push(this.poolrebalances);
    this.disks = new DiskCollection();
    this.disks.pageSize = RockStorGlobals.maxPageSize;
    this.cOpts = {'no': 'Dont enable compression', 'zlib': 'zlib', 'lzo': 'lzo'};
    this.cView = this.options.cView;
  },

  events: {
    'click #delete-pool': 'deletePool',
    "click #js-resize-pool": "resizePool",
    "click #js-submit-resize": "resizePoolSubmit",
    "click #js-resize-cancel": "resizePoolCancel",
   "click #js-edit-compression": "editCompression",
    "click #js-edit-compression-cancel": "editCompressionCancel",
    "click #js-submit-compression": "updateCompression",
  },

  render: function() {
    this.fetch(this.renderSubViews, this);
    return this;
  },

  renderSubViews: function() {
    $(this.el).html(this.template({pool: this.pool}));
    this.subviews['pool-info'] = new PoolInfoModule({ model: this.pool });
    this.subviews['pool-usage'] = new PoolUsageModule({ model: this.pool });
    this.subviews['pool-scrubs'] = new PoolScrubTableModule({
    	poolscrubs: this.poolscrubs,
        pool: this.pool,
        parentView: this
    });
    this.subviews['pool-rebalances'] = new PoolRebalanceTableModule({
    	poolrebalances: this.poolrebalances,
        pool: this.pool,
        parentView: this
    });
    this.pool.on('change', this.subviews['pool-info'].render, this.subviews['pool-info']);
    this.pool.on('change', this.subviews['pool-usage'].render, this.subviews['pool-usage']);
    this.poolscrubs.on('change', this.subviews['pool-scrubs'].render, this.subviews['pool-scrubs']);
    this.$('#ph-pool-info').html(this.subviews['pool-info'].render().el);
    this.$('#ph-pool-usage').html(this.subviews['pool-usage'].render().el);
    this.$('#ph-pool-scrubs').html(this.subviews['pool-scrubs'].render().el);
    this.$('#ph-pool-rebalances').html(this.subviews['pool-rebalances'].render().el);
    this.$('#ph-resize-pool-info').html(this.resize_pool_info_template({pool: this.pool}));
   if (!_.isUndefined(this.cView) && this.cView == 'edit') {
      this.$('#ph-compression-info').html(this.compression_info_edit_template({
        pool: this.pool,
        cOpts: this.cOpts
      }));
      this.showCompressionTooltips();
    } else {
      this.$('#ph-compression-info').html(this.compression_info_template({pool: this.pool}));
    }
    this.$("ul.css-tabs").tabs("div.css-panes > div");
    if (!_.isUndefined(this.cView) && this.cView == 'edit') {
      //console.log(this.$('#ph-compression-info').offset().top);
      //$('#content').scrollTop(this.$('#ph-compression-info').offset().top);
    }
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
  
  resizePool: function(event) {
	 var _this = this;
    event.preventDefault();
    _this.disks.fetch({
        success: function(collection, response) {
          _this.$('#ph-resize-pool-info').html(_this.resize_pool_edit_template({disks: _this.disks, poolName: _this.poolName}));
            }});
       
  },
  
  resizePoolSubmit: function(event) {
	    event.preventDefault();
	    var button = this.$('#js-submit-resize');
	    if (buttonDisabled(button)) return false;
	    if(confirm(" Are you sure to Resize the pool?")){
	    disableButton(button);
	  var _this = this;
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
        	
          _this.pool.fetch();
          _this.renderSubViews();
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
            _this.pool.fetch();
            _this.renderSubViews();
          },
          error: function(request, status, error) {
            _this.$('#alert-msg').html("<font color='red'>"+request.responseText+"</font>");
          }
        });
      } else if(n <= 0) {
        _this.$('#alert-msg').html("<font color='red'>"+err_msg+"</font>");
      }
  }
     // this.$('#ph-resize-pool-info').html(this.resize_pool_info_template({pool: this.pool}));
		  },
  
 resizePoolCancel: function(event) {
	    event.preventDefault();
	//    this.hideCompressionTooltips();
	    this.$('#ph-resize-pool-info').html(this.resize_pool_info_template({pool: this.pool}));
	  },
	  
  editCompression: function(event) {
    event.preventDefault();
    this.$('#ph-compression-info').html(this.compression_info_edit_template({
      pool: this.pool,
      cOpts: this.cOpts
    }));
    this.showCompressionTooltips();
  },

  editCompressionCancel: function(event) {
    event.preventDefault();
    this.hideCompressionTooltips();
    this.$('#ph-compression-info').html(this.compression_info_template({pool: this.pool}));
  },

  updateCompression: function(event) {
    var _this = this;
    event.preventDefault();
    var button = this.$('#js-submit-compression');
    if (buttonDisabled(button)) return false;
    disableButton(button);
    $.ajax({
      url: "/api/pools/" + this.pool.get('name') + '/remount',
      type: "PUT",
      dataType: "json",
      data: {
        "compression": this.$('#compression').val(),
        "mnt_options": this.$('#mnt_options').val(),
      },
      success: function() {
        _this.hideCompressionTooltips();
        _this.pool.fetch({
          success: function(collection, response, options) {
            _this.cView = 'view';
            _this.renderSubViews();
          }
        });
      },
      error: function(xhr, status, error) {
        enableButton(button);
      }
    });
  },

  showCompressionTooltips: function() {
    this.$('#ph-compression-info #compression').tooltip({
      html: true,
      placement: 'top',
      title: "Choose a compression algorithm for this Pool.<br><strong>zlib: </strong>slower but higher compression ratio.<br><strong>lzo: </strong>faster compression/decompression, but ratio smaller than zlib.<br>Enabling compression at the pool level applies to all Shares carved out of this Pool.<br>Don't enable compression here if you like to have finer control at the Share level.<br>You can change the algorithm, disable or enable it later, if necessary."
    });
    this.$('#ph-compression-info #mnt_options').tooltip({ placement: 'top' });
  },

  hideCompressionTooltips: function() {
    this.$('#ph-compression-info #compression').tooltip('hide');
    this.$('#ph-compression-info #mnt_options').tooltip('hide');
  },

  cleanup: function() {
    if (!_.isUndefined(this.statusIntervalId)) {
	window.clearInterval(this.statusIntervalId);
    }
  }
});
