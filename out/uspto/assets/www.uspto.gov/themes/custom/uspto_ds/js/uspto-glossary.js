(function ($, Drupal) {
	/* check for content in glossary, if no content for letter link, disable button */
	$('#glossaryNav').find('a').each(function() {
		var currentAnchor = $(this).attr('href');
		if($(currentAnchor).length == 0) {
			$(this).parent().addClass('disabled');
		}
	});

})(jQuery, Drupal);