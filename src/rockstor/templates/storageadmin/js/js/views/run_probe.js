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

RunProbeView = RockstoreModuleView.extend({
  events: {
    "click #js-cancel": "cancel"
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.probes_run_probe;
    this.probeTemplates = new ProbeTemplateCollection();
    this.dependencies.push(this.probeTemplates);
  },

  render: function() {
    this.fetch(this.renderRunProbe, this);
    return this;
  },
  
  renderRunProbe: function() {
    var _this = this;
    $(this.el).append(this.template({
      probeTemplates: this.probeTemplates
    }));
    this.$("#probe-create-form").validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        probe_name: "required"
      },
      submitHandler: function() {
        var probeName = _this.$("#probe-type").val();
        var displayName = _this.$("#probe-name").val();
        $.ajax({
          url: "/api/sm/sprobes/" + probeName + "?format=json",
          type: 'POST',
          data: { display_name: displayName },
          dataType: "json",
          global: false, // dont show global loading indicator
          success: function(data, textStatus, jqXHR) {
            app_router.navigate('#analytics', {trigger: true});
          },
          error: function(jqXHR, textStatus, error) {
            var msg = parseXhrError(jqXHR)
            _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
          }
        });
        return false;
      }
    });
  },

  cancel: function() {
    app_router.navigate('#analytics', {trigger: true});
  } 

});

