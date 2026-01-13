(function($, Drupal) {
	var uspto_section_landings;
	
	Drupal.behaviors.uspto_section_landing = uspto_section_landings = {
		state: {
			page: 1
		},
		state_1: {
			page: 1
		},
		attach: function(context, settings) {
			$('.view-section-news > .view-content > div').hide();
			this.update();
			$('.section-view-more', context).click(this.onShowMoreClick);

			$('.view-section-events > .view-content > div').hide();
			this.update_event();
			$('.section-event-view-more', context).click(this.onShowMoreEvent);
		},
		onShowMoreClick: function(event) {
			event.preventDefault();
			uspto_section_landings.state.page++;
			uspto_section_landings.update();
			if (!$('.view-section-news .page-' + (uspto_section_landings.state.page + 1)).length) {
				$('.section-view-more').hide();
			}
		},
		update: function() {
			$('.view-section-news .page-' + uspto_section_landings.state.page).show();
		},

		onShowMoreEvent: function(event) {
			event.preventDefault();
			uspto_section_landings.state_1.page++;
			uspto_section_landings.update_event();
			if (!$('.view-section-events .page-' + (uspto_section_landings.state_1.page + 1)).length) {
				$('.section-event-view-more').hide();
			}
		},
		update_event: function() {
			$('.view-section-events .page-' + uspto_section_landings.state_1.page).show();
		}
	};
}(jQuery, Drupal));