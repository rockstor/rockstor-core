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
  },

  installPlugin: function(event) {
    var _this = this;
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    disableButton(button);
    this.$('#plugin-install-modal').modal('show');
    var pluginName = button.attr('data-name');
    $.ajax({
      url: "/api/installed_plugins", 
      type: "POST",
      data: {plugin_name: pluginName},
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        _this.$('#plugin-install-modal').modal('hide');
        _this.reloadWindow();
      },
      error: function(xhr, status, error) {

      }
    });

  },

  reloadWindow: function() {
    location.reload(true);
  }
});

