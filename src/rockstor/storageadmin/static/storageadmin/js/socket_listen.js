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

var RockStorSocket = {};
RockStorSocket.handlerMap = {}; // initialize handler array

RockStorSocket.addListener = function(fn, fn_this, key) {
  RockStorSocket.handlerMap[key] = {fn: fn, fn_this: fn_this}; 
};

RockStorSocket.removeAllListeners = function() {
  _.each(_.keys(RockStorSocket.handlerMap), function(key) {
    delete RockStorSocket.handlerMap[key];
  });
};

RockStorSocket.msgHandler = function(data) {
  logger.debug('received msg');
  msg_data = JSON.parse(data.msg);
  _.each(_.keys(RockStorSocket.handlerMap), function(key) {
    if (!_.isNull(msg_data[key]) && !_.isUndefined(msg_data[key])) {
      var obj = RockStorSocket.handlerMap[key];
      obj.fn.call(obj.fn_this, msg_data[key]); 
    }
  });
};

