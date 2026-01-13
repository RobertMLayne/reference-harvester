$ = jQuery;

jQuery(function () {
  jQuery('[data-bs-toggle="tooltip"]').tooltip()
  // 508 Fix Missing First level heading.
  $('body').prepend('<h1 class="hidden sr-only">United States Patent and Trademark Office</h1>');
})

// set equal space if uspto-icon on one in row
if (jQuery('.field-collection-item-field-help-topics-collection .uspto-icon').length) {
  jQuery('.field-collection-item-field-help-topics-collection').each(function(index) {
    if (! jQuery('.uspto-icon', this).length) {
      jQuery('h4', this).addClass('icon-margin-top');
    }
  });
}

if (jQuery('ul.horizontal').length) {
  var rowCount = 0;
  jQuery('ul.horizontal').each(function() {
    if (jQuery('li', this).hasClass('span3')) {
      jQuery('li', this).each(function(index) {
        if (index % 4 == 0) {
          rowCount++;
        }
        jQuery(this).addClass('row' + rowCount);
      });
    }
    else if (jQuery('li', this).hasClass('span4')) {
      jQuery('li', this).each(function(index) {
        if (index % 3 == 0) {
          rowCount++;
        }
        jQuery(this).addClass('row' + rowCount);
      });
    }
  });

  for (var $i = 0; $i < rowCount; $i++) {
    var currentRow = ".row" + $i;
    if (jQuery('.uspto-icon', currentRow).length || jQuery('.acronyms', currentRow).length) {
      jQuery(currentRow).addClass('has-icon');
    }
  }
}
/*
jQuery('.dropdown').on('mouseenter mouseleave click tap', function() {
  jQuery(this).toggleClass("open");
});*/

jQuery('li.dropdown').on('click', function() {
    var el = jQuery(this);
  var a = el.children('a.dropdown-toggle');
  if (a.length && a.attr('href')) {
    location.href = a.attr('href');
    }
});

jQuery('.dropdown-toggle').keyup(function(e) {
    if (e.keyCode == 9) {
        jQuery(this).dropdown('toggle');
    jQuery(this).focus();
    }
});

jQuery('#uspto-main-menu> li > .dropdown-toggle').click(function () {
    window.location = jQuery(this).attr('href');
});

jQuery('#uspto-main-menu > li > .dropdown-toggle').keyup(function(e) {
    if (e.keyCode == 13) {
        window.location = jQuery(this).attr('href');
    }
});

(function ($, Drupal) {
  Drupal.behaviors.uspto_menu = {
    attach: function(context, settings) {
      // Set the main menu item of the current page to active.
      var paths = [];

      // Query search.
      if (window.location.search) {
        paths.push(window.location.pathname + window.location.search);
      }

      // Hash search.
      if (window.location.hash) {
        paths.push(window.location.pathname + window.location.hash);
      }

      // Direct path.
      paths.push(window.location.pathname);

      // Search for paths in order of preference.
      var $active;
      for (var p = 0; p < paths.length; p++) {
        $active = $('#uspto-main-menu a[href="' + paths[p] + '"]', context);
        if ($active.length) {
          // Add active class to the first link found.
          $active.parents('li').addClass('active');
          break;
        }
      }
    }
  };

})(jQuery, Drupal);

// mobile launchers
jQuery('#launch-search').on("click", function(e) {
  e.preventDefault();
  if(jQuery(this).hasClass('active')) {
    //jQuery('#block-search-form').slideUp();
    //jQuery('#block-uspto-theme-search-form').slideUp();
    jQuery('#block-usasearchform').slideUp();
    jQuery(this).removeClass('active');
  } else {
    //jQuery('#block-search-form').slideDown();
    //jQuery('#block-uspto-theme-search-form').slideDown();
    jQuery('#block-usasearchform').slideDown();
    jQuery(this).addClass('active');
  }
});
jQuery('#launch-links').on("click", function(e) {
  e.preventDefault();
  if(jQuery(this).hasClass('active')) {
    jQuery('.quick-links-menu').slideUp();
    jQuery(this).removeClass('active');
    jQuery('.region-mobile-utility-menu').hide();
  } else {
    jQuery('.quick-links-menu').slideDown();
    //jQuery('#block-mobilenavigation').slideUp().removeClass('mobile-menu-open');
	jQuery('#block-mobilenavigation').slideUp().removeClass('mobile-menu-open');
    jQuery('#launch-menu').removeClass('active');
    jQuery(this).addClass('active');
    jQuery('.region-mobile-utility-menu').show();
  //          setMobileMenuPosition();
  }
});
jQuery('#launch-menu').on("click", function(e) {
  e.preventDefault();
  if(jQuery(this).hasClass('active')) {
    //jQuery('#block-mobilenavigation').slideUp().removeClass('mobile-menu-open');
    jQuery('#block-mobilenavigation').slideUp();
    jQuery(this).removeClass('active');
    jQuery('.region-mobile-utility-menu').hide();
  } else {
    //jQuery('#block-mobilenavigation').addClass('mobile-menu-open').slideDown();
    jQuery('#block-mobilenavigation').slideDown();
    jQuery('.quick-links-menu').slideUp();
    jQuery('#launch-links').removeClass('active');
    jQuery(this).addClass('active');
    jQuery('.region-mobile-utility-menu').show();
  //          setMobileMenuPosition();
  }
});

// footer menu blocks toggle for mobile
jQuery('.region-footer .block-menu > h2').on("click", function() {
  //if (jQuery(window).width() <= 767) {
  if(window.innerWidth <= 767) {
    jQuery(this).siblings('.menu').toggle().toggleClass('active');
  }
});

// mobile sticky menu
var stickyMobileHeader = jQuery('.region-header-top');
var stickyMobileHeaderTop = 0;
if (stickyMobileHeader.length > 0) {
  stickyMobileHeaderTop = stickyMobileHeader.offset().top;
}

function checkTabletMenu() {
  if (jQuery(window).width() >= 768 && jQuery("html").hasClass('touch')) {
    jQuery('.sf-megamenu').each(function() {
    if (! jQuery(this).hasClass("sf-hidden")) {
      jQuery(".sf-megamenu").addClass("sf-hidden");
      jQuery("li.sf-depth-1.menuparent").removeClass("sfHover");
    }
    });
  }
}

jQuery(window).scroll(function(){
  setMobileMenuPosition();
  checkTabletMenu();
});

function setMobileMenuPosition() {
  if(jQuery(window).width() <= 480 && jQuery(window).scrollTop() > stickyMobileHeaderTop) {
    jQuery('.region-header-top, .region-header-middle').addClass('sticky');
  } else {
    jQuery('.region-header-top, .region-header-middle').removeClass('sticky');
  }
}
// end sticky mobile menu

function checkMobileHeight() {
  jQuery('body').css('height', '100%');
  if (jQuery(window).outerHeight() < jQuery('#block-mobilenavigation').outerHeight()) {
    jQuery('body').css('height', jQuery('#block-mobilenavigation').outerHeight() + 100);
  }
}

