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

PoolDetailsLayoutView = RockstoreLayoutView.extend({

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.poolName = this.options.poolName;
    this.template = window.JST.pool_pool_details_layout;
    this.select_disks_template = window.JST.disk_select_disks_template;

    this.pool = new Pool({poolName: this.poolName});
    this.dependencies.push(this.pool);

    this.disks = new DiskCollection();
  },

  events: {
    'click #delete-pool': 'deletePool'
  },

  render: function() {
    this.fetch(this.renderSubViews, this);
    return this;

  },

  renderSubViews: function() {
    $(this.el).append(this.template({pool: this.pool}));
    this.subviews['pool-info'] = new PoolInfoModule({ model: this.pool });
    this.subviews['pool-usage'] = new PoolUsageModule({ model: this.pool });
    this.pool.on('change', this.subviews['pool-info'].render, this.subviews['pool-info']);
    this.pool.on('change', this.subviews['pool-usage'].render, this.subviews['pool-usage']);
    this.$('#ph-pool-info').append(this.subviews['pool-info'].render().el);
    console.log('rendered pool info module');
    this.$('#ph-pool-usage').append(this.subviews['pool-usage'].render().el);
    console.log('rendered pool usage module');
    this.attachActions();
  },

  
  
  
  attachActions: function() {
    var _this = this;
    this.$('#resize-pool-popup').click(function() {
      _this.disks.fetch({
        success: function(collection, response) {
          console.log('got disks');
          _this.$('#disks-to-add').html(_this.select_disks_template({disks: _this.disks}));
          _this.$('#alert-msg').empty();
          _this.$('#resize-pool').click(function() {
            var disk_names = '';
            var err_msg = "Please select atleast one disk";
            var n = $("input:checked").length;
            if(n > 0){
            $("input:checked").each(function(i) {
              if (i < n-1) {
                disk_names += $(this).val() + ',';
              } else {
                disk_names += $(this).val();	  
              }
            });
            console.log(disk_names);
            $.ajax({
              url: "/api/pools/"+_this.pool.get('name')+'/add/',
              type: "PUT",
              dataType: "json",
              data: {"disks": disk_names},
              success: function() {
                _this.$('#resize-pool-form').overlay().close();
                _this.pool.fetch();
              },
              error: function(request, status, error) {
            	 _this.$('#alert-msg').html("<font color='red'>"+request.responseText+"</font>");
              }
            });
          }else{
        	  _this.$('#alert-msg').html("<font color='red'>"+err_msg+"</font>");
          }
          });
          $('#resize-pool-form').overlay().load();
          
        }});
    });
    _this.$('#resize-pool-form').overlay({ load: false });
    

  },

  deletePool: function() {
    var _this = this;
    console.log('deleting ' + this.pool.get('name'));
    var button = this.$('#delete-pool');
    if (buttonDisabled(button)) return false;
    disableButton(button);
    $.ajax({
      url: "/api/pools/" + this.pool.get('name') + "/",
      type: "DELETE",
      dataType: "json",
      data: { "name": this.pool.get('name'), "disks": "foo", "raid_level": "foo" }
    }).done(function() {
      app_router.navigate('pools', {trigger: true});
    }).fail(function(request, status, error) {
        showError(request.responseText); 
    }).always(function() {
      enableButton(button);
    });

  }



});

