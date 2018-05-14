// ==UserScript==
// @name        BlockUnloadEvents
// @namespace   BlockUnloadEvents
// @include     *
// @version     1
// @grant       none
// ==/UserScript==
(function() {
  unsafeWindow.onbeforeunload = null;
  unsafeWindow.onunload = null;
})();