// Events and News Views Attachment
function listPageFilters() {
  var pageTitleHeight = jQuery('#block-pagetitle').outerHeight() - 9;
  var descriptionHeight = 0;
  if(jQuery('.main-content').find('.field--name-body').length) {
    descriptionHeight = jQuery('.main-content').find('.field--name-body').outerHeight();
  }
  var attachmentBefore = jQuery('.main-content').find('.uspto-list .attachment-before');
  var moderateFormHeight = 0;
  if (jQuery('.node-list.node--unpublished').length > 0) {
    moderateFormHeight = 120;
  }
  attachmentBefore.css('margin-top', -(pageTitleHeight + descriptionHeight - moderateFormHeight));
}

// Menu for Mobile.
// Setup Mobile Menu classes
var mobileMenu = jQuery('#block-mobilenavigation');
mobileMenu.find('li.expanded > a').addClass('menuparent');
mobileMenu.find('ul ul').addClass('mobile-menu-column');
mobileMenu.find('.mobile-menu-column').each(function() {
  var parentLinkItem = jQuery(this).prev('a');
  if(!parentLinkItem.hasClass('disableLink')) {
    var parentLinkText = parentLinkItem.text();
    parentLinkText += ' Home';
    var parentLink = parentLinkItem.attr('href');
    jQuery(this).children(":first").after('<li class="menu-item"><a href="' + parentLink + '">' + parentLinkText  + '</a></li>');
  }
});
//mobileMenu.find('.mobile-menu-column > li:nth-child(2) a').removeClass('menuparent');
// Set the parent default last, after everything else is setup.
mobileMenu.find('ul').first().addClass('mobile-menu-column mobile-active-menu');
slideInLinks();

// Mobile menu advance.
function slideInLinks() {
  mobileMenu.find('.mobile-last-active > li > a').css({'left': -jQuery(window).width()});
  mobileMenu.find('.mobile-active-menu > li > a').css('left', '0px');
}
jQuery('#block-mobilenavigation a.menuparent').click(function(e){
  e.preventDefault();
  mobileMenu.find('.mobile-last-active').removeClass('mobile-last-active');
  mobileMenu.find('.mobile-active-menu').addClass('mobile-last-active').removeClass('mobile-active-menu');
  jQuery(this).next().addClass('mobile-active-menu').css({'width': jQuery(window).width()});
  checkMobileHeight();
  slideInLinks();
});
// mobile menu back
function slideOutLinks() {
  mobileMenu.find('.mobile-last-active > li > a').css({'left': jQuery(window).width()});
  mobileMenu.find('.mobile-active-menu > li > a').css('left', '0px');
}
jQuery('#block-mobilenavigation a.menu-back').click(function(e){
  e.preventDefault();
  jQuery(this).parent().parent().addClass('mobile-last-active').removeClass('mobile-active-menu');
  jQuery(this).parent().parent().parent().parent().addClass('mobile-active-menu').css({'width': jQuery(window).width()});
  checkMobileHeight();
  slideOutLinks();
});

// window resize operations
jQuery(window).resize(function() {
  var winWidth = window.innerWidth;//jQuery(window).width();

  if (jQuery('.path-frontpage').length) {
    //jQuery(".quick-links-menu").removeAttr("style");
    jQuery("#block-bean-news-notices .tab-content").removeAttr("style");
    viewTabsAccordian();
    //if (jQuery(window).width() > 767) {
    if(window.innerWidth <= 767) {
      setTabHeight();
    }
  }

  if (jQuery('.node-type-major-landing-v2').length || jQuery('.node-type-section-landing-v2').length) {
    jQuery("#block-bean-news-notices .tab-content").removeAttr("style");
    viewTabsAccordian();
    //if (jQuery(window).width() > 767) {
      if(window.innerWidth <= 767) {
      setTabHeight();
    }
  }


  if (winWidth < 480) {

  }
  if (winWidth > 480) {
    // Make sure header isn't sticky
    jQuery('.region-header-top, .region-header-middle').removeClass('sticky');

  }
  /*if (winWidth < 727) {
    jQuery('.region-footer .menu').removeClass('active').css('display', 'none');
  }
  if (winWidth > 726) {
    jQuery('.region-footer .menu').removeClass('active').css('display', 'block');
  }*/
  if (winWidth > 726 && winWidth < 768) {

  }
  if (winWidth < 768) {
    jQuery('.sf-menu ul').css('width', winWidth);
    if (jQuery('#hero').length) {
    jQuery('.hero-content-secondary').css('height', 'auto');
    jQuery('.hero-content-primary').css('height', 'auto');
    jQuery('.hero-rotator-secondary').css('height', 'auto');
    jQuery('.hero-rotator-primary').css('height', 'auto');
    }
    if (jQuery('#block-bean-learn-about-the-process-block').length){
    var beanHeight = 0;
    jQuery('#block-bean-learn-about-the-process-block .field-collection-view').each(function() {
      jQuery('h3', this).removeClass('inactive active');
      var fcvHeight = jQuery(this).outerHeight(true);
      if (fcvHeight > beanHeight){
      beanHeight = fcvHeight;
      jQuery(this).parent().css('height', beanHeight + 60);
      }
      if(jQuery(this).is(':first-child')) {
      jQuery('h3', this).addClass('active');
      } else {
      jQuery('h3', this).addClass('inactive');
      }
    });
    }
  }
  if (jQuery('#hero.two-col').length && winWidth > 767) {
    equalHeroHeights();
  }
  if (winWidth > 767) {
    if (
      jQuery('.view-events-calendar').length ||
      jQuery('.view-news-listing').length ||
      jQuery('.view-blog-listing').length ||
      jQuery('.view-press-release-listing').length) {
      listPageFilters();
    }
    jQuery('#block-bean-learn-about-the-process-block .field-collection-container').css('height', 'auto');
    jQuery('#block-bean-learn-about-the-process-block .field-collection-view h3').removeClass('inactive active');
    jQuery('#block-mobilenavigation').hide();
    jQuery('.region-mobile-utility-menu').hide();
    jQuery('#block-usasearchform').show();
    jQuery('.quick-links-menu').removeAttr('style');
    jQuery('[id^=launch]').removeClass('active');
    setTopNavMargin();
  }
  if (jQuery('#hero-rotator').length && winWidth <= 768) {
    jQuery('.region-header-bottom .wrapper').addClass('blue-rotator');
  }
  if (jQuery('#hero-rotator').length && winWidth > 768) {
    jQuery('.region-header-bottom .wrapper').removeClass('blue-rotator');
  }
  /*if (winWidth > 767 && winWidth < 980) {
    jQuery('#block-superfish-1').find('.sf-megamenu').css('width', jQuery(window).outerWidth());
  } else if (winWidth > 980) {
    jQuery('#block-superfish-1').find('.sf-megamenu').css('width', '980');
  }*/
  resizeStatusFeeds();
}).resize();


