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

/*
 * Add Share View 
 */

AddShareView = Backbone.View.extend({
  events: {
    "click #js-cancel": "cancel"
  },

  initialize: function() {
    var _this = this;
    this.pools = new PoolCollection();
    this.pools.pageSize = RockStorGlobals.maxPageSize;
    this.poolName = this.options.poolName;
    this.tickFormatter = function(d) {
      var formatter = d3.format(",.0f");
      if (d > 1024) {
        return formatter(d/(1024)) + " TB";
      } else {
        return formatter(d) + " GB";
      }
    }
    this.slider = null;
    this.sliderCallback = function(slider) {
      var value = slider.value();
      _this.$('#share_size').val(_this.tickFormatter(value));
    }
  },

  render: function() {
    $(this.el).empty();
    this.template = window.JST.share_add_share_template;
    var _this = this;
    this.pools.fetch({
      success: function(collection, response) {
        $(_this.el).append(_this.template({pools: _this.pools, poolName: _this.poolName}));

        _this.renderSlider(); 
        _this.$('#pool_name').change(function(){
          _this.renderSlider();
        });
      

        _this.$("#share_size").change(function(){
          var size = this.value;
          var sizeFormat = size.replace(/[^a-z]/gi, ""); 

          var size_array = size.split(sizeFormat)
          var size_value = size_array[0];

          if(sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb') {
            size_value = size_value*1024;
            _this.slider.setValue(parseInt(size)*1024);
          } else if (sizeFormat == 'GB' || sizeFormat == 'gb' || sizeFormat == 'Gb') {
            _this.slider.setValue(parseInt(size));
          } else {
            _this.slider.setValue(parseInt(size));
          }
        });

        $('#add-share-form :input').tooltip({placement: 'right'});
        
        $('#add-share-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
              share_name: 'required',
              share_size: {
                required: true,
              },
            },
            
            submitHandler: function() {
              var button = _this.$('#create_share');
              if (buttonDisabled(button)) return false;
              disableButton(button);
              var share_name = $('#share_name').val();
              var pool_name = $('#pool_name').val();
              var size = $('#share_size').val();
              var sizeFormat = size.replace(/[^a-z]/gi, ""); 
              var size_array = size.split(sizeFormat)
              var size_value = size_array[0];

              if(sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb') {
                size_value = size_value*1024*1024*1024;
              } else if (sizeFormat == 'GB' || sizeFormat == 'gb' || sizeFormat == 'Gb') {
                size_value = size_value*1024*1024;
              } else {
                size_value = size_value*1024*1024;
              }

              $.ajax({
                url: "/api/shares",
                type: "POST",
                dataType: "json",
                data: {sname: share_name, "pool": pool_name, "size": size_value},
                success: function() {
                  enableButton(button);
                  _this.$('#add-share-form :input').tooltip('hide');
                  app_router.navigate('shares', {trigger: true})
                },
                error: function(xhr, status, error) {
                  enableButton(button);
                },
              });
            }
        });
      }
    });
    return this;
  },

  renderSlider: function() {
    var pool_name = this.$('#pool_name').val();
    var selectedPool = this.pools.find(function(p) { return p.get('name') == pool_name; });
    var max = (selectedPool.get('free') + selectedPool.get('reclaimable')) / (1024*1024);
    var min = 0;
    var ticks = 3;
    var value = 1;
    var section = selectedPool.get('free')/(1024*1024);
    
    this.$('#slider').empty();
    this.slider = d3.slider2().min(min).max(max).ticks(ticks).tickFormat(this.tickFormatter).value(value).section(section).callback(this.sliderCallback);
    d3.select('#slider').call(this.slider);
  },

  cancel: function(event) {
    event.preventDefault();
    this.$('#add-share-form :input').tooltip('hide');
    app_router.navigate('shares', {trigger: true})
  }

});

