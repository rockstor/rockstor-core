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
  events: {
    "click .selectedAttr": "setSelectedAttr"
  },

  initialize: function() {
    this.probe = this.options.probe;
    this.template = window.JST.probes_nfs_share_client_user;
    this.nfsAttrs = ["num_read", "num_write", "num_lookup",
      "num_create", "num_commit", "num_remove",
      "sum_read", "sum_write"];
    this.sortAttrs = ["num_read"]; // default
    this.treeType = "uid";
    this.updateInterval = 5000; // update every updateInterval seconds
    this.rawData = null; // data returned from probe backend
  },

  render: function() {
    $(this.el).html(this.template({
      probe: this.probe, 
      updateInterval: this.updateInterval,
      treeType: this.treeType
    }));
    this.rows = d3.select(this.el).select("#nfs-share-client-user-rows");
    var _this = this;
    if (this.probe.get("state") == probeStates.RUNNING) {
      var t2 = this.probe.get("start");
      var t1 = moment(t2).subtract("ms",this.updateInterval).toISOString();
      this.update(this.probe, t1, t2, true, this.updateInterval);
    } else if (this.probe.get("state") == probeStates.STOPPED) {
      var t1 = this.probe.get("start");
      var t2 = this.probe.get("end");
      this.update(this.probe, t1, t2, false, null);
    } 
    return this;
  },
  
  update: function(probe, t1, t2, repeat, updateInterval) {
    var _this = this;
    var dataUrl = this.probe.dataUrl() + "?t1=" + t1 + "&t2=" + t2;
    if (repeat) {
      this.renderIntervalId = window.setInterval(function() {
        _this.fetchAndRender(dataUrl);
        // update times
        t1 = t2;
        t2 = moment(t1).add("ms",_this.updateInterval).toISOString();
        dataUrl = _this.probe.dataUrl() + "?t1=" + t1 + "&t2=" + t2;
      }, updateInterval);
    } else {
      this.fetchAndRender(dataUrl);
    }
  },

  fetchAndRender: function(dataUrl) {
    var _this = this;
    $.ajax({
      url: dataUrl,
      type: "GET",
      dataType: "json",
      success: function(data, textStatus, jqXHR) {
        _this.data = data;
        var results = data.results;
        //results = _this.generateData(); // TODO remove after test
        if (!_.isEmpty(results)) {
          _this.renderViz(results);
        } else {
          // TODO show no data msg
        }
      },
      error: function(request, status, error) {
        console.log(error);
      }
    });
  },

  renderViz: function(data) {
    var _this = this;
    this.root = this.createTree(data, this.treeType, this.nfsAttrs, this.sortAttrs, 4);
    var rowHeight = 50;
    var rowPadding = 4;
    var length = this.root.children.length;
    
    var attrArray = _.flatten(_.map(this.root.children, function(n) {
      return _.map(n.children, function(d) { return d.sortVal; } );
    }));
    this.attrMax = d3.max(attrArray);
    
    // Create rows 
    var row = this.rows.selectAll("div.nfs-viz-row")
    .data(this.root.children, function(d,i) {
      return d.id;
    });
    var rowEnter = row.enter()
    .append("div")
    .attr("class", "nfs-viz-row")
    // enter at the bottom of the list
    .style("top", ((length-1)*(rowHeight + rowPadding*2)) + "px");
  
    // Render row contents 
    this.renderRow(row); 

    // move to sorted position
    var rowUpdate = row.transition()
    .duration(1000)
    .style("top",function(d,i) { 
      return (i*(rowHeight + rowPadding*2)) + "px"; 
    });
    
    var rowExit = row.exit();
    rowExit.remove();
    
  },
  
  renderRow: function(row) {
    if (this.treeType == "client") {
      var clients = row.selectAll("div.client")
      .data(function(d,i) { return [d]; }, function(d) { return d.id});
      var clientsEnter = clients.enter().append("div").attr("class", "client");

      var clientsInner = clients.selectAll("div.column-inner")
      .data(function(d,i) { return [d]; }, function(d) { return d.id});

      var clientsInnerEnter = clientsInner.enter()
      .append("div")
      .attr("class", "column-inner");

      this.renderClient(clientsInner);

    } else if (this.treeType == "uid") {
      var users = row.selectAll("div.user")
      .data(function(d,i) { return [d]; }, function(d) { return d.id});
      var usersEnter = users.enter().append("div").attr("class", "user");
      
      var usersInner = users.selectAll("div.column-inner")
      .data(function(d,i) { return [d]; }, function(d) { return d.id});
      var usersInnerEnter = usersInner.enter()
      .append("div")
      .attr("class", "column-inner")
              
      this.renderUser(usersInner);
    }

    var shares = row.selectAll("div.top-shares")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});
    var sharesEnter = shares.enter().append("div").attr("class", "top-shares");
    
    var sharesInner = shares.selectAll("div.column-inner")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});
    
    var sharesInnerEnter = sharesInner.enter()
    .append("div")
    .attr("class", "column-inner");

    this.renderShares(sharesInner);
    
    var reads = row.selectAll("div.nfs-reads")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});
    var readsEnter = reads.enter().append("div").attr("class", "nfs-reads");
    
    var readsInner = reads.selectAll("div.column-inner")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});
    
    var readsInnerEnter = readsInner.enter()
    .append("div")
    .attr("class", "column-inner");

    this.renderReads(readsInner);
   
    var writes = row.selectAll("div.nfs-writes")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});
    var writesEnter = writes.enter().append("div").attr("class", "nfs-writes");
    
    var writesInner = writes.selectAll("div.column-inner")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});

    var writesInnerEnter = writesInner.enter()
    .append("div")
    .attr("class", "column-inner")

    this.renderWrites(writesInner);
    
    var lookups = row.selectAll("div.nfs-lookups")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});
    var lookupsEnter = lookups.enter().append("div").attr("class", "nfs-lookups");

    var lookupsInner = lookups.selectAll("div.column-inner")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});

    var lookupsInnerEnter = lookupsInner.enter()
    .append("div")
    .attr("class", "column-inner")
    
    this.renderLookups(lookupsInner);
    
    var dataRead = row.selectAll("div.nfs-data-read")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});
    var dataReadEnter = dataRead.enter().append("div").attr("class", "nfs-data-read");
    
    var dataReadInner = dataRead.selectAll("div.column-inner")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});

    var dataReadInnerEnter = dataReadInner.enter()
    .append("div")
    .attr("class", "column-inner")
    this.renderDataRead(dataReadInner);
    
    var dataWritten = row.selectAll("div.nfs-data-written")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});
    var dataWrittenEnter = dataWritten.enter().append("div").attr("class", "nfs-data-written");
    
    var dataWrittenInner = dataWritten.selectAll("div.column-inner")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});

    var dataWrittenInnerEnter = dataWrittenInner.enter()
    .append("div")
    .attr("class", "column-inner")
    this.renderDataWritten(dataWrittenInner);

    var lastSeen = row.selectAll("div.nfs-last-seen")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});
    var lastSeenEnter = lastSeen.enter().append("div").attr("class", "nfs-last-seen");
    
    var lastSeenInner = lastSeen.selectAll("div.column-inner")
    .data(function(d,i) { return [d]; }, function(d) { return d.id});

    var lastSeenInnerEnter = lastSeenInner.enter()
    .append("div")
    .attr("class", "column-inner")
    this.renderLastSeen(lastSeenInner);
  },

  renderClient: function(client) {
    client.html("");
    client.append("img")
    .attr("src", "/img/computer.png")
    .attr("width", "20")
    .attr("height", "20");
    client.append("br");    
    client.append("span")
    .attr("class","nodeLabel")
    .text(function(d) { return d.name; });
  },

  renderUser: function(user) {
    user.html("");
    user.append("i")
    .attr("class", "icon-user")
    user.append("br");    
    user.append("span")
    .attr("class","nodeLabel")
    .text(function(d) { return d.name; });
  },

  renderShares: function(shares) {
    var _this = this;
    var shareWidth = 60;
    var sharePadding = 4;

    //var rScale = d3.scale.linear().domain([0, this.attrMax]).range([2,10]);
    var rScale = d3.scale.linear()
    .domain([0, this.attrMax])
    .range(["#F7C8A8","#F26F18"]);

    var share = shares.selectAll("div.share")
    .data(function(d) { return d.children; }, function(dItem){
      return dItem.id;
    });
    var shareEnter = share.enter()
    .append("div")
    .attr("class","share")
    
    shareEnter.append("svg")
    .attr("width", 50)
    .attr("height", 25)
    .append("g")
    .append("rect")
    .attr("x", 10)
    .attr("y", 10)
    .attr("width", 10)
    .attr("height", 10)
    .attr("fill", function(d) { return rScale(d.sortVal); });
  
    //.append("circle")
    //.attr("cx", 25)
    //.attr("cy", 10)
    ////.attr("r", function(d) { return rScale(d[_this.attr]); })
    //.attr("r", 2)
    //.attr("fill", "steelblue");
    
    shareEnter.append("br");
    
    shareEnter.append("span")
    .attr("class","nodeLabel")
    .text(function(d) { return d.name; });

    //share.select("circle").transition().duration(500).attr("r", function(d) { return rScale(d.sortVal); })
    share.select("rect").transition().duration(500)
    .attr("fill", function(d) {  return rScale(d.sortVal); });
    share.select("nodeLabel").text(function(d) { return d.name; });

    var shareUpdate = share.transition()
    .duration(500)
    .style("left", function(d,i) { 
      return (i*(shareWidth + sharePadding*2)) + "px";
    });
    
    var shareExit = share.exit();
    shareExit.remove();

  },
  
  renderReads: function(reads) {
    reads.text(function(d) { return d["num_read"]; });
  },

  renderWrites: function(writes) {
    writes.text(function(d) { return d["num_write"]; });
  },

  renderLookups: function(lookups) {
    lookups.text(function(d) { return d["num_lookup"]; });
  },
  
  renderDataRead: function(dataRead) {
    dataRead.text(function(d) { return humanize.filesize(d["sum_read"]); });
  },

  renderDataWritten: function(dataWritten) {
    dataWritten.text(function(d) { return humanize.filesize(d["sum_write"]); });
  },

  renderLastSeen: function(lastSeen) {
    lastSeen.text(function(d) { return d.lastSeen.format(); });
  },

  cleanup: function() {
    if (!_.isUndefined(this.renderIntervalId) && 
    !_.isNull(this.renderIntervalId)) {
      window.clearInterval(this.renderIntervalId);
    }
  },

  createTree: function(data, treeType, attrList, sortAttrs, n) {
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
      if (moment(d.ts).isAfter(root.lastSeen)) {
        root.lastSeen = moment(d.ts);
      }
      if (moment(d.ts).isAfter(nodeL1.lastSeen)) {
        nodeL1.lastSeen = moment(d.ts);
      }
      if (moment(d.ts).isAfter(nodeL2.lastSeen)) {
        nodeL2.lastSeen = moment(d.ts);
      }
     
    });
  
    // update value to be sorted by
    _.each(root.children, function(n1) {
      n1.sortVal = 0;
      _.each(sortAttrs, function(a) {
        n1.sortVal = n1.sortVal + n1[a];
      });
      _.each(n1.children, function(n2) {
        n2.sortVal = 0;
        _.each(sortAttrs, function(a) {
          n2.sortVal = n2.sortVal + n2[a];
        });
      });
    });
     
    // get top n children sorted by sortAttr 
    var children = root.children;
    root.children = [];
    var tmp = _.sortBy(children, function(d) { return d.sortVal; }).reverse();
    for (i=0; i<n && i<tmp.length; i++) {
      var c = tmp[i].children;
      tmp[i].children = [];
      var tmp2 = _.sortBy(c, function(d1) { return d1.sortVal; }).reverse();
      for (j=0; j<n && j<tmp2.length; j++) {
        tmp[i].children.push(tmp2[j])
      }
      root.children.push(tmp[i]);
    }
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
    return {name: name, nodeType: nodeType, children: [], 
      lastSeen: moment.unix(0)};
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
        var uid = 5000 + j;
        var gid = 5000 + j;
        data.push({
          share: share,
          client: ip,
          uid: uid,
          gid: gid,
          num_read: 5 + Math.floor(Math.random() * 5),
          num_write: 1 + Math.floor(Math.random() * 5),
          num_lookup: 1 + Math.floor(Math.random() * 5),
        });
      }
    }
    var ipRandom1 = "10.0.0." + (5 + (Math.floor(Math.random() * 5)));
    var share1 = "share_1";
    var uid1 = 5005;
    var gid1 = 5005;
    var ipRandom2 = "10.0.0." + (10 + (Math.floor(Math.random() * 5)));
    var share2 = "share_2";
    var uid2 = 5006;
    var gid2 = 5006;
    var ipRandom3 = "10.0.0." + (15 + (Math.floor(Math.random() * 5)));
    var share3 = "share_3";
    var uid3 = 5007;
    var gid3 = 5007;
    data.push({
      share: share1,
      client: ipRandom1,
      uid: uid1,
      gid: gid1,
      num_read: 5 + Math.floor(Math.random() * 5),
      num_write: 1 + Math.floor(Math.random() * 5),
      num_lookup: 1 + Math.floor(Math.random() * 5),
    });
    data.push({
      share: share2,
      client: ipRandom2,
      uid: uid2,
      gid: gid2,
      num_read: 5 + Math.floor(Math.random() * 5),
      num_write: 1 + Math.floor(Math.random() * 5),
      num_lookup: 1 + Math.floor(Math.random() * 5),
    });
    data.push({
      share: share3,
      client: ipRandom3,
      uid: uid3,
      gid: gid3,
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
  },

  setSelectedAttr: function(event) {
    var _this = this;
    var tgt = $(event.currentTarget);
    var val = tgt.val();
    if (tgt.is(':checked')) {
      if (this.sortAttrs.indexOf(val) == -1) {
        this.sortAttrs.push(val);
      }
    } else {
      var i = this.sortAttrs.indexOf(val);
      if (i != -1) {
        this.sortAttrs.splice(i, 1);
      }
    }
    this.renderViz(this.data.results);
  }

});

RockStorProbeMap.push({
  name: 'nfs-5',
  view: 'NfsShareClientView',
  description: 'NFS Share and Client Distribution',
});



