// Light/dark mode. Dark is the default; a visitor who switches to light keeps it on later
// visits (remembered in their own browser only, nothing is sent anywhere). Loaded in <head>,
// so a stored choice applies before anything is drawn, without a flash of the wrong colours.
(function () {
  var root = document.documentElement;
  try {
    if (localStorage.getItem('theme') === 'light') root.dataset.theme = 'light';
  } catch (e) {}

  // Pictures with their own dark version are written as <img src="x-dark.png" data-light="x.png">:
  // the dark file is the default, and the light one is only fetched when needed. A picture with a
  // phone version has it in <source srcset="y-dark.png" data-light="y.png">, swapped the same way.
  function pictures(light) {
    document.querySelectorAll('img[data-light], source[data-light]').forEach(function (el) {
      var attribute = el.tagName === 'SOURCE' ? 'srcset' : 'src';
      if (!el.dataset.dark) el.dataset.dark = el.getAttribute(attribute);
      var wanted = light ? el.dataset.light : el.dataset.dark;
      if (el.getAttribute(attribute) !== wanted) el.setAttribute(attribute, wanted);
    });
  }

  function apply(light) {
    if (light) root.dataset.theme = 'light';
    else delete root.dataset.theme;
    pictures(light);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = light ? '#ffffff' : '#121212';
    var label = light ? 'Switch to dark mode' : 'Switch to light mode';
    document.querySelectorAll('.theme-switch').forEach(function (button) {
      button.title = label;
      button.setAttribute('aria-label', label);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    apply(root.dataset.theme === 'light');
    document.querySelectorAll('.theme-switch').forEach(function (button) {
      button.addEventListener('click', function () {
        var light = root.dataset.theme !== 'light';
        apply(light);
        try { localStorage.setItem('theme', light ? 'light' : 'dark'); } catch (e) {}
      });
    });
  });

  // Printing always uses the light version (see the print rules in style.css).
  window.addEventListener('beforeprint', function () { pictures(true); });
  window.addEventListener('afterprint', function () { pictures(root.dataset.theme === 'light'); });
})();
