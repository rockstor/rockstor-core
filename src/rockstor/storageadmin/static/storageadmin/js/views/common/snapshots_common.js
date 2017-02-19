SnapshotsCommonView = RockstorLayoutView.extend({
    selectSnapshot: function(event) {
        var _this = this;
        var name = $(event.currentTarget).attr('data-name');
        var checked = $(event.currentTarget).prop('checked');
        this.selectSnapshotWithName(name, checked);
        this.toggleDeleteButton();
    },

    selectSnapshotWithName: function(name, checked) {
        if (checked) {
            if (!RockstorUtil.listContains(this.selectedSnapshots, 'name', name)) {
                RockstorUtil.addToList(
                    this.selectedSnapshots, this.collection, 'name', name);
            }
        } else {
            if (RockstorUtil.listContains(this.selectedSnapshots, 'name', name)) {
                RockstorUtil.removeFromList(this.selectedSnapshots, 'name', name);
            }
        }
    },

    toggleDeleteButton: function() {
        if (this.selectedSnapshots.length == 0) {
            $('#js-snapshot-delete-multiple').css('visibility', 'hidden');
        } else {
            $('#js-snapshot-delete-multiple').css('visibility', 'visible');
        }
    },

    selectAllSnapshots: function(event) {
        var _this = this;
        var checked = $(event.currentTarget).prop('checked');
        this.$('.js-snapshot-select').prop('checked', checked);
        this.$('.js-snapshot-select').each(function() {
            _this.selectSnapshotWithName($(this).attr('data-name'), checked);
        });
        this.toggleDeleteButton();
    },
});