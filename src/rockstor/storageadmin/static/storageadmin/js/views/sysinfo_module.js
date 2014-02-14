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

SysInfoModule = RockstoreModuleView.extend({
  
  initialize: function() {
    logger.debug('in SysInfoModule initialize');
    this.template = window.JST.home_sysinfo;
    this.module_name = 'sysinfo';
  },

  render: function() {
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      model: this.model
    }));
    var _this = this;
    RockStorSocket.addListener(function(load_avg) {
      if (load_avg.length > 0) {
        console.log('updating load avg');
        console.log(load_avg[load_avg.length-1].load_1);
        _this.$('#load-avg').html(load_avg[load_avg.length-1].load_1);
      }
    }, this, 'load_avg');
    return this;
  }

});
