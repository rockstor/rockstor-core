app_router.route('backup', 'backup', function() {
    RockStorSocket.removeAllListeners();
    this.renderSidebar("plugins", "backup");
    $('#maincontent').empty();
    this.cleanup();
    this.currentLayout = new BackupView();
    $('#maincontent').append(this.currentLayout.render().el);
  //console.log('backup route called');
});

app_router.route('add_backup_policy', 'add_backup_policy', function() {
    RockStorSocket.removeAllListeners();
    this.renderSidebar("plugins", "backup");
    $('#maincontent').empty();
    this.cleanup();
    this.currentLayout = new AddBackupPolicyView();
    $('#maincontent').append(this.currentLayout.render().el);
  });