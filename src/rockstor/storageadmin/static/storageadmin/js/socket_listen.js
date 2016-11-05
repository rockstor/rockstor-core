/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
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

// Connect globally to sysinfo as the information is in the breadcrumb
RockStorSocket.sysinfo = io.connect('/sysinfo', {
    'secure': true,
    'force new connection': true
});

// Add the function and context to be fired when a message comes in
RockStorSocket.addListener = function(fn, fn_this, nsp_event) {
    RockStorSocket.handlerMap[nsp_event] = {
        fn: fn,
        fn_this: fn_this
    };
    var namespace = nsp_event.split(':')[0];
    var namespace_event = nsp_event.split(':')[1];
    RockStorSocket[namespace].on(namespace_event, RockStorSocket.msgHandler);
};

// Disconnect everything.
RockStorSocket.removeAllListeners = function() {
    _.each(_.keys(RockStorSocket.handlerMap), function(key) {
        delete RockStorSocket.handlerMap[key];
    });
};

RockStorSocket.removeOneListener = function(namespace) {
    RockStorSocket[namespace].disconnect();
};

// Fire appropriate callback given message
RockStorSocket.msgHandler = function(data) {
    var obj = RockStorSocket.handlerMap[data.key];
    if (!_.isNull(obj) && !_.isUndefined(obj)) {
        obj.fn.call(obj.fn_this, data.data);
    }
};
