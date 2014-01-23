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

PluginsView = RockstoreLayoutView.extend({
  events: {
    "click button[data-action=install]": "installPlugin"
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.plugins_plugins;
    this.plugins = new PluginCollection();
    this.installedPlugins = new InstalledPluginCollection();
    this.dependencies.push(this.plugins);
    this.dependencies.push(this.installedPlugins);
  },

  render: function() {
    this.fetch(this.renderPlugins, this);
    return this;
  },

  renderPlugins: function() {
    var _this = this;
    $(this.el).html(this.template({
      plugins: this.plugins,                             
      installedPlugins: this.installedPlugins
    }));
    this.$('#plugin-install-modal').modal({
      keyboard: false,
      backdrop: 'static',
      show: false
    });
    this.$('#plugin-key-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        activation_key: 'required',
      },
      submitHandler: function() {
        var button = _this.$('#plugin-install-form-submit');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        _this.$('#plugin-install-modal #installing-msg').html('<h4>Installing plugin ' + _this.selectedPluginName + '. The browser window will refresh after the plugin is installed</h4><br><div style="text-align: center"><img src="/static/storageadmin/img/ajax-loader-big.gif"></div>');
        
        $.ajax({
          url: "/api/installed_plugins", 
          type: "POST",
          data: {plugin_name: _this.selectedPluginName},
          dataType: "json",
          global: false, // dont show global loading indicator and error
          success: function(data, status, xhr) {
            _this.$('#plugin-install-modal #installing-msg').empty();
            _this.$('#plugin-install-modal').modal('hide');
            _this.reloadWindow();
          },
          error: function(xhr, status, error) {
            _this.$('#plugin-install-modal #installing-msg').empty();
            var errJson = getXhrErrorJson(xhr);
            detail = errJson.detail;
            _this.$('#plugin-install-form .messages').html(detail);
          }
        });
        return false;
      },
      
    });
  },

  installPlugin: function(event) {
    var _this = this;
    var button = $(event.currentTarget);
    this.selectedPluginName = button.attr('data-name');
    this.$('#plugin-install-modal').modal('show');
  },

  reloadWindow: function() {
    location.reload(true);
  }
});

