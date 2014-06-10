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

AddShareView =  RockstorLayoutView.extend({
  events: {
    "click #js-cancel": "cancel"
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.share_add_share_template;
   
    this.pools = new PoolCollection();
    this.pools.pageSize = RockStorGlobals.maxPageSize;
    this.poolName = this.options.poolName;
    this.dependencies.push(this.pools);
    
  },
  
   render: function() {
   
   var _this = this;
    this.pools.fetch({
      success: function(collection, response) {
        $(_this.el).append(_this.template({pools: _this.pools, poolName: _this.poolName}));
         
        
        $('#add-share-form :input').tooltip({placement: 'right'});
        
        // tick formatter
        var formatter = d3.format(",.2f");
        var tickFormatter = function(d) {
        if(d < 1024){
        return formatter(d) + " GB";
          }else{
        return formatter(d/1024) + " TB";
          }
        }
        
         var callback = function(slider) {
        // get current slider value
         var value = slider.value();
         if(value < 1024)
          {
            $("#share_size").val(value.toFixed(2)+"GB");
            }else
            {
            $("#share_size").val(((value)/1024).toFixed(2)+"TB");
            }
          }   
          
         
          var slider_poolsize = function(){  
          var pool_name = $('#pool_name').val();
          var selectedPool = _this.pools.find(function(p) { return p.get('name') == pool_name; });
          var maxPoolSize =  (selectedPool.get('size')- selectedPool.get('usage'))/1024;
          
          var foo = [];
          for (var i=0;i<= maxPoolSize;i++) {
          foo.push(i);
             }
             
          var foo2 = [];
          var step = maxPoolSize/5;
          for (var i=0;i<=maxPoolSize;i=i+step) {
          foo2.push(i); 
             }
          
          var slider = d3.slider().min(0).max(maxPoolSize).tickValues(foo2).stepValues(foo).tickFormat(tickFormatter).callback(callback);
          d3.select('#slider').call(slider);
          
          };
          
          slider_poolsize();
          
          $('#pool_name').change(function(){
          slider_poolsize();
           });
          
          
        $("#share_size").change(function(){
          var size = this.value;
          var sizeFormat = size.replace(/[^a-z]/gi, ""); 
        
          var size_array = size.split(sizeFormat)
          var size_value = size_array[0];
          
           if(sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb'){
           size_value = size_value*1024;
           slider.setValue(parseInt(size_value));
           }else{
           slider.setValue(parseInt(size));
           }
                
        });
        
        $('#add-share-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
              share_name: 'required',
              share_size: {
                required: true,
                
              },
            },
            errorPlacement: function(error, element) {
              if (element.attr("name") == "share_size") {
                // insert error for share size after the size format field.
                error.insertAfter("#size_format");
              } else {
                error.insertAfter(element);
              }
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
              var size = size_array[0];
             
              if(sizeFormat == 'GB' || sizeFormat == 'gb' || sizeFormat == 'Gb'){
              size = size*1024*1024;
              }else if(sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb'){
              size = size*1024*1024*1024;
              }
              
              $.ajax({
                url: "/api/shares",
                type: "POST",
                dataType: "json",
                data: {sname: share_name, "pool": pool_name, "size": size},
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

  cancel: function(event) {
    event.preventDefault();
    this.$('#add-share-form :input').tooltip('hide');
    app_router.navigate('shares', {trigger: true})
  }

});

