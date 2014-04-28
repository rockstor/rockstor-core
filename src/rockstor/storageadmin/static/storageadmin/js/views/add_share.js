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
         var err_msg = 'Size can be GB/gb/Gb or TB/tb/Tb';
         var size_err_msg = function() {
          return err_msg;
           }
           
     //   $("#slider-size").simpleSlider({
     //      range: [0,2049],
     //       step: '10',
     //       value: 0,
     //  });

        $.validator.addMethod('validateShareSize', function(value) {
        
            var size = $('#share_size').val();
            var sizeFormat = size.replace(/[^a-z]/gi, ""); 
            if(sizeFormat != 'GB' && sizeFormat != 'gb' && sizeFormat != 'Gb' && sizeFormat != 'TB' && sizeFormat != 'Tb' && sizeFormat != 'tb'){
                err_msg = 'Size can be GB/gb/Gb or TB/tb/Tb';
                return false;
              }
             return true;
          }, size_err_msg);

     //   $("#slider-size").bind("slider:changed", function (event, data) {
     //       The currently selected value of the slider
     //       if(data.value < 1024){
     //       $("#share_size").val((data.value).toFixed(2)+"GB");
     //       }else{
     //           $("#share_size").val(((data.value)/1024).toFixed(2)+"TB");
     //        }
     //       });
     //   $("#share_size").change(function(){
     //   var size = this.value;
     //   var sizeFormat = size.replace(/[^a-z]/gi, ""); 
        
     //   var size_array = size.split(sizeFormat)
     //   var size_value = size_array[0];
        
     //   if(sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb'){
     //      size_value = size_value*1024;
     //      $("#slider-size").simpleSlider("setValue",parseInt(size_value));
     //      }else{
     //      $("#slider-size").simpleSlider("setValue",parseInt(size));
     //      }
        
     //   });
     
        
     
        $("#Slider1").slider({ from: 1, to: 2048, step: 2, round: 1, dimension: "&nbsp;GB", skin: "round" });
        
        $("#Slider1").bind("slider:changed", function (event, data) {
            if(data.value < 1024){
            $("#share_size").val((data.value).toFixed(2)+"GB");
            }else{
                $("#share_size").val(((data.value)/1024).toFixed(2)+"TB");
             }
            });
            
              $("#share_size").change(function(){
          var size = this.value;
          var sizeFormat = size.replace(/[^a-z]/gi, ""); 
        
          var size_array = size.split(sizeFormat)
          var size_value = size_array[0];
        
        if(sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb'){
           size_value = size_value*1024;
           $("#Slider1").slider("value",parseInt(size_value));
           }else{
           $("#Slider1").slider("value",parseInt(size));
           }
        
        });
     
        
        $('#add-share-form :input').tooltip({placement: 'right'});
        
        $('#add-share-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
              share_name: 'required',
              share_size: "validateShareSize",
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
              var size_value = size_array[0];    
              
              if(sizeFormat == 'GB' || sizeFormat == 'gb' || sizeFormat == 'Gb'){
               size_value = size_value*1024*1024;
                }else if(sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb'){
               size_value = size_value*1024*1024*1024;
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

  cancel: function(event) {
    event.preventDefault();
    this.$('#add-share-form :input').tooltip('hide');
    app_router.navigate('shares', {trigger: true})
  }

});

