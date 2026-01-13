(function($) {
  Drupal.behaviors.uspto_home = {
    attach: function(context, settings) {
	  /*
      const newsRotator = $(".news-rotator");
      const newsSideBlock = $(".news-side-block");

      function rearrangeElements() {
        if (isMobile($) && !document.body.classList.contains('ds-2')) {
          newsSideBlock.insertBefore(newsRotator);
        } else newsRotator.insertBefore(newsSideBlock);
      }

      if (isMobile($)) {
        rearrangeElements();
      }

      $(window).resize(function() {
        rearrangeElements();
      });
	  */
    }
  };
})(jQuery);

function isMobile($) {
  let isMobile = false;

  if ($(window).width() < 768) {
    // do something for small screens
    isMobile = true;
  } else if ($(window).width() >= 768 && $(window).width() <= 992) {
    // do something for medium screens
    isMobile = false;
  } else if ($(window).width() > 992 && $(window).width() <= 1200) {
    // do something for big screens
    isMobile = false;
  } else {
    // do something for huge screens
    isMobile = false;
  }

  return isMobile;
}
