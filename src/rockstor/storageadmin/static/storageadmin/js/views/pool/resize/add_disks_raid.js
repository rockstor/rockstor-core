PoolAddDisksRaid = RockstorWizardPage.extend({

    initialize: function() {
        this.template = window.JST.pool_resize_add_disks_raid;
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.initHandlebarHelpers();
    },

    save: function() {
        var _this = this;
        var json = this.$('#raid-change-form').getJSON();
        if (json.raidChange == 'yes') {
            this.model.set('raidChange', true);
        } else {
            this.model.set('raidChange', false);
        }
        return $.Deferred().resolve();
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_poolName_raidLevel', function() {
            var html = '';
            html += this.model.get('pool').get('name') + ' is ' + this.model.get('pool').get('raid');
            return new Handlebars.SafeString(html);
        });

    }
});