(function(Drupal, $, cookies, once) {
  Drupal.behaviors.uspto_alerts = {
    attach: function (context, settings) {
      $(".region-global-alert .alert", context).each(function(index, block) {
        const alertWrapper = $(block).parents('.block');
        const alertWrapperId = alertWrapper.attr("id");

        // Show alert only if alertWrapperId is not in the cookie and not set to "closed".
        if (cookies.get(alertWrapperId) !== "closed") {
          // Show alert element which by default set to display:none look at uspto_alerts.module.
          $(alertWrapper).show();

          // Add close button and functionality.
          Drupal.behaviors.uspto_alerts.addClose(block);
        }
      });

      // If a link exists in global alert text, clicking on link should dismiss the alert.
      $(once('global-alert-link', '.region-global-alert .alert-info a', context)).on('click', function () {
        var alert_wrp = $(this).closest('.alert');
        if (alert_wrp.length && alert_wrp.find('.close').length) {
          alert_wrp.find('.close').trigger('click');
        }
      });
    },
    addClose: function(element) {
      // Add event listener for close button.
      $(element)
        .find(".close")
        .click(function(event) {
          event.preventDefault();

          // Get the id of the alert wrapper. alertWrapperId contains block name and revision id.
          const alertWrapperId = $(element)
            .parents('.block')
            .attr("id");

          // Smooth fade out close.
          $(element).fadeOut("slow", function() {
            $(element).remove();

            // Set 'closed' as cookie value for alertWrapperId.
            cookies.set(alertWrapperId, "closed", {
              expires: 7,
              path: '/'
            });
          });
        });
    }
  };
})(Drupal, jQuery, window.Cookies, once);
