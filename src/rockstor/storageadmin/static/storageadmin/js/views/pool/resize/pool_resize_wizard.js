PoolResizeWizardView = WizardView.extend({
    
  setCurrentPage: function() {
    console.log('in setCurrentPage');
    console.log(this.currentPageNum);
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
          this.currentPage = new PoolAddDisks({
            model: this.model,
            parent: this,
            evAgg: this.evAgg
          });
        } else if (this.model.get('resize-choice') == 'remove') {
          this.currentPage = new PoolRemoveDisks({
            model: this.model,
            parent: this,
            evAgg: this.evAgg
          });
        } else if (this.model.get('resize-choice') == 'raid') {
        }
        break;
      case 2:
        if (this.model.get('resize-choice') == 'add') {
          // add success msg
        } else if (this.model.get('resize-choice') == 'remove') {
          this.currentPage = new PoolRemoveDisksComplete({
            model: this.model,
            parent: this,
            evAgg: this.evAgg
          });
        } else if (this.model.get('resize-choice') == 'raid') {
        }
        break;
    }
  },

  lastPage: function() {
    var last = false;
    console.log('in lastPage');
    console.log(this.currentPageNum);
    switch(this.currentPageNum) {
      case 0:
        break;
      case 1:
        break;
      case 2:
        if (this.model.get('resize-choice') == 'remove') {
          last = true;
        }
        break;
      default: 
        break;
    }
    return last;
  },

  modifyButtonText: function() {
    switch(this.currentPageNum) {
      case 0:
        this.$('#ph-wizard-buttons').hide();
        break;
      default:
        this.$('#ph-wizard-buttons').show();
        break;
    }
    if (this.lastPage()) {
      this.$('#next-page').html('Finish');
    } else {
      this.$('#next-page').html('Next');
    }
  },

  finish: function() {
    console.log('finish in resize wizard');
    console.log(this.parent);
    this.parent.$('#pool-resize-raid-overlay').overlay().close();
    this.parent.render();
  },

});
