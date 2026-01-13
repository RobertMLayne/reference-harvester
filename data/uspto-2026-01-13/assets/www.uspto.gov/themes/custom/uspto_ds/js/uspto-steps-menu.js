(function($, Drupal, window, document) {
  Drupal.behaviors.usptoSteps = {
    attach: function(context, settings) {
      var currentHash = "";
      if ($("#step1").length) {
        var stepsOffset = $("#step1").offset().top + 60;
        $("#step1-control").addClass("active");
        $("#step1-control").one("active", function() {
          $(this).addClass("active");
        });

        if ($("#mobile-menu-options").is(":visible")) {
          stepsAccordion(true, false);
          initFloatingStepsMenu(false);
        } else {
          stepsAccordion(false, true);
          initFloatingStepsMenu(true);
        }

        $(".control-button.dropdown > button").click(function(event) {
          event.preventDefault();
          event.stopPropagation();

          var $content = $(this).next(".inner");

          $($content)
            .find(".close")
            .click(function(event) {
              event.preventDefault();
              event.stopPropagation();
              $(this)
                .parent()
                .fadeOut("fast");
            });

          if ($content.is(":visible")) {
            $content.fadeOut(200);
          } else {
            $content.fadeIn(200);
          }
        });
      }

      /**** Flows & Process Steps Accordion ****/
      function stepsAccordion(initAcc, resetAcc) {
        if (initAcc) {
          $(".step.clearfix").each(function() {
            $(this)
              .hide()
              .children(".box")
              .appendTo($(this));
          });

          $(".control-button.toggle")
            .unbind()
            .click(function(event) {
              var _this = $(this).next("div");

              event.preventDefault();

              $(_this).slideToggle("fast", function() {
                $(this)
                  .prev("div")
                  .toggleClass("active");
                $("html,body").animate(
                  { scrollTop: $(this).offset().top - 10 },
                  "fast"
                );
              });
            });
        } else {
          if (resetAcc) {
            $(".step.clearfix").each(function() {
              $(this)
                .removeAttr("style")
                .children(".box")
                .prependTo($(this));
            });

            $(".control-button.toggle").unbind();
          }
        }
      }

      /**** Flows & Process Steps Sticky Menu ****/
      function initFloatingStepsMenu(init) {
        if (init) {
          if (!$("#steps-controls").attr("style")) {
            if ($("#steps-controls").length > 0) {
              positionFloatingStepsMenu();
              $(window).bind("scroll resize", positionFloatingStepsMenu);
            }

            $("#steps-controls a, .back-to-top").click(function(event) {
              event.preventDefault();
              scrollToAnchor($(this).attr("href"));
            });
          }
        } else {
          $("#steps-controls a").unbind();
          $("#steps-controls").removeAttr("style");
          $(window).unbind("scroll resize", positionFloatingStepsMenu);
        }
      }

      function scrollToAnchor(id) {
        var tag = $("a[id='" + id.replace("#", "") + "']");
        var temp;

        $("html,body").animate(
          { scrollTop: tag.offset().top },
          "slow",
          function() {
            $("#steps-controls li").removeClass("active");
            $(id + "-control").addClass("active");
          }
        );
      }

      function positionFloatingStepsMenu() {
        var id = "";
        var hash = location.hash;

        if (hash) {
          id = hash.replace("#", "");
          $("#steps-controls li").removeClass("active");
          $("#" + id + "-control").addClass("active");
        }

        if ($(window).scrollTop() > stepsOffset && $(window).width() > 768) {
          $("#steps-controls").css({
            position: "fixed",
            top: "20px",
            "z-index": "888",
            width: "111%",
          });

          var cHeight = $('#main').height();
          var controlHeight = $('#steps-controls').height()
          var fdiff = $('#modern-page-control').offset().top - $('#steps-controls').offset().top - controlHeight;
          if (fdiff < 45) {
            $("#steps-controls").css({
              position: "relative",
              top: (cHeight - controlHeight - 66) + 'px'
            });
          }
        } else {
          $("#steps-controls").attr("style", "");
        }
        
        $(".page-anchor").each(function() {
          var top = $(window).scrollTop();
          var distance = top - $(this).offset().top;
          var hash = "#" + $(this).attr("id");
          var lastHash = Math.abs(
            $("#last-anchor").offset().top - $("#steps-controls").outerHeight()
          );

          if (distance < 30 && distance > -30 && currentHash != hash) {
            location.hash = hash;
            currentHash = hash;
          }
          if (lastHash - top <= 0) {
            $("#steps-controls").fadeOut("slow");
          } else {
            $("#steps-controls").fadeIn("fast");
          }
        });
      }

      function swapElements(element1, element2) {
        if ($(element2).index() > $(element1).index()) {
          $(element2).insertBefore(element1);
        }
      }
    }
  };
})(jQuery, Drupal, this, this.document);
