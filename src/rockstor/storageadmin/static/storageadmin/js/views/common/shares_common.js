SharesCommonView = RockstorLayoutView.extend({
	confirmShareDelete: function(event) {
		var _this = this;
		var button = $(event.currentTarget);
		if (buttonDisabled(button)) return false;
		disableButton(button);
		$.ajax({
			url: "/api/shares/" + _this.share.get('name'),
			type: "DELETE",
			dataType: "json",
			success: function() {
				_this.collection.fetch({reset: true});
				enableButton(button);
				_this.$('#delete-share-modal').modal('hide');
				$('.modal-backdrop').remove();
				app_router.navigate('shares', {trigger: true})
			},
			error: function(xhr, status, error) {
				enableButton(button);
			}
		});
	},
	cancel: function(event) {
		if (event) event.preventDefault();
		app_router.navigate('shares', {trigger: true})
	}
});