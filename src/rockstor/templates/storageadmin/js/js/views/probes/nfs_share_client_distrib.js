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

NfsShareClientDistribView = Backbone.View.extend({
  initialize: function() {
    this.probe = this.options.probe;
    this.template = window.JST.probes_nfs_share_client_distrib;
    this.nfsAttrs = ["num_read", "num_write", "num_lookup"];

    this.m = [20, 100, 20, 20]; 
    this.w = 400 - this.m[1] - this.m[3],
    this.h = 350 - this.m[0] - this.m[2];

    this.d3tree = d3.layout.tree().size([this.h, this.w]);

    this.diagonal = d3.svg.diagonal()
    .projection(function(d) { return [d.y, d.x]; });

    this.numTop = 5; // no of top children to select;
    this.treeType = "client";
    this.selectedNode = null;
    this.tsN = null;
    this.updateInterval = 5; // update every updateInterval seconds
    this.ts = this.options.ts; // ISO format timestamp
    this.rawData = null; // data returned from probe backend

    //this.fullTree = null;
    //this.prevTree = null;
    //this.currentTree = null;
    
    //this.clientTree = null;
    //this.shareTree = null;
    
  },

  render: function() {
    
    $(this.el).html(this.template({probe: this.probe}));
    var _this = this;

    this.$(".selectedAttr").click(function() {
      var val = $(this).val();
      console.log(val + " clicked");
      if ($(this).is(':checked')) {
        if (_this.selAttrs.indexOf(val) == -1) {
          _this.selAttrs.push(val);
        }
      } else {
        var i = _this.selAttrs.indexOf(val) 
        if (i != -1) {
          _this.selAttrs.splice(i, 1);
        }
      }
      console.log(_this.selAttrs);
      _this.$("#selectedAttrs").html(_this.selAttrs.join(","));
    });

    this.$("input:radio[name=selectedRoot]").click(function() {
      var value = $(this).val();
      console.log("root  = " + value);
      if (value == "Clients") {
        _this.$("#selectedRootName").html("Clients");
        _this.$("#selectedChildName").html("Shares");
      } else {
        _this.$("#selectedRootName").html("Shares");
        _this.$("#selectedChildName").html("Clients");
      }
      console.log("setting treeType to " + _this.treeType);
      _this.treeType = $(this).attr("data-treetype");
    });
    
    this.vis = d3.select(this.el).select("#nfs-share-client-graph").append("svg:svg")
    .attr("width", this.w + this.m[1] + this.m[3])
    .attr("height", this.h + this.m[0] + this.m[2])
    .append("svg:g")
    .attr("transform", "translate(" + this.m[3] + "," + this.m[0] + ")");
   
    if (this.probe.get("state") == "running") {
      this.updateAndRenderViz();
    } else if (this.probe.get("state") == "stopped") {
      this.renderViz();
    }

    /*
    this.renderIntervalId = window.setInterval(function() {
      var data = _this.generateData();
      var filteredData = _this.filterData(data, _this.treeType, _this.selAttrs, _this.numTop);
      //console.log(filteredData);
      _this.root = _this.createTree(filteredData, _this.treeType, _this.nfsAttrs);
      _this.displayTree(_this.root);
    }, 5000);
    */
    
    /*
    this.renderIntervalId = window.setInterval(function() {
      $.ajax({
        url: dataUrl,
        type: "GET",
        dataType: "json",
        success: function(data, textStatus, jqXHR) {
          console.log("data length is " + data.length);
          console.log("ts is "  + _this.tsN);
          if (data.length > 0 && _.isNull(_this.tsN)) {
            console.log("got data length > 0");
            console.log(data[0]);
            _this.tsN = (new Date(data[0].ts)).getTime();
          }
          _this.fullTree = _this.generateTree(data, "client");
          _this.sortTree(_this.fullTree, _this.selectedAttr);
          _this.currentTree = _this.getTopN(_this.fullTree, 5);
          console.log("current tree is ");
          console.log(_this.currentTree);
          _.each(_this.currentTree.children, function(d) {
            _this.toggleAll(d);
          });
          //_this.currentTree.children.forEach(_this.toggleAll);
          _this.toggleCopy(_this.prevTree, _this.currentTree);
          _this.displayTree(_this.currentTree);
          if (_.isNull(_this.selectedNode)) {
            _this.selectedNode = _this.currentTree;
          } else {
            _this.setSelectedNode(_this.selectedNode.name);
          }
          _this.updateDetail(_this.selectedNode, _this.selectedAttr);
          _this.prevTree = _this.currentTree;
          if (!_.isNull(_this.tsN)) {
            _this.tsN = _this.tsN + 1000*5;
          }
        },
        error: function(request, status, error) {
          logger.debug(error);
        }
      });

    }, 5000);
    */

    return this;
  },

  // gets data every updateInterval seconds and renders it
  updateAndRender: function() {
    // set t1 and t2 for dataUrl
    var dataUrl = this.appendTimeIntervaltoUrl(
      this.probe.dataUrl(),
      this.ts, 
      this.updateInterval
    );
    console.log("dataUrl is " + dataUrl); 
    // update current timestamp by updateInterval
    this.ts = this.getDateAfter(this.ts, this.updateInterval*1000);
    // get data and render every updateInterval seconds
    var _this = this;
    this.renderIntervalId = window.setInterval(function() {
      $.ajax({
        url: dataUrl,
        type: "GET",
        dataType: "json",
        success: function(data, textStatus, jqXHR) {
          var filteredData = _this.filterData(
            data, _this.treeType, _this.selAttrs, _this.numTop
          );
          _this.root = _this.createTree(
            filteredData, _this.treeType, _this.nfsAttrs
          );
          _this.renderViz();
        },
        error: function(request, status, error) {
          console.log(error);
        }
      });
    }, this.updateInterval);
  },

  renderViz: function() {
    this.displayTree(this.root);
  },

  cleanup: function() {
    if (!_.isUndefined(this.renderIntervalId) && 
    !_.isNull(this.renderIntervalId)) {
      window.clearInterval(this.renderIntervalId);
    }
  },

  /////
  createTree: function(data, treeType, attrList) {
    var _this = this;
    var root = null;
    if (treeType == "client") {
      root = this.createNode("root", null, attrList, treeType);
      _.each(data, function(d) {
        // get client node
        var client = _this.findOrCreateNodeWithName(
        root.children, d.client, "client", d, attrList, treeType)
        // get share node
        var share = _this.findOrCreateNodeWithName(
        client.children, d.share, "share", d, attrList, treeType);
        // update attributes - there may be multiple data points
        // for each client or share, so add the attr values
        _.each(attrList, function(attr) {
          share[attr] = share[attr] + d[attr];
          client[attr] = client[attr] + d[attr];
        });
      });
    } else if (treeType == "share") {
      root = this.createNode("root", null, attrList, treeType);
      _.each(data, function(d) {
        // get share node
        var share = _this.findOrCreateNodeWithName(root.children,
        d.share, "share", d, attrList, treeType);
        // get client node
        var client = _this.findOrCreateNodeWithName(share.children, 
        d.client, "client", d, attrList, treeType);
        
        // update attributes - there may be multiple data points
        // for each client or share, so add the attr values
        _.each(attrList, function(attr) {
          share[attr] = share[attr] + d[attr];
          client[attr] = client[attr] + d[attr];
        });
      });

    }
    // update attributes for root 
    _.each(root.children, function(c) {
      _.each(attrList, function(attr) {
        root[attr] = root[attr] + c[attr];
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

  findOrCreateNodeWithName: function(nodeList, name, nodeType, 
  d, attrList, treeType) {
    var node = this.findNodeWithName(nodeList, name);
    if (_.isUndefined(node)) {
      node = this.createNode(nodeType, d, attrList, treeType);
      nodeList.push(node);
    }
    return node;
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

  createNode: function(nodeType, d, attrList, treeType) {
    var node = {};
    if (!d) d = {};
    if (nodeType == "root") {
      node.id = "root";
      node.type = "root";
      node.name = "";
      node.children = [];
    } else if (nodeType == "client") {
      node.type = "client";

      if (treeType == "client") {
        node.id = d.client;
      } else {
        node.id = d.client + "_" + d.share;
      }
      node.name = d.client;
      node.share = d.share;
      if (treeType == "client") {
        node.children = [];
      }
    } else if (nodeType == "share") {
      node.type = "share";
      if (treeType == "share") {
        node.id = d.share;
      } else {
        node.id = d.client + "_" + d.share;
      }
      node.name = d.share;
      node.client = d.client;
      if (treeType == "share") {
        node.children = [];
      }
    } 
    _.each(attrList, function(attr) {
      node[attr] = 0;
    });
    return node;
  },
  ///// end new
  
  
  generateTree: function(data, treeType) {
    var root = null;
    var _this = this;
    if (treeType == 'client') {
      root = this.createRoot(treeType, this.nfsAttrs);
      _.each(data, function(d) {
        var c = _.find(root.children, function(x) {
          return x.clientName == d.client; 
        });
        if (_.isUndefined(c)) {
          c = _this.createNode("client", d, _this.nfsAttrs, treeType);
          root.children.push(c);
        }
        var s = _.find(c.children, function(x) {
          return x.shareName == d.share;
        });
        if (_.isUndefined(s)) {
          s = _this.createNode("share", d, _this.nfsAttrs, c, treeType);
          c.children.push(s);
        }
        _.each(_this.nfsAttrs, function(attr) {
          // copy attributes from data
          s[attr] = s[attr] + d[attr];
          // accumulate attributes
          c[attr] = c[attr] + d[attr];
        });
      });
      _.each(root.children, function(node) {
        _.each(this.nfsAttrs, function(attr) {
          root[attr] = root[attr] + node[attr];
        })
      });
    }
    return root;
  },

  getSum: function(root) {
    var sum = 0;
    if (!root.children) {
      sum = root.num_read;
    } else {
      _.each(root.children, function(node) {
        sum = sum + getSum(node);
      });
    }
    return sum;
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

  // copies attrs from old root, does not copy children
  copyRoot: function(oldRoot, nfsAttrs) {
    var newRoot = {}; 
    newRoot.name = oldRoot.name;
    newRoot.displayName = oldRoot.displayName;
    newRoot.treeType = oldRoot.treeType;
    newRoot.label = oldRoot.label;
    newRoot.type = oldRoot.type;
    newRoot.children = [];
    _.each(nfsAttrs, function(attr) {
      newRoot[attr] = oldRoot[attr];
    });
    return newRoot;
  },

  displayTree: function(json) { 
    var root = json;
    root.x0 = this.h / 2;
    root.y0 = 0;
    this.update(root);
  },

  update: function(source) {
    var duration = d3.event && d3.event.altKey ? 5000 : 500;
    var _this = this;

    // Compute the new tree layout.
    var nodes = this.d3tree.nodes(source);
    var clientNodes = nodes.filter(function(d,i) {
      return d.type == "client";
    });
    var shareNodes = nodes.filter(function(d,i) {
      return d.type == "share";
    });
    var offset = 0;
    if (!_.isNull(this.selectedNode)) {
      this.selectedNode = this.findNode(source, this.selectedNode.id); 
    }
    if (this.treeType == "client") {
      if (clientNodes.length > 0) {
        offset = -(clientNodes[0].y);
        if (_.isUndefined(this.selectedNode) || _.isNull(this.selectedNode)) {
          this.selectedNode = clientNodes[0];
        }
      }
    } else {
      if (shareNodes.length > 0) {
        offset = -(shareNodes[0].y);
        if (_.isUndefined(this.selectedNode) || _.isNull(this.selectedNode)) {
          this.selectedNode = shareNodes[0];
        } 
      }
    }
    // move everything to the left since we are not displaying the root
    //this.vis.attr("transform", "translate(" + offset + ",0)");
    this.updateDetail(this.selectedNode);
    
    var clientNode = this.vis.selectAll("g.clientNode")
    .data(clientNodes, function(d,i) {
      return d.id;
    });
    
    var clientNodeEnter = clientNode.enter().append("svg:g")
    .attr("class", "clientNode")
    .attr("transform", function(d) { 
      return "translate(" + source.y0 + "," + source.x0 + ")"; 
    })
    .on("click", function(d) {
      _this.setSelectedNode(d); 
      _this.update(_this.root);
    });

    clientNodeEnter.append("svg:image")
    .attr("xlink:href", "/img/computer.png")
    .attr("width", "20")
    .attr("height", "20")
    .attr("transform", function(d) { return "translate(0,-5)"});
    
    clientNodeEnter.append("svg:text")
    .attr("class","nodeLabel")
    .attr("x", 25)
    .attr("dy", ".35em")
    .attr("text-anchor", "start")
    .text(function(d) { return d.name; })
    .style("fill-opacity", 1e-6);

    var shareNode = this.vis.selectAll("g.shareNode")
    .data(shareNodes, function(d,i) {
      return d.id;
    });
    
    var shareNodeEnter = shareNode.enter().append("svg:g")
    .attr("class", "shareNode")
    .attr("transform", function(d) { 
      return "translate(" + source.y0 + "," + source.x0 + ")"; 
    })
    .on("click", function(d) {
      _this.setSelectedNode(d); 
      _this.update(_this.root);
    });
    
    shareNodeEnter.append("svg:image")
    .attr("xlink:href", "/img/Closed_32x32x32.png")
    .attr("width", "20")
    .attr("height", "20")
    .attr("transform", function(d) { return "translate(0,-10)"});

    //shareNodeEnter.append("svg:circle")
    //.attr("r", 1e-6)
    //.style("fill", "lightsteelblue");
    
    shareNodeEnter.append("svg:text")
    .attr("class","nodeLabel")
    .attr("x", 25)
    .attr("dy", ".35em")
    .attr("text-anchor", "start")
    .text(function(d) { return d.name; })
    .style("fill-opacity", 1e-6);

    // Transition nodes to their new position.
    var clientNodeUpdate = clientNode.transition()
    .duration(duration)
    .attr("transform", function(d) { 
      return "translate(" + d.y + "," + d.x + ")"; 
    });

    clientNodeUpdate.select("text.nodeLabel")
    .style("fill-opacity", 1)
    .style("fill", function(d) {
      if (d.id == _this.selectedNode.id) {
        return "red";
      } else {
        return "#555";
      }
    });

    var shareNodeUpdate = shareNode.transition()
    .duration(duration)
    .attr("transform", function(d) { 
      return "translate(" + d.y + "," + d.x + ")"; 
    });

    shareNodeUpdate.select("text.nodeLabel")
    .style("fill-opacity", 1)
    .style("fill", function(d) {
      if (d.id == _this.selectedNode.id) {
        return "red";
      } else {
        return "#555";
      }
    });


//
//    nodeUpdate.select("text.nodeValue")
//    .text(function(d) { 
//      return _this.selectedAttr + ": " + d[_this.selectedAttr];
//    })
//
    // Transition exiting nodes to the parent's new position.
    var clientNodeExit = clientNode.exit().transition()
    .duration(duration)
    .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
    .remove();
    
    clientNodeExit.select("text")
    .style("fill-opacity", 1e-6);

    var shareNodeExit = shareNode.exit().transition()
    .duration(duration)
    .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
    .remove();

    //shareNodeExit.select("circle")
    //.attr("r", 1e-6);

    shareNodeExit.select("text")
    .style("fill-opacity", 1e-6);

    // Update links
    var link = null;
    if (this.treeType == "client") {
      link = this.vis.selectAll("path.link")
      .data(_this.d3tree.links(clientNodes), 
      function(d) { return d.target.id; });
    } else if (this.treeType == "share") {
      link = this.vis.selectAll("path.link")
      .data(_this.d3tree.links(shareNodes), 
      function(d) { return d.target.id; });

    }

    // Enter any new links at the parent's previous position.
    link.enter().insert("svg:path", "g")
    .attr("class", "link")
    .attr("d", function(d) {
      var o = {x: source.x0, y: source.y0};
      return _this.diagonal({source: o, target: o});
    })
    .transition()
    .duration(duration)
    .attr("d", _this.diagonal);

    // Transition links to their new position.
    link.transition()
    .duration(duration)
    .attr("d", _this.diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition()
    .duration(duration)
    .attr("d", function(d) {
      var o = {x: source.x, y: source.y};
      return _this.diagonal({source: o, target: o});
    })
    .remove();

    // Stash the old positions for transition.
    nodes.forEach(function(d) {
      d.x0 = d.x;
      d.y0 = d.y;
    });
  },

  // Toggle children.
  toggle: function(d) {
    if (d.children) {
      d._children = d.children;
      d.children = null;
    } else {
      d.children = d._children;
      d._children = null;
    }
  },

  toggleAll: function(d) {
    var _this = this;
    if (d.children) {
      _.each(d.children, function(dd) {
        _this.toggleAll(dd);
      });
      //d.children.forEach(_this.toggleAll);
      this.toggle(d);
    }
  },

  toggleCopy: function(oTree, nTree) {
    var _this = this;
    // sets children or _children of nTree acc to oTree
    if (!_.isNull(oTree) && !_.isNull(nTree)) {
      this.toggleIfDifferent(oTree, nTree);
      o = oTree.children || oTree._children;
      n = nTree.children || nTree._children;
      _.chain(n).each(function(nn) {
        var on = _.find(o, function(x) { return x.name == nn.name; });
        if (on) {
          _this.toggleIfDifferent(on, nn);
        }
      });
    }
  },

  toggleIfDifferent: function(oldNode, newNode) {
    // toggles newNode if oldNode and newNode are in a different toggled state
    if ( (oldNode.children && newNode._children) || 
    (oldNode._children && newNode.children)) {
      this.toggle(newNode);
    }
  },

  updateDetail: function(node) {
    var str = "";
    if (!_.isNull(node)) {
      if (node.type == "client") {
        str = str + "Client : " + node.name + "<br>"
        +  "Share: All shares" + "<br>";
      } else if (node.type == "share") {
        str = str + "Client : " + node.client + "<br>"
        +  "Share: " + node.name + "<br>";
      } else if (node.type == "root") {
        str = str + "Client : All clients <br>"
        +  "Share: All shares <br>";

      }
      _.each(this.nfsAttrs, function(a) {
        str = str + a + ": " + node[a] + "<br>";
      });
      $("#selected-node-detail-inner").html(str);
    } else {

    }
  },

  setSelectedNode: function(node) {
    //newSelectedNode = this.findNode(this.fullTree, name);
    //if (_.isNull(newSelectedNode)) {
      //// TODO set attrs of selectedNode to 0

    //} else {
      //this.selectedNode = newSelectedNode;
    //}
    this.selectedNode = node;
    this.updateDetail(this.selectedNode);
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
  name: 'nfs-share-client-distrib',
  view: 'NfsShareClientDistribView',
  description: 'NFS Share and Client Distribution',
});


