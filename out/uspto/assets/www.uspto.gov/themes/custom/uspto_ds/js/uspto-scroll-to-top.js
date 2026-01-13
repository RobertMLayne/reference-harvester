// show/hide the back-to-top link in footer
// set to show when the user has scrolled past 50% of their window

$(function(){ 
  $(window).scroll(function() {
    if($(this).scrollTop() > $(window).height() * 0.5) {
      $('footer a.scrollToTop').fadeIn()
    } else {
      $('footer a.scrollToTop').fadeOut()
    }
  })
})
