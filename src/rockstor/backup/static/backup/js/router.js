app_router.route('backup', 'backup', function() {
    RockStorSocket.removeAllListeners();
    this.renderSidebar("plugins", "backup");
    $('#maincontent').empty();
    this.cleanup();
    this.currentLayout = new BackupView();
    $('#maincontent').append(this.currentLayout.render().el);
  //console.log('backup route called');
});