(function ($, Drupal) {

  // Share Links
  Drupal.behaviors.shareLinks = {
    attach: function (context) {
      var shareConfig = {
        "Facebook": {
          "url": "https://www.facebook.com/sharer/sharer.php?u=%SHARE_URL%",
          "icon": "facebook-16.png"
        },
        "X": {
          "url": "https://x.com/intent/post?url=%SHARE_URL%&amp;text=%SHARE_TITLE%&amp;via=USPTO&amp;count=none&amp;lang=en",
          "icon": "x-16.png"
        },
        "LinkedIn":{
          url:"https://www.linkedin.com/shareArticle?mini=true&url=%SHARE_URL%&title=%SHARE_TITLE%",
          icon:"linkedin-16.png"
        },
        "Digg":{
          url:"https://digg.com/submit?url=%SHARE_URL%&title=%SHARE_TITLE%",
          icon:"digg-16.png"
        },
        "Reddit":{
          url:"https://reddit.com/submit?url=%SHARE_URL%&title=%SHARE_TITLE%",
          icon:"reddit-16.png"
        },
      };
      var currentPage = window.location.href;
      var title = document.title;
      if(typeof imagePath === 'undefined'){var imagePath = "/themes/custom/uspto_ds/images/share/"};
      var shareHTML = '<div id="share-box"><ul>';

      $.each(shareConfig, function(name, site) {
        shareHTML = shareHTML + '<li><a href="' + site.url.replace("%SHARE_URL%", encodeURIComponent(currentPage)).replace("%SHARE_TITLE%", encodeURIComponent(title)) + '" target="_blank"><img src="' + imagePath + site.icon + '" alt="Share on ' + name + '" />' + name + '</a></li>';
      });
      shareHTML = shareHTML + '</ul></div>';

      $('a.addthis_button', context).hover(function() {
        $(this).append(shareHTML);
        return false;
      }, function() {
        $(this).find("div:last").remove();
      });

    }
  };

})(jQuery, Drupal);

function setTopNavMargin() {
  let topNavLeftMargin = 22;

  let btnWidthPatents = $('#main-menu_patents_primary_menu').width();
  let btnWidthTrademarks = $('#main-menu_trademarks_primary_menu').width();
  let btnWidthIpPolicy = $('#main-menu_ip-policy_primary_menu').width();
  let btnWidthLearning = $('#main-menu_learning-and-resources_primary_menu').width();

  $('#main-menu_patents_primary_menu .dropdown-menu').css("margin-left", "-" + topNavLeftMargin + "px");
  $('#main-menu_trademarks_primary_menu .dropdown-menu').css("margin-left", "-" + (btnWidthPatents + 2 + topNavLeftMargin) + "px");
  $('#main-menu_ip-policy_primary_menu .dropdown-menu').css("margin-left", "-" + (btnWidthPatents + btnWidthTrademarks + 3 + topNavLeftMargin) + "px");
  $('#main-menu_learning-and-resources_primary_menu .dropdown-menu').css("margin-left", "-" + (btnWidthPatents + btnWidthTrademarks + btnWidthIpPolicy + 4 + topNavLeftMargin) + "px");

}

function include(file) {
  var script = document.createElement('script');
  script.src = file;
  script.type = 'text/javascript';
  script.defer = true;

  document.getElementsByTagName('head').item(0).appendChild(script);
}

if (window.location.hostname.toLowerCase() == "www.uspto.gov" ||
    window.location.hostname.toLowerCase() == "beta.uspto.gov" ||
    window.location.hostname.toLowerCase() == "patents.uspto.gov") {
  include(window.location.protocol + '//components.uspto.gov/js/ais/12-www.js');
}
else if(window.location.hostname.toLowerCase().indexOf("etc.uspto.gov", window.location.hostname.length - "etc.uspto.gov".length) !== -1) {
  include(window.location.protocol + '//pvt-components.etc.uspto.gov/js/ais/20-beta.js');
}

(function ($) {

  if($('.main-content #legacy-image-info').length) {
    $('.main-content #legacy-image-info').each(function() {
      if($(this).data('style')) {
        if($(this).data('style').indexOf('float: right') != -1) {
          $(this).children('.embedded-entity').addClass('align-right');
        }
        if($(this).data('style').indexOf('float: left') != -1) {
          $(this).children('.embedded-entity').addClass('align-left');
        }
        $(this).children('.embedded-entity').children('.media').children('.field--name-field-media-image').children('img').attr('style', $(this).data("style"));
      }

      if($(this).data("height")) {
        $(this).children('.embedded-entity').children('.media').children('.field--name-field-media-image').children('img').attr('height', $(this).data("height"));
      }

      if($(this).data("width")) {
        $(this).children('.embedded-entity').children('.media').children('.field--name-field-media-image').children('img').attr('width', $(this).data("width"));
      }
    });
  }

})(jQuery);

