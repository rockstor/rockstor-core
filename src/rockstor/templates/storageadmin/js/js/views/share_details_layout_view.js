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

ShareDetailsLayoutView = RockstoreLayoutView.extend({
  id: "share-details-container",
  events: {
    "click #js-acl-edit": "editAcl",
    "click #js-acl-save": "saveAcl",
    "click #js-acl-cancel": "cancelAcl",
    "click input[name='perms[]']": "showPermStr",
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.shareName = this.options.shareName;
    this.template = window.JST.share_share_details_layout;
    this.shareAclTemplate = window.JST.share_share_acl;
    this.shareAclEditTemplate = window.JST.share_share_acl_edit;
    //this.iscsi_target = new ISCSITarget({shareName: this.shareName});
    this.appliances = new ApplianceCollection();

    // create models
    this.share = new Share({shareName: this.shareName});
    this.snapshots = new SnapshotCollection();
    this.snapshots.pageSize = 10;
    this.snapshots.setUrl(this.shareName);

    this.users = new UserCollection();
    // add dependencies
    this.dependencies.push(this.share);
    this.dependencies.push(this.snapshots);
    this.dependencies.push(this.users);
    //this.dependencies.push(this.iscsi_target);
    this.dependencies.push(this.appliances);
    this.modify_choices = [
      {name: 'ro', value: 'ro'}, 
      {name: 'rw', value: 'rw'},
    ];
    this.sync_choices = [
      {name: 'async', value: 'async'},
      {name: 'sync', value: 'sync'}, 
    ];
    this.nsecurity_choices = [
      {name: 'secure', value: 'secure'},
      {name: 'insecure', value: 'insecure'}, 
    ];

  },

  render: function() {
    this.fetch(this.renderSubViews, this);
    return this;
  },
  
  renderSubViews: function() {
    var current_appliance = this.appliances.find(function(appliance) {
      return appliance.get('current_appliance') == true; 
    })
    //this.subviews['share-info'] = new ShareInfoModule({ model: this.share });
    this.subviews['share-usage'] = new ShareUsageModule({ share: this.share });
    this.subviews['snapshots'] = new SnapshotsTableModule({ 
      snapshots: this.snapshots,
      share: this.share
    });
    this.subviews['nfs-exports'] = new NFSExportsTableModule({ 
      share: this.share,
      modify_choices: this.modify_choices,
      sync_choices: this.sync_choices,
      appliance_ip: current_appliance.get('ip'),
    });
    this.subviews['smb-shares'] = new SMBShares({ 
      share: this.share,
    });
    //console.log('create ISCSITarget subview');
    //this.subviews['iscsi-target'] = new ISCSITargetView({ 
    //  share: this.share,
    //  iscsi_target: this.iscsi_target
    //});
    this.subviews['button-bar'] = new RockstoreButtonView({ 
      actions: [
        //{ name: 'resize', class: 'btn-primary', text: 'Resize', options: {rel: '#resize-share-form'}},
        //{ name: 'nfs-popup', class: 'btn-primary', text: 'NFS Export', options: {rel: '#nfs-export-form'}},
        //{ name: 'smb-popup', class: 'btn-primary', text: 'CIFS Export', options: {rel: '#smb-share-form'}},
        //{ name: 'snapshot-popup', class: 'btn-primary', text: 'Snapshot', options: {rel: '#create-snapshot-form'}},
      ]
    });
    //this.share.on('change', this.subviews['share-info'].render, this.subviews['share-info']);
    this.share.on('change', this.subviews['share-usage'].render, this.subviews['share-usage']);
    //this.share.on('change', this.subviews['nfs-exports'].render, this.subviews['nfs-exports']);
    //this.share.on('change', this.subviews['smb-shares'].render, this.subviews['smb-shares']);
    //this.snapshots.on('reset', this.subviews['snapshots'].render, this.subviews['snapshots']);
    $(this.el).append(this.template({
      share: this.share,
      permStr: this.parsePermStr(this.share.get("perms")),
      modify_choices: this.modify_choices, 
      sync_choices: this.sync_choices, 
      nsecurity_choices: this.nsecurity_choices,
    }));
    this.renderAcl();
    //this.$('#ph-share-info').append(this.subviews['share-info'].render().el);
    this.$('#ph-share-usage').append(this.subviews['share-usage'].render().el);
    this.$('#ph-snapshots').append(this.subviews['snapshots'].render().el);
    this.$('#ph-nfs-exports').append(this.subviews['nfs-exports'].render().el);
    this.$('#ph-smb-shares').append(this.subviews['smb-shares'].render().el);
    //this.$('#ph-iscsi-target').append(this.subviews['iscsi-target'].render().el);
    this.$('#ph-button-bar').append(this.subviews['button-bar'].render().el);

    this.attachActions();
  },

  attachActions: function() {
    var _this = this;
    // attach overlays
    this.$('#js-access-control').overlay();
    // create snapshot form submit action
    this.$('#create-snapshot').click(function() {
      var button = _this.$('#create-snapshot');
      if (buttonDisabled(button)) return false;
      disableButton(button);
      $.ajax({
        url: "/api/shares/" + _this.share.get('name') + "/snapshots/" + $('#snapshot-name').val(),
        type: "POST",
        dataType: "json"
      }).done(function() {
        enableButton(button);
        _this.$('#js-snapshot-popup').overlay().close();
        _this.snapshots.fetch();
        //_this.$('#snapshots').empty().append(_this.snapshotsTableView.render().el);
      }).fail(function() {
        enableButton(button);
        showError('error while creating snapshot');
      });
    });
    
    //this.$('#resize-share').click(function() {
      //var button = _this.$('#resize-share');
      //if (buttonDisabled(button)) return false;
      //disableButton(button);
      //var size = $('#new-size').val();
      
      //var sizeFormat = $('#size_format').val();
        //if(sizeFormat == 'KB'){
        //size = size;
      //}else if(sizeFormat == 'MB'){
        //size = size*1024;	
      //}else if(sizeFormat == 'GB'){
        //size = size*1024*1024;
      //}else if(sizeFormat == 'TB'){
        //size = size*1024*1024*1024;
      //}
      //$.ajax({
        //url: "/api/shares/" + _this.share.get('name'),
        //type: "PUT",
        //dataType: "json",
        //data: { "size": size},
        //success: function() {
          //enableButton(button);
          //_this.$('#js-resize').overlay().close();
          //_this.share.fetch();
        //},
        //error: function(request, status, error) {
          //enableButton(button);
          //showError(request.responseText);
        //}
      //});
    //});

    this.$('#js-delete').click(function() {
      logger.info('deleting share ' + _this.share.get('name'));
      var button = _this.$('#js-delete');
      var name = _this.share.get('name');
      if (buttonDisabled(button)) return false;
      if(confirm("Delete share:  "+ name +"...Are you sure?")){
      disableButton(button);
      $.ajax({
        url: "/api/shares/"+name+"/",
        type: "DELETE",
        dataType: "json",
        success: function() {
          enableButton(button);
          app_router.navigate('shares', {trigger: true}) 
        },
        error: function(request, status, error) {
          enableButton(button);
          showError(request.responseText);
        }
       });
      }
    });

  },
  
  renderAcl: function() {
    this.$("#ph-access-control").html(this.shareAclTemplate({
      share: this.share,
      permStr: this.parsePermStr(this.share.get("perms")),
    }));
  },

  editAcl: function(event) {
    event.preventDefault();
    this.$("#ph-access-control").html(this.shareAclEditTemplate({
      share: this.share,
      permStr: this.parsePermStr(this.share.get("perms")),
      users: this.users
    }));
  },

  saveAcl: function(event) {
    event.preventDefault();
    var _this = this;
    var button = _this.$('#js-acl-save');
    if (buttonDisabled(button)) return false;
    disableButton(button);
    var permStr = this.createPermStr();
    var data = {
      owner: this.$("#share-owner").val(),
      perms: permStr
    }
    $.ajax({
      url: "/api/shares/"+this.share.get("name")+"/acl",
      type: "POST",
      data: data,
      dataType: "json",
      success: function() {
        enableButton(button);
        _this.share.fetch({
          success: function() {
            _this.renderAcl();
          }
        });
      },
      error: function(request, status, error) {
        enableButton(button);
        var msg = parseXhrError(error)
        _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
      }
    });
  },

  cancelAcl: function(event) {
    event.preventDefault();
    this.$("#ph-access-control").html(this.shareAclTemplate({
      share: this.share,
      permStr: this.parsePermStr(this.share.get("perms")),
    }));
  },

  parsePermStr: function(perms) {
    var p = "";
    for (var i=0; i<3; i++) {
      var tmp = parseInt(perms.charAt(i)).toString(2);
      p = (tmp.length == 3) ? p.concat(tmp) :
        (tmp.length == 2) ? p.concat("0").concat(tmp) :
        p.concat("00").concat(tmp);
    }
    return p;
  },
  
  createPermStr: function() {
    var perms = [];
    this.$("input[name='perms[]']:checked").each(function() {
      perms.push($(this).val());
    });
    var us = ["owner","group","other"];
    var ps = ["r","w","x"];
    var permStr = "";
    _.each(us, function(u) {
      var t = "";
      _.each(ps, function(p) {
        var s = u + "-" + p;
        t = t + (perms.indexOf(s) != -1 ? "1" : "0"); 
      });
      permStr = permStr + parseInt(t,2);
    });
    return permStr;
  },

  showPermStr: function() {
    this.$("#permStrEdit").html(this.createPermStr());
  }

});
