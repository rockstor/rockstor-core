PoolResizeWizardView = WizardView.extend({
    
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
          this.currentPage = new PoolRaidChange({
            model: this.model,
            parent: this,
            evAgg: this.evAgg
          });
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
    switch(this.currentPageNum) {
      case 0:
        break;
      case 1:
        if (this.model.get('resize-choice') == 'add') {
          last = true;
        }
        if (this.model.get('resize-choice') == 'raid') {
          last = true;
        }
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
    console.log('in PoolResizeWizardView - finish');
    this.parent.$('#pool-resize-raid-overlay').overlay().close();
    this.parent.render();
  },

});
