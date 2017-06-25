PoolResizeChoice = RockstorWizardPage.extend({

    initialize: function() {
        this.template = window.JST.pool_resize_choice;
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.initHandlebarHelpers();
    },

    events: {
        'click #change-raid': 'changeRaid',
        'click #add-disks': 'addDisks',
        'click #remove-disks': 'removeDisks'
    },

    changeRaid: function() {
        this.model.set('choice', 'raid');
        this.evAgg.trigger('nextPage');
        return false;
    },

    addDisks: function() {
        this.model.set('choice', 'add');
        this.evAgg.trigger('nextPage');
        return false;
    },

    removeDisks: function() {
        this.model.set('choice', 'remove');
        this.parent.nextPage();
        return false;
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_poolName', function() {
            var poolName = '';
            poolName = this.model.get('pool').get('name');
            return new Handlebars.SafeString(poolName);
        });

    }

});