// TODO: Remove code block 512-529 and embed libraries properly.
/*!***************************************************
* mark.js v9.0.0
* https://markjs.io/
* Copyright (c) 2014–2018, Julian Kühnel
* Released under the MIT license https://git.io/vwTVl
*****************************************************/
!function(e,t){"object"==typeof exports&&"undefined"!=typeof module?module.exports=t(require("jquery")):"function"==typeof define&&define.amd?define(["jquery"],t):e.Mark=t(e.jQuery)}(this,function(e){"use strict";function t(e){return(t="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function n(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}function r(e,t){for(var n=0;n<t.length;n++){var r=t[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(e,r.key,r)}}function o(e,t,n){return t&&r(e.prototype,t),n&&r(e,n),e}function i(){return(i=Object.assign||function(e){for(var t=1;t<arguments.length;t++){var n=arguments[t];for(var r in n)Object.prototype.hasOwnProperty.call(n,r)&&(e[r]=n[r])}return e}).apply(this,arguments)}e=e&&e.hasOwnProperty("default")?e.default:e;var a=
/* */
function(){function e(t){var r=!(arguments.length>1&&void 0!==arguments[1])||arguments[1],o=arguments.length>2&&void 0!==arguments[2]?arguments[2]:[],i=arguments.length>3&&void 0!==arguments[3]?arguments[3]:5e3;n(this,e),this.ctx=t,this.iframes=r,this.exclude=o,this.iframesTimeout=i}return o(e,[{key:"getContexts",value:function(){var e=[];return(void 0!==this.ctx&&this.ctx?NodeList.prototype.isPrototypeOf(this.ctx)?Array.prototype.slice.call(this.ctx):Array.isArray(this.ctx)?this.ctx:"string"==typeof this.ctx?Array.prototype.slice.call(document.querySelectorAll(this.ctx)):[this.ctx]:[]).forEach(function(t){var n=e.filter(function(e){return e.contains(t)}).length>0;-1!==e.indexOf(t)||n||e.push(t)}),e}},{key:"getIframeContents",value:function(e,t){var n,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:function(){};try{var o=e.contentWindow;if(n=o.document,!o||!n)throw new Error("iframe inaccessible")}catch(e){r()}n&&t(n)}},{key:"isIframeBlank",value:function(e){var t="about:blank",n=e.getAttribute("src").trim();return e.contentWindow.location.href===t&&n!==t&&n}},{key:"observeIframeLoad",value:function(e,t,n){var r=this,o=!1,i=null,a=function a(){if(!o){o=!0,clearTimeout(i);try{r.isIframeBlank(e)||(e.removeEventListener("load",a),r.getIframeContents(e,t,n))}catch(e){n()}}};e.addEventListener("load",a),i=setTimeout(a,this.iframesTimeout)}},{key:"onIframeReady",value:function(e,t,n){try{"complete"===e.contentWindow.document.readyState?this.isIframeBlank(e)?this.observeIframeLoad(e,t,n):this.getIframeContents(e,t,n):this.observeIframeLoad(e,t,n)}catch(e){n()}}},{key:"waitForIframes",value:function(e,t){var n=this,r=0;this.forEachIframe(e,function(){return!0},function(e){r++,n.waitForIframes(e.querySelector("html"),function(){--r||t()})},function(e){e||t()})}},{key:"forEachIframe",value:function(t,n,r){var o=this,i=arguments.length>3&&void 0!==arguments[3]?arguments[3]:function(){},a=t.querySelectorAll("iframe"),s=a.length,c=0;a=Array.prototype.slice.call(a);var u=function(){--s<=0&&i(c)};s||u(),a.forEach(function(t){e.matches(t,o.exclude)?u():o.onIframeReady(t,function(e){n(t)&&(c++,r(e)),u()},u)})}},{key:"createIterator",value:function(e,t,n){return document.createNodeIterator(e,t,n,!1)}},{key:"createInstanceOnIframe",value:function(t){return new e(t.querySelector("html"),this.iframes)}},{key:"compareNodeIframe",value:function(e,t,n){if(e.compareDocumentPosition(n)&Node.DOCUMENT_POSITION_PRECEDING){if(null===t)return!0;if(t.compareDocumentPosition(n)&Node.DOCUMENT_POSITION_FOLLOWING)return!0}return!1}},{key:"getIteratorNode",value:function(e){var t=e.previousNode();return{prevNode:t,node:null===t?e.nextNode():e.nextNode()&&e.nextNode()}}},{key:"checkIframeFilter",value:function(e,t,n,r){var o=!1,i=!1;return r.forEach(function(e,t){e.val===n&&(o=t,i=e.handled)}),this.compareNodeIframe(e,t,n)?(!1!==o||i?!1===o||i||(r[o].handled=!0):r.push({val:n,handled:!0}),!0):(!1===o&&r.push({val:n,handled:!1}),!1)}},{key:"handleOpenIframes",value:function(e,t,n,r){var o=this;e.forEach(function(e){e.handled||o.getIframeContents(e.val,function(e){o.createInstanceOnIframe(e).forEachNode(t,n,r)})})}},{key:"iterateThroughNodes",value:function(e,t,n,r,o){for(var i,a,s,c=this,u=this.createIterator(t,e,r),l=[],h=[];s=void 0,s=c.getIteratorNode(u),a=s.prevNode,i=s.node;)this.iframes&&this.forEachIframe(t,function(e){return c.checkIframeFilter(i,a,e,l)},function(t){c.createInstanceOnIframe(t).forEachNode(e,function(e){return h.push(e)},r)}),h.push(i);h.forEach(function(e){n(e)}),this.iframes&&this.handleOpenIframes(l,e,n,r),o()}},{key:"forEachNode",value:function(e,t,n){var r=this,o=arguments.length>3&&void 0!==arguments[3]?arguments[3]:function(){},i=this.getContexts(),a=i.length;a||o(),i.forEach(function(i){var s=function(){r.iterateThroughNodes(e,i,t,n,function(){--a<=0&&o()})};r.iframes?r.waitForIframes(i,s):s()})}}],[{key:"matches",value:function(e,t){var n="string"==typeof t?[t]:t,r=e.matches||e.matchesSelector||e.msMatchesSelector||e.mozMatchesSelector||e.oMatchesSelector||e.webkitMatchesSelector;if(r){var o=!1;return n.every(function(t){return!r.call(e,t)||(o=!0,!1)}),o}return!1}}]),e}(),s=
/* */
function(){function e(t){n(this,e),this.opt=i({},{diacritics:!0,synonyms:{},accuracy:"partially",caseSensitive:!1,ignoreJoiners:!1,ignorePunctuation:[],wildcards:"disabled"},t)}return o(e,[{key:"create",value:function(e){return"disabled"!==this.opt.wildcards&&(e=this.setupWildcardsRegExp(e)),e=this.escapeStr(e),Object.keys(this.opt.synonyms).length&&(e=this.createSynonymsRegExp(e)),(this.opt.ignoreJoiners||this.opt.ignorePunctuation.length)&&(e=this.setupIgnoreJoinersRegExp(e)),this.opt.diacritics&&(e=this.createDiacriticsRegExp(e)),e=this.createMergedBlanksRegExp(e),(this.opt.ignoreJoiners||this.opt.ignorePunctuation.length)&&(e=this.createJoinersRegExp(e)),"disabled"!==this.opt.wildcards&&(e=this.createWildcardsRegExp(e)),e=this.createAccuracyRegExp(e),new RegExp(e,"gm".concat(this.opt.caseSensitive?"":"i"))}},{key:"sortByLength",value:function(e){return e.sort(function(e,t){return e.length===t.length?e>t?1:-1:t.length-e.length})}},{key:"escapeStr",value:function(e){return e.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g,"\\$&")}},{key:"createSynonymsRegExp",value:function(e){var t=this,n=this.opt.synonyms,r=this.opt.caseSensitive?"":"i",o=this.opt.ignoreJoiners||this.opt.ignorePunctuation.length?"\0":"";for(var i in n)if(n.hasOwnProperty(i)){var a=Array.isArray(n[i])?n[i]:[n[i]];a.unshift(i),(a=this.sortByLength(a).map(function(e){return"disabled"!==t.opt.wildcards&&(e=t.setupWildcardsRegExp(e)),e=t.escapeStr(e)}).filter(function(e){return""!==e})).length>1&&(e=e.replace(new RegExp("(".concat(a.map(function(e){return t.escapeStr(e)}).join("|"),")"),"gm".concat(r)),o+"(".concat(a.map(function(e){return t.processSynonyms(e)}).join("|"),")")+o))}return e}},{key:"processSynonyms",value:function(e){return(this.opt.ignoreJoiners||this.opt.ignorePunctuation.length)&&(e=this.setupIgnoreJoinersRegExp(e)),e}},{key:"setupWildcardsRegExp",value:function(e){return(e=e.replace(/(?:\\)*\?/g,function(e){return"\\"===e.charAt(0)?"?":""})).replace(/(?:\\)*\*/g,function(e){return"\\"===e.charAt(0)?"*":""})}},{key:"createWildcardsRegExp",value:function(e){var t="withSpaces"===this.opt.wildcards;return e.replace(/\u0001/g,t?"[\\S\\s]?":"\\S?").replace(/\u0002/g,t?"[\\S\\s]*?":"\\S*")}},{key:"setupIgnoreJoinersRegExp",value:function(e){return e.replace(/[^(|)\\]/g,function(e,t,n){var r=n.charAt(t+1);return/[(|)\\]/.test(r)||""===r?e:e+"\0"})}},{key:"createJoinersRegExp",value:function(e){var t=[],n=this.opt.ignorePunctuation;return Array.isArray(n)&&n.length&&t.push(this.escapeStr(n.join(""))),this.opt.ignoreJoiners&&t.push("\\u00ad\\u200b\\u200c\\u200d"),t.length?e.split(/\u0000+/).join("[".concat(t.join(""),"]*")):e}},{key:"createDiacriticsRegExp",value:function(e){var t=this.opt.caseSensitive?"":"i",n=this.opt.caseSensitive?["aàáảãạăằắẳẵặâầấẩẫậäåāą","AÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÄÅĀĄ","cçćč","CÇĆČ","dđď","DĐĎ","eèéẻẽẹêềếểễệëěēę","EÈÉẺẼẸÊỀẾỂỄỆËĚĒĘ","iìíỉĩịîïī","IÌÍỈĨỊÎÏĪ","lł","LŁ","nñňń","NÑŇŃ","oòóỏõọôồốổỗộơởỡớờợöøō","OÒÓỎÕỌÔỒỐỔỖỘƠỞỠỚỜỢÖØŌ","rř","RŘ","sšśșş","SŠŚȘŞ","tťțţ","TŤȚŢ","uùúủũụưừứửữựûüůū","UÙÚỦŨỤƯỪỨỬỮỰÛÜŮŪ","yýỳỷỹỵÿ","YÝỲỶỸỴŸ","zžżź","ZŽŻŹ"]:["aàáảãạăằắẳẵặâầấẩẫậäåāąAÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÄÅĀĄ","cçćčCÇĆČ","dđďDĐĎ","eèéẻẽẹêềếểễệëěēęEÈÉẺẼẸÊỀẾỂỄỆËĚĒĘ","iìíỉĩịîïīIÌÍỈĨỊÎÏĪ","lłLŁ","nñňńNÑŇŃ","oòóỏõọôồốổỗộơởỡớờợöøōOÒÓỎÕỌÔỒỐỔỖỘƠỞỠỚỜỢÖØŌ","rřRŘ","sšśșşSŠŚȘŞ","tťțţTŤȚŢ","uùúủũụưừứửữựûüůūUÙÚỦŨỤƯỪỨỬỮỰÛÜŮŪ","yýỳỷỹỵÿYÝỲỶỸỴŸ","zžżźZŽŻŹ"],r=[];return e.split("").forEach(function(o){n.every(function(n){if(-1!==n.indexOf(o)){if(r.indexOf(n)>-1)return!1;e=e.replace(new RegExp("[".concat(n,"]"),"gm".concat(t)),"[".concat(n,"]")),r.push(n)}return!0})}),e}},{key:"createMergedBlanksRegExp",value:function(e){return e.replace(/[\s]+/gim,"[\\s]+")}},{key:"createAccuracyRegExp",value:function(e){var t=this,n=this.opt.accuracy,r="string"==typeof n?n:n.value,o="string"==typeof n?[]:n.limiters,i="";switch(o.forEach(function(e){i+="|".concat(t.escapeStr(e))}),r){case"partially":default:return"()(".concat(e,")");case"complementary":return i="\\s"+(i||this.escapeStr("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~¡¿")),"()([^".concat(i,"]*").concat(e,"[^").concat(i,"]*)");case"exactly":return"(^|\\s".concat(i,")(").concat(e,")(?=$|\\s").concat(i,")")}}}]),e}(),c=
/* */
function(){function e(t){n(this,e),this.ctx=t,this.ie=!1;var r=window.navigator.userAgent;(r.indexOf("MSIE")>-1||r.indexOf("Trident")>-1)&&(this.ie=!0)}return o(e,[{key:"log",value:function(e){var n=arguments.length>1&&void 0!==arguments[1]?arguments[1]:"debug",r=this.opt.log;this.opt.debug&&"object"===t(r)&&"function"==typeof r[n]&&r[n]("mark.js: ".concat(e))}},{key:"getSeparatedKeywords",value:function(e){var t=this,n=[];return e.forEach(function(e){t.opt.separateWordSearch?e.split(" ").forEach(function(e){e.trim()&&-1===n.indexOf(e)&&n.push(e)}):e.trim()&&-1===n.indexOf(e)&&n.push(e)}),{keywords:n.sort(function(e,t){return t.length-e.length}),length:n.length}}},{key:"isNumeric",value:function(e){return Number(parseFloat(e))==e}},{key:"checkRanges",value:function(e){var t=this;if(!Array.isArray(e)||"[object Object]"!==Object.prototype.toString.call(e[0]))return this.log("markRanges() will only accept an array of objects"),this.opt.noMatch(e),[];var n=[],r=0;return e.sort(function(e,t){return e.start-t.start}).forEach(function(e){var o=t.callNoMatchOnInvalidRanges(e,r),i=o.start,a=o.end;o.valid&&(e.start=i,e.length=a-i,n.push(e),r=a)}),n}},{key:"callNoMatchOnInvalidRanges",value:function(e,t){var n,r,o=!1;return e&&void 0!==e.start?(r=(n=parseInt(e.start,10))+parseInt(e.length,10),this.isNumeric(e.start)&&this.isNumeric(e.length)&&r-t>0&&r-n>0?o=!0:(this.log("Ignoring invalid or overlapping range: "+"".concat(JSON.stringify(e))),this.opt.noMatch(e))):(this.log("Ignoring invalid range: ".concat(JSON.stringify(e))),this.opt.noMatch(e)),{start:n,end:r,valid:o}}},{key:"checkWhitespaceRanges",value:function(e,t,n){var r,o=!0,i=n.length,a=t-i,s=parseInt(e.start,10)-a;return(r=(s=s>i?i:s)+parseInt(e.length,10))>i&&(r=i,this.log("End range automatically set to the max value of ".concat(i))),s<0||r-s<0||s>i||r>i?(o=!1,this.log("Invalid range: ".concat(JSON.stringify(e))),this.opt.noMatch(e)):""===n.substring(s,r).replace(/\s+/g,"")&&(o=!1,this.log("Skipping whitespace only range: "+JSON.stringify(e)),this.opt.noMatch(e)),{start:s,end:r,valid:o}}},{key:"getTextNodes",value:function(e){var t=this,n="",r=[];this.iterator.forEachNode(NodeFilter.SHOW_TEXT,function(e){r.push({start:n.length,end:(n+=e.textContent).length,node:e})},function(e){return t.matchesExclude(e.parentNode)?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT},function(){e({value:n,nodes:r})})}},{key:"matchesExclude",value:function(e){return a.matches(e,this.opt.exclude.concat(["script","style","title","head","html"]))}},{key:"wrapRangeInTextNode",value:function(e,t,n){var r=this.opt.element?this.opt.element:"mark",o=e.splitText(t),i=o.splitText(n-t),a=document.createElement(r);return a.setAttribute("data-markjs","true"),this.opt.className&&a.setAttribute("class",this.opt.className),a.textContent=o.textContent,o.parentNode.replaceChild(a,o),i}},{key:"wrapRangeInMappedTextNode",value:function(e,t,n,r,o){var i=this;e.nodes.every(function(a,s){var c=e.nodes[s+1];if(void 0===c||c.start>t){if(!r(a.node))return!1;var u=t-a.start,l=(n>a.end?a.end:n)-a.start,h=e.value.substr(0,a.start),f=e.value.substr(l+a.start);if(a.node=i.wrapRangeInTextNode(a.node,u,l),e.value=h+f,e.nodes.forEach(function(t,n){n>=s&&(e.nodes[n].start>0&&n!==s&&(e.nodes[n].start-=l),e.nodes[n].end-=l)}),n-=l,o(a.node.previousSibling,a.start),!(n>a.end))return!1;t=a.end}return!0})}},{key:"wrapGroups",value:function(e,t,n,r){return r((e=this.wrapRangeInTextNode(e,t,t+n)).previousSibling),e}},{key:"separateGroups",value:function(e,t,n,r,o){for(var i=t.length,a=1;a<i;a++){var s=e.textContent.indexOf(t[a]);t[a]&&s>-1&&r(t[a],e)&&(e=this.wrapGroups(e,s,t[a].length,o))}return e}},{key:"wrapMatches",value:function(e,t,n,r,o){var i=this,a=0===t?0:t+1;this.getTextNodes(function(t){t.nodes.forEach(function(t){var o;for(t=t.node;null!==(o=e.exec(t.textContent))&&""!==o[a];){if(i.opt.separateGroups)t=i.separateGroups(t,o,a,n,r);else{if(!n(o[a],t))continue;var s=o.index;if(0!==a)for(var c=1;c<a;c++)s+=o[c].length;t=i.wrapGroups(t,s,o[a].length,r)}e.lastIndex=0}}),o()})}},{key:"wrapMatchesAcrossElements",value:function(e,t,n,r,o){var i=this,a=0===t?0:t+1;this.getTextNodes(function(t){for(var s;null!==(s=e.exec(t.value))&&""!==s[a];){var c=s.index;if(0!==a)for(var u=1;u<a;u++)c+=s[u].length;var l=c+s[a].length;i.wrapRangeInMappedTextNode(t,c,l,function(e){return n(s[a],e)},function(t,n){e.lastIndex=n,r(t)})}o()})}},{key:"wrapRangeFromIndex",value:function(e,t,n,r){var o=this;this.getTextNodes(function(i){var a=i.value.length;e.forEach(function(e,r){var s=o.checkWhitespaceRanges(e,a,i.value),c=s.start,u=s.end;s.valid&&o.wrapRangeInMappedTextNode(i,c,u,function(n){return t(n,e,i.value.substring(c,u),r)},function(t){n(t,e)})}),r()})}},{key:"unwrapMatches",value:function(e){for(var t=e.parentNode,n=document.createDocumentFragment();e.firstChild;)n.appendChild(e.removeChild(e.firstChild));t.replaceChild(n,e),this.ie?this.normalizeTextNode(t):t.normalize()}},{key:"normalizeTextNode",value:function(e){if(e){if(3===e.nodeType)for(;e.nextSibling&&3===e.nextSibling.nodeType;)e.nodeValue+=e.nextSibling.nodeValue,e.parentNode.removeChild(e.nextSibling);else this.normalizeTextNode(e.firstChild);this.normalizeTextNode(e.nextSibling)}}},{key:"markRegExp",value:function(e,t){var n=this;this.opt=t,this.log('Searching with expression "'.concat(e,'"'));var r=0,o="wrapMatches";this.opt.acrossElements&&(o="wrapMatchesAcrossElements"),this[o](e,this.opt.ignoreGroups,function(e,t){return n.opt.filter(t,e,r)},function(e){r++,n.opt.each(e)},function(){0===r&&n.opt.noMatch(e),n.opt.done(r)})}},{key:"mark",value:function(e,t){var n=this;this.opt=t;var r=0,o="wrapMatches",i=this.getSeparatedKeywords("string"==typeof e?[e]:e),a=i.keywords,c=i.length;this.opt.acrossElements&&(o="wrapMatchesAcrossElements"),0===c?this.opt.done(r):function e(t){var i=new s(n.opt).create(t),u=0;n.log('Searching with expression "'.concat(i,'"')),n[o](i,1,function(e,o){return n.opt.filter(o,t,r,u)},function(e){u++,r++,n.opt.each(e)},function(){0===u&&n.opt.noMatch(t),a[c-1]===t?n.opt.done(r):e(a[a.indexOf(t)+1])})}(a[0])}},{key:"markRanges",value:function(e,t){var n=this;this.opt=t;var r=0,o=this.checkRanges(e);o&&o.length?(this.log("Starting to mark with the following ranges: "+JSON.stringify(o)),this.wrapRangeFromIndex(o,function(e,t,r,o){return n.opt.filter(e,t,r,o)},function(e,t){r++,n.opt.each(e,t)},function(){n.opt.done(r)})):this.opt.done(r)}},{key:"unmark",value:function(e){var t=this;this.opt=e;var n=this.opt.element?this.opt.element:"*";n+="[data-markjs]",this.opt.className&&(n+=".".concat(this.opt.className)),this.log('Removal selector "'.concat(n,'"')),this.iterator.forEachNode(NodeFilter.SHOW_ELEMENT,function(e){t.unwrapMatches(e)},function(e){var r=a.matches(e,n),o=t.matchesExclude(e);return!r||o?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT},this.opt.done)}},{key:"opt",set:function(e){this._opt=i({},{element:"",className:"",exclude:[],iframes:!1,iframesTimeout:5e3,separateWordSearch:!0,acrossElements:!1,ignoreGroups:0,each:function(){},noMatch:function(){},filter:function(){return!0},done:function(){},debug:!1,log:window.console},e)},get:function(){return this._opt}},{key:"iterator",get:function(){return new a(this.ctx,this.opt.iframes,this.opt.exclude,this.opt.iframesTimeout)}}]),e}();return e.fn.mark=function(e,t){return new c(this.get()).mark(e,t),this},e.fn.markRegExp=function(e,t){return new c(this.get()).markRegExp(e,t),this},e.fn.markRanges=function(e,t){return new c(this.get()).markRanges(e,t),this},e.fn.unmark=function(e){return new c(this.get()).unmark(e),this},e});


/*! http://mths.be/details v0.1.0 by @mathias | includes http://mths.be/noselect v1.0.3 */
!function(e,t){var r,n=t.fn,o="[object Opera]"==Object.prototype.toString.call(window.opera),a=function(e){var t,r,n,o=e.createElement("details");return"open"in o?(r=e.body||function(){var r=e.documentElement;return t=!0,r.insertBefore(e.createElement("body"),r.firstElementChild||r.firstChild)}(),o.innerHTML="<summary>a</summary>b",o.style.display="block",r.appendChild(o),n=o.offsetHeight,o.open=!0,n=n!=o.offsetHeight,r.removeChild(o),t&&r.parentNode.removeChild(r),n):!1}(e),i=function(e,t,r,n){var o=e.prop("open"),a=o&&n||!o&&!n;a?(e.removeClass("open").prop("open",!1).triggerHandler("close.details"),t.attr("aria-expanded",!1),r.hide()):(e.addClass("open").prop("open",!0).triggerHandler("open.details"),t.attr("aria-expanded",!0),r.show())};n.noSelect=function(){var e="none";return this.bind("selectstart dragstart mousedown",function(){return!1}).css({MozUserSelect:e,msUserSelect:e,webkitUserSelect:e,userSelect:e})},a?(r=n.details=function(){return this.each(function(e){var r=t(this),n=t("summary",r).first();r.attr("id")||r.attr("id","details-id-"+e),r.attr("role","group"),n.attr({role:"button","aria-expanded":r.prop("open"),"aria-controls":r.attr("id")}).on("click",function(){var e=r.prop("open");n.attr("aria-expanded",!e),r.triggerHandler((e?"close":"open")+".details")})})},r.support=a):(r=n.details=function(){return this.each(function(e){var r=t(this),n=t("summary",r).first(),a=r.children(":not(summary)"),s=r.contents(":not(summary)");r.attr("id")||r.attr("id","details-id-"+e),r.attr("role","group"),n.length||(n=t("<summary>").text("Details").prependTo(r)),a.length!=s.length&&(s.filter(function(){return 3==this.nodeType&&/[^ \t\n\f\r]/.test(this.data)}).wrap("<span>"),a=r.children(":not(summary)")),r.prop("open","string"==typeof r.attr("open")),i(r,n,a),n.attr({role:"button","aria-controls":r.attr("id")}).noSelect().prop("tabIndex",0).on("click",function(){n.focus(),i(r,n,a,!0)}).keyup(function(e){(32==e.keyCode||13==e.keyCode&&!o)&&(e.preventDefault(),n.click())})})},r.support=a)}(document,jQuery);


(function ($) {

  $('details').details();

})(jQuery);



(function ($) {
  //Show first 10 stories on News and Updates list in Newest [year-now]
  if($('.main-content .view-id-news_listing, .main-content  .view-id-press_release_listing, .main-content .view-id-blog_listing').length) {
    $('.uspto-list .view-content div.item').each(function( i, val ){
      val.className += ' year-now';
      return (i !== 9);
    });
  }
})(jQuery);

/* Home page scripts */
function setTabHeight() {
  jQuery("#block-bean-news-notices .tab-content").removeAttr("style");
  var maxHeight=0;
  var activeTab = jQuery("#block-bean-news-notices .tab-content .tab-pane.active");
  var activeTabId = activeTab.length ? activeTab.attr("id") : null;

  jQuery("#block-bean-news-notices .tab-content .tab-pane").each(function(){
    jQuery(this).addClass("active");
    var height = jQuery(this).height();
    maxHeight = height>maxHeight?height:maxHeight;
    jQuery(this).removeClass("active");
  });

  jQuery("#block-bean-news-notices .tab-content").height(maxHeight);

  // Restore the previously active tab, or default to first
  if (activeTabId && jQuery("#" + activeTabId).length) {
    jQuery("#" + activeTabId).addClass("active show");
    // Also update the corresponding nav-link
    var navLink = jQuery("#block-bean-news-notices .nav-link[href='#" + activeTabId + "']");
    if (navLink.length) {
      jQuery("#block-bean-news-notices .nav-link").removeClass("active");
      navLink.addClass("active");
    }
  } else {
    jQuery("#block-bean-news-notices .tab-content .tab-pane:first").addClass("active show");
    jQuery("#block-bean-news-notices .nav-link:first").addClass("active");
  }
}

function viewTabsAccordian() {
  //if (Math.round(jQuery("body").width()) <= 750) { // changed to body width to ignore scrollbar width on window width
  if(window.innerWidth <= 767) {
    jQuery(".path-frontpage #newsPanel").addClass("panel-collapse collapse");
    jQuery(".path-frontpage #eventsPanel").addClass("panel-collapse collapse");
    jQuery(".path-frontpage #remarksPanel").addClass("panel-collapse collapse");
    jQuery(".path-frontpage #blogPanel").addClass("panel-collapse collapse");
    jQuery(".path-frontpage #subscriptionPanel").addClass("panel-collapse collapse");
    jQuery(".path-frontpage #initiativesPanel").addClass("panel-collapse collapse");

    jQuery(".path-frontpage #eventsHeading > h4 > a").addClass("collapsed");
    jQuery(".path-frontpage #remarksHeading > a").addClass("collapsed");
    jQuery(".path-frontpage #blogHeading > a").addClass("collapsed");
    jQuery(".path-frontpage #subscriptionHeading > a").addClass("collapsed");
    jQuery(".path-frontpage #initiativesHeading > h4 > a").addClass("collapsed");

    jQuery("#block-bean-quick-links-menu").removeClass("navbar yamm");
    jQuery("#qlTabContent").attr("role", "tablist");
    jQuery("#qlTabContent").removeClass("nav navbar");
    jQuery("#qlTabContent").addClass("panel-group");

    jQuery("#patentsTab").removeClass("dropdown yamm-fw");
    jQuery("#patentsTab").addClass("panel panel-default");
    jQuery("#patentsTab > a").wrap("<div class='panel-heading' role='tab' id='patentsHeading'></div>");
    jQuery("#patentsHeading > a").removeClass("dropdown-toggle");
    jQuery("#patentsHeading > a").addClass("panel-title");
    jQuery("#patentsHeading > a").removeAttr("data-bs-toggle");
    jQuery("#patentsHeading > a").attr("data-bs-toggle", "collapse");
    jQuery("#patentsHeading > a").attr("data-parent", "#qlTabContent");
    jQuery("#patentsHeading > a").attr("href", "#patentsPanel");
    jQuery("#patentsPanel").removeClass("dropdown-menu");
    jQuery("#patentsPanel").addClass("tabpanel panel-collapse collapse");
    jQuery("#patentsPanel").removeAttr("role");
    jQuery("#patentsPanel").attr("role", "tabpanel");

    jQuery("#trademarksTab").removeClass("dropdown yamm-fw");
    jQuery("#trademarksTab").addClass("panel panel-default");
    jQuery("#trademarksTab > a").wrap("<div class='panel-heading' role='tab' id='trademarksHeading'></div>");
    jQuery("#trademarksHeading > a").removeClass("dropdown-toggle");
    jQuery("#trademarksHeading > a").addClass("panel-title");
    jQuery("#trademarksHeading > a").removeAttr("data-bs-toggle");
    jQuery("#trademarksHeading > a").attr("data-bs-toggle", "collapse");
    jQuery("#trademarksHeading > a").attr("data-parent", "#qlTabContent");
    jQuery("#trademarksHeading > a").attr("href", "#trademarksPanel");
    jQuery("#trademarksPanel").removeClass("dropdown-menu");
    jQuery("#trademarksPanel").addClass("tabpanel panel-collapse collapse");
    jQuery("#trademarksPanel").removeAttr("role");
    jQuery("#trademarksPanel").attr("role", "tabpanel");


  }
  else {
    jQuery(".path-frontpage #newsPanel").removeClass("panel-collapse collapse in").removeAttr("style");
    jQuery(".path-frontpage #eventsPanel").removeClass("panel-collapse collapse in").removeAttr("style");
    jQuery(".path-frontpage #remarksPanel").removeClass("panel-collapse collapse in").removeAttr("style");
    jQuery(".path-frontpage #blogPanel").removeClass("panel-collapse collapse in").removeAttr("style");
    jQuery(".path-frontpage #subscriptionPanel").removeClass("panel-collapse collapse in").removeAttr("style");
    jQuery(".path-frontpage #initiativesPanel").removeClass("panel-collapse collapse in").removeAttr("style");

    jQuery(".path-frontpage #newsHeading > h4 > a").removeClass("collapsed");
    jQuery(".path-frontpage #eventsHeading > h4 > a").removeClass("collapsed");
    jQuery(".path-frontpage #remarksHeading > a").removeClass("collapsed");
    jQuery(".path-frontpage #blogHeading > a").removeClass("collapsed");
    jQuery(".path-frontpage #subscriptionHeading > a").removeClass("collapsed");
    jQuery(".path-frontpage #initiativesHeading > h4 > a").removeClass("collapsed");

    jQuery("#block-bean-quick-links-menu").addClass("navbar yamm");
    jQuery("#qlTabContent").removeAttr("role");
    jQuery("#qlTabContent").addClass("nav navbar");
    jQuery("#qlTabContent").removeClass("panel-group");

    jQuery("#patentsTab").addClass("dropdown yamm-fw");
    jQuery("#patentsTab").removeClass("panel panel-default");
    jQuery("#patentsTab > div > a").unwrap();
    jQuery("#patentsTab > a").addClass("dropdown-toggle");
    jQuery("#patentsTab > a").removeClass("panel-title collapsed");
    jQuery("#patentsTab > a").removeAttr("data-bs-toggle");
    jQuery("#patentsTab > a").removeAttr("href");
    jQuery("#patentsTab > a").removeAttr("data-parent");
    jQuery("#patentsTab > a").attr("data-bs-toggle", "dropdown");
    jQuery("#patentsPanel").addClass("dropdown-menu");
    jQuery("#patentsPanel").removeClass("tabpanel panel-collapse collapse in").removeAttr("style");
    jQuery("#patentsPanel").removeAttr("role");
    jQuery("#patentsPanel").attr("role", "menu");

    jQuery("#trademarksTab").addClass("dropdown yamm-fw");
    jQuery("#trademarksTab").removeClass("panel panel-default");
    jQuery("#trademarksTab > div > a").unwrap();
    jQuery("#trademarksTab > a").addClass("dropdown-toggle");
    jQuery("#trademarksTab > a").removeClass("panel-title collapsed");
    jQuery("#trademarksTab > a").removeAttr("data-bs-toggle");
    jQuery("#trademarksTab > a").removeAttr("href");
    jQuery("#trademarksTab > a").removeAttr("data-parent");
    jQuery("#trademarksTab > a").attr("data-bs-toggle", "dropdown");
    jQuery("#trademarksPanel").addClass("dropdown-menu");
    jQuery("#trademarksPanel").removeClass("tabpanel panel-collapse collapse in").removeAttr("style");
    jQuery("#trademarksPanel").removeAttr("role");
    jQuery("#trademarksPanel").attr("role", "menu");
  }
}

// For mobile FAQ's.
$(once('.mobile-filter-toggle', 'body')).on('click', function () {
  $(this).closest('.uspto-filter').toggleClass('active');
});

// For events series.
$(document).ready(function () {
  function setLessMore(sel, moreText, lessText) {
    if ($(sel).find('.views-row').length > 5) {
      $(sel).each(function () {
        var $list = $(this);
        $list.after('<a href="#" class="more_less"> ' + moreText + '</a>')
        $list.find('.views-row:gt(4)').hide();
      });

      $(once('more_less_once', '.more_less')).click(function () {
        var $btn = $(this)
        $btn.prev().find('.views-row:gt(4)').slideToggle();
        $btn.text($btn.text().trim() == moreText ? lessText : moreText);
        return false;
      });
    }
  }
  setLessMore('.view-event-series.view-display-id-list  > .view-content:first', 'Show more upcoming events', 'Show less upcoming events');
  setLessMore('.view-event-series.view-display-id-list .attachment-after .view-content', 'Show more past events', 'Show less past events');

});

/* Allow anchors from Collapse Text module to be focused and opened across all major browsers. */
(function ($) {
  if (window.location.hash.length && document.getElementById(window.location.hash.substring(1))) {
    var expandCollapsed = $('a' + window.location.hash).closest('details.collapsed').children('summary');
    if (expandCollapsed.length) {
      expandCollapsed.trigger('click');
    }
  }
})(jQuery);

/* Insert director's blog subscription block */
(function ($) {
  if ($('.node-type-blog').length || $('.list-page-blog').length) {
    let blockLocation = "";
    let blockCode = "<div id='subscription-block'>";
      blockCode += "<form accept-charset='UTF-8' action='https://public.govdelivery.com/accounts/USPTO/subscribers/qualify' id='GD-snippet-form' method='post' data-once='form-updated' data-drupal-form-fields='topic_id,email'>";
      blockCode += "<input name='utf8' type='hidden' value='?'></input>";
      blockCode += "<input name='authenticity_token' type='hidden' value='B1rRTrN4DIBteCJEdjsJ73zBe5iKdC4C8NRqnXn+y3HppmZ97jwMzCC6c6FCVGuX8Wa0rzuC+sdtmfGQgejUGw=='></input>";
      blockCode += "<input id='topic_id' name='topic_id' type='hidden' value='USPTO_3'></input>";
      blockCode += "<div class='subscription-block-title'>Subscribe to the blog</div>";
      blockCode += "<div class='form-group'>";
      blockCode += "<label for='email'>Enter your email address</label>";
      blockCode += "<div class='input-group'>";
      blockCode += "<input id='email' name='email' type='text' class='form-control' placeholder='your@email.com'>";
      blockCode += "<input class='btn btn-primary' name='commit' data-event-category='GovDelivery signup' data-event-action='GovDelivery signup button click' data-event-label='GovDelivery subscription on USPTO Directors Forum Blog' type='submit' value='Subscribe'>";
      blockCode += "</div>";
      blockCode += "</div>";
      blockCode += "</form>";
      blockCode += "</div>";

    if ($('.node-type-blog').length) {
      blockLocation = $('.row-blog-content .field--name-field-sections p:nth-of-type(2)').first();
    } else if ($('.list-page-blog').length) {
      blockLocation = $('#block-uspto-ds-views-block-blog-landing-recent-posts-block-1');
      blockCode = "<div class='col-xl-4 col-lg-5 col-12 b'>" + blockCode + "</div>";
    }

    blockLocation.after(blockCode);
  }
})(jQuery);
(function ($) {
  // initialize popovers
  //$('[data-bs-toggle="popover"]').popover();
  //bootstrap 5 popover initialize
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
})(jQuery);

function resizeStatusFeeds() {
  /*if ($('.system-status-feeds').length && window.innerWidth > 767) {
    let topMargin = document.getElementById("block-pagetitle").offsetHeight;
    if ($("#sys-status-subtitle").length) {
      topMargin += document.getElementById("sys-status-subtitle").offsetHeight;
    }
    if ($("#block-tabs").length) {
      topMargin += document.getElementById("block-tabs").offsetHeight;
    }
    if ($("#block-views-block-uspto-published-info-block-1").length) {
      topMargin += document.getElementById("block-views-block-uspto-published-info-block-1").offsetHeight;
    }
    $('.system-status-feeds').css("margin-top", + topMargin + "px");
    $('.system-status-feeds').show();
  } else {
    $('.system-status-feeds').css("margin-top", 0);
    $('.system-status-feeds').show();
  }*/
}
