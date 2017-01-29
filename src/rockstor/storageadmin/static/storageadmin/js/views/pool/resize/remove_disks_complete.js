PoolRemoveDisksComplete = RockstorWizardPage.extend({
    initialize: function() {
        this.template = window.JST.pool_resize_remove_disks_complete;
        this.initHandlebarHelpers();
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_breadCrumbs', function() {
            var html = '';
            if (this.model.get('choice') == 'add') {
                html += '<div>Change RAID level?</div><div>Select disks to add</div>';
            } else if (this.model.get('choice') == 'remove') {
                html += '<div>Select disks to remove</div>';
            } else if (this.model.get('choice') == 'raid') {
                html += '<div>Select RAID level and add disks</div>';
            }
            return new Handlebars.SafeString(html);
        });

    }

});