PoolResizeWizardView = WizardView.extend({
  //initialize: function() {
    //WizardView.prototype.initialize.apply(this, arguments);
  //},
  
  setCurrentPage: function() {
    switch(this.currentPageNum) {
      case 0:
        this.currentPage = new PoolResizeChoice({
          model: this.model,
          parent: this,
          evAgg: this.evAgg
        });
        break;
      case 1:
        if (this.model.get('resize-choice') == 'add') {
          this.currentPage = new PoolAddDisk({
            model: this.model,
            parent: this,
            evAgg: this.evAgg
          });
        } else if (this.model.get('resize-choice') == 'remove') {
          this.currentPage = new PoolRemoveDisk({
            model: this.model,
            parent: this,
            evAgg: this.evAgg
          });
        } else if (this.model.get('resize-choice') == 'raid') {
        }
    }
    console.log('in setCurrentPage - current page is ');
    console.log(this.currentPage);
  }
});
