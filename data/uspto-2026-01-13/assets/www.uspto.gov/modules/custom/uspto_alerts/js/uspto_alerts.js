(function (Drupal, $, cookies, once) {
  Drupal.behaviors.uspto_alerts = {
    attach: function (context, settings) {
      // Var to hold alert message from JSON.
      var jsonMessage = "";

      $.ajax({
        async: false,
        url: "/alerts.json",
        dataType: "json",
        success: function (data) {
          // Store alert message in global variable for later use.
          jsonMessage = data.alert;
        },
        error: function (jqXHR, textStatus, errorThrown) {
          console.log(errorThrown);
        },
      });

      $(".wrapper-alert", context).each(function (index, block) {
        const alertWrapper = $(block).parents(".uspto-alert");
        const alertWrapperId = alertWrapper.attr("id");

        // Show alert only if alertWrapperId is not in the cookie and not set to "closed".
        if (cookies.get(alertWrapperId) !== "closed") {
          // Add global alert message from JSON.
          $(alertWrapper)
            .find(".block .container .field--name-field-global-alert")
            .html(jsonMessage);

          // Show alert element which by default set to display:none look at uspto_alerts.module.
          if ($('.alert-content').length) {
            $(alertWrapper).show();
          }

          // Add close button and functionality.
          // Global alerts have their own close button. All buttons need listeners.
          if (!/global/.test(alertWrapperId)) {
            Drupal.behaviors.uspto_alerts.addClose($(block).children('.alert'));
          }
          Drupal.behaviors.uspto_alerts.addCloseListener($(block).children('.alert'));

        }
      });

      // If a link exists in global alert text, clicking on link should dismiss the alert.
      $(
        once(
          "global-alert-link",
          ".header-highlighted-global .field--name-field-global-alert a",
          context
        )
      ).on("click", function () {
        var alert_wrp = $(this).closest(".alert");
        if (alert_wrp.length && alert_wrp.find(".close").length) {
          alert_wrp.find(".close").trigger("click");
        }
      });

      // Alerts change the height of the header. Need to adjust the background height.
      let bg_height = $('section.banner').height() + $('.region-header-top').height() + ($('.region-header-highlighted').height() || 0) + $('.region-header-middle').height();
      $('.dialog-off-canvas-main-canvas').css('background-size', '100% ' + String(bg_height) + 'px');

    },
    addClose: function (element) {
      // Add close button.
      var parentWrp = $(element).parents(".uspto-alert");
      if (
        parentWrp.length == 0 ||
        (parentWrp && parentWrp.data("disable-close") != true)
      ) {
        if (!document.body.classList.contains("ds-2")) {
          $(element).prepend(
            '<button type="button" class="btn-close"><span class="sr-only">Close</span></button>'
          );
        } else {
          $(element).append(
            '<div class="alert-close-button"><button type="button" class="btn-close ml-3"><span class="sr-only">Close</span></button></div>'
          );
        }
      }
    },
    addCloseListener: function(element) {
      // Add event listener for close button.
      $(element)
        .find(".btn-close")
        .click(function (event) {
          event.preventDefault();

          // Get the id of the alert wrapper. alertWrapperId contains node id and alert version.
          const alertWrapperId = $(element).parents(".uspto-alert").attr("id");
          // Smooth fade out close.
          $(element).fadeOut("slow", function () {
            $(element).remove();

            // Set 'closed' as cookie value for alertWrapperId contains node id and alert version.
            cookies.set(alertWrapperId, "closed", {
              expires: 7,
              path: "/",
            });
          });
        });
    }

  };
})(Drupal, jQuery, window.Cookies, once);
