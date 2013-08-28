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

NfsShareClientUserView = Backbone.View.extend({
  initialize: function() {
    this.probe = this.options.probe;
    this.template = window.JST.probes_nfs_share_client_user;
    this.nfsAttrs = ["num_read", "num_write", "num_lookup"];
    this.treeType = "client";
    this.updateInterval = 5000; // update every updateInterval seconds
    this.ts = this.options.ts; // ISO format timestamp
    this.rawData = null; // data returned from probe backend
  },

  render: function() {
    
    $(this.el).html(this.template({probe: this.probe}));
    var _this = this;

    this.renderIntervalId = window.setInterval(function() {
      var data = _this.generateData();
      //var filteredData = _this.filterData(data, _this.treeType, _this.selAttrs, _this.numTop);
      //console.log(filteredData);
      _this.root = _this.createTree(data, _this.treeType, _this.nfsAttrs);
      console.log(_this.root);
      _this.renderViz(_this.root);
    }, this.updateInterval);
    
    return this;
  },

  // gets data every updateInterval seconds and renders it
  renderViz: function() {
  },

  cleanup: function() {
    if (!_.isUndefined(this.renderIntervalId) && 
    !_.isNull(this.renderIntervalId)) {
      window.clearInterval(this.renderIntervalId);
    }
  },

  createTree: function(data, treeType, attrList) {
    var _this = this;
    var root = null;
    // types of nodes at level 1 and 2 of the tree
    var typeL1 = treeType == "client" ? "client" : "uid";
    var typeL2 = "share";
    root = this.createNode("root", "root");
    _.each(data, function(d) {
      var nodeL1 = _this.findOrCreateNodeWithName(
        root.children, d[typeL1], typeL1 
      );
      nodeL1.id = d[typeL1];
      var nodeL2 = _this.findOrCreateNodeWithName(
        nodeL1.children, d[typeL2], typeL2
      );
      nodeL2.id = d[typeL2] + "_" + d[typeL1];
      // update attributes - there may be multiple data points
      // for each node type, so add the attr values
      _.each(attrList, function(a) {
        root[a] = _.isUndefined(root[a]) ? d[a] : root[a] + d[a];
        nodeL1[a] = _.isUndefined(nodeL1[a]) ? d[a] : nodeL1[a] + d[a];
        nodeL2[a] = _.isUndefined(nodeL2[a]) ? d[a] : nodeL2[a] + d[a];
      });
    });
    return root;
  },

  findNodeWithName: function(nodeList, name) {
    return _.find(nodeList, function(node) {
      return node.name == name;
    });
  },

  findNodeWithId: function(nodeList, id) {
    return _.find(nodeList, function(node) {
      return node.id == id;
    });
  },

  findOrCreateNodeWithName: function(nodeList, name, nodeType) {
    var node = this.findNodeWithName(nodeList, name);
    if (_.isUndefined(node)) {
      node = this.createNode(name, nodeType);
      nodeList.push(node);
    }
    return node;
  },

  createNode: function(name, nodeType) {
    return {name: name, nodeType: nodeType, children: []};
  },
  
  filterData: function(data, treeType, selAttrs, n) {
    var list = [];
    _.each(data, function(d) {
      // find corresp obj in list (share or client)
      var e = _.find(list, function(el) {
        return el[treeType] == d[treeType];
      });
      if (_.isUndefined(e)) {
        e = {};
        e[treeType] = d[treeType];
        e.value = 0;
        list.push(e);
      }
      // add attr value 
      _.each(selAttrs, function(attr) {
        e.value = e.value + d[attr];
      });
    });
    list = (_.sortBy(list, function(e) { 
      return e.value; 
    })).reverse().slice(0,n);
    return _.filter(data, function(d) {
      return _.find(list, function(e) {
        return e[treeType] == d[treeType];
      });
    });
  },

  generateData: function() {
    var data = [];
    for (i=1; i<=3; i++) {
      var ip = "10.0.0." + i;
      for (j=1; j<=2; j++) {
        var share = "share_" + j;
        data.push({
          share: share,
          client: ip,
          num_read: 5 + Math.floor(Math.random() * 5),
          num_write: 1 + Math.floor(Math.random() * 5),
          num_lookup: 1 + Math.floor(Math.random() * 5),
        });
      }
    }
    var ipRandom1 = "10.0.0." + (5 + (Math.floor(Math.random() * 5)));
    var share1 = "share_1";
    var ipRandom2 = "10.0.0." + (10 + (Math.floor(Math.random() * 5)));
    var share2 = "share_2";
    var ipRandom3 = "10.0.0." + (15 + (Math.floor(Math.random() * 5)));
    var share3 = "share_3";
    data.push({
      share: share1,
      client: ipRandom1,
      num_read: 5 + Math.floor(Math.random() * 5),
      num_write: 1 + Math.floor(Math.random() * 5),
      num_lookup: 1 + Math.floor(Math.random() * 5),
    });
    data.push({
      share: share2,
      client: ipRandom2,
      num_read: 5 + Math.floor(Math.random() * 5),
      num_write: 1 + Math.floor(Math.random() * 5),
      num_lookup: 1 + Math.floor(Math.random() * 5),
    });
    data.push({
      share: share3,
      client: ipRandom3,
      num_read: 5 + Math.floor(Math.random() * 5),
      num_write: 1 + Math.floor(Math.random() * 5),
      num_lookup: 1 + Math.floor(Math.random() * 5),
    });
    return data;
  },


  // sorts children of root by attr
  sortTree: function(root, attr) {
    newChildren = _.sortBy(root.children, function(node) {
      return node[attr];
    }).reverse();
    root.children = newChildren;
  },

  // creates new root with n of oldroots children
  getTopN: function(root, n) {
    var newRoot = this.copyRoot(root, this.nfsAttrs);
    if (root.children.length > 0) {
      for (i=0; i<n; i++) {
        newRoot.children[i] = root.children[i];
        if (i == root.children.length-1) break;
      }
    }
    return newRoot;
  },

  findNode: function(root, id) {
    var n = null;
    if (root.id == id) {
      n = root;
    } else if (root.children) {
      for (var i=0; i<root.children.length; i++) {
        n = this.findNode(root.children[i], id);
        if (!_.isNull(n)) break;
      }
    } 
    return n;
  },

  createRoot: function(treeType, nfsAttrs) {
    var root = {};
    if (treeType == 'client') {
      root.name = 'clients';
      root.displayName = 'All clients';
      root.treeType = treeType;
      root.type = 'root';
      root.label = 'clients';
      root.children = [];
      _.each(nfsAttrs, function(attr) {
        root[attr] = 0;
      });
    }
    return root;
  },

  // Accepts date string in ISO 8601 format and returns 
  // date string 'dMs' milliseconds later
  getDateAfter: function(s, dMs) {
    var t1 = moment(s);
    return moment(t1).add("ms",dMs).toISOString();
  },

  // adds t1 and t2 to url, t2 is 'duration' seconds after t1
  appendTimeIntervaltoUrl: function(url, t1, duration) {
    var t2 = this.getDateAfter(t1, duration*1000);
    return url + "&t1=" + t1 + "&t2=" + _this.ts;
  }

});

RockStorProbeMap.push({
  name: 'nfs-share-client-user',
  view: 'NfsShareClientUserView',
  description: 'NFS Share, Client, User Distribution',
});



