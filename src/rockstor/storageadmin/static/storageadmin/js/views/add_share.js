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
    this.pools = new PoolCollection();
    this.pools.pageSize = RockStorGlobals.maxPageSize;
    this.poolName = this.options.poolName;
    
  },

  render: function() {
    $(this.el).empty();
    this.template = window.JST.share_add_share_template;
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
         var foo = [];
        for (var i=0;i<2049;i++) {
          foo.push(i);
             }
        var step_values = ['1','500','1024','15',''];
         var slider = d3.slider().min(0).max(2048).tickValues([1,500,1024,1536,2048]).stepValues(foo).tickFormat(tickFormatter).callback(callback);
       // var slider = d3.slider().min(0).max(2048).tickValues([1,500,1024,1536,2048]).stepValues([1,50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000,1024,1229,1332,1434,1536,1639,1741,1844,1946,2048]).tickFormat(tickFormatter).callback(callback);
        d3.select('#slider').call(slider);
        
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
              alert(size);
              }else if(sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb'){
              size = size*1024*1024*1024;
              alert(size);
              }
              
              alert(size);
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

