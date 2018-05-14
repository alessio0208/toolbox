// ==UserScript==
// @name        OverwriteAlert
// @namespace   OverwriteAlert
// @include     *
// @version     1
// @grant       none
// @run-at      document-start
// ==/UserScript==
unsafeWindow.alert = function(){};
unsafeWindow.confirm = function(){};
unsafeWindow.prompt = function(){};
