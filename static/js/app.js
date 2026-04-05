// ThermoLac — app.js
// Tema escuro/claro e menu mobile

(function () {
  "use strict";

  // ── Dark Mode ──────────────────────────────────────────────────────────────
  function setIconsAndMode(isDark) {
    document.documentElement.classList.toggle("dark-mode", isDark);
    document.querySelectorAll(".sun-icon").forEach(function (s) {
      s.style.display = isDark ? "block" : "none";
    });
    document.querySelectorAll(".moon-icon").forEach(function (m) {
      m.style.display = isDark ? "none" : "block";
    });
  }

  setIconsAndMode(document.documentElement.classList.contains("dark-mode"));

  document.querySelectorAll(".theme-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var isDark = document.documentElement.classList.toggle("dark-mode");
      try { localStorage.setItem("theme", isDark ? "dark" : "light"); } catch (e) {}
      setIconsAndMode(isDark);
    });
  });

  // ── Mobile Menu ────────────────────────────────────────────────────────────
  var menuBtn = document.querySelector(".menu-toggle");
  var topbarNav = document.querySelector(".topbar-nav");
  if (menuBtn && topbarNav) {
    menuBtn.addEventListener("click", function () {
      topbarNav.classList.toggle("active");
    });
  }
  // ── Service Worker ────────────────────────────────────────────────────────
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker
        .register("/static/sw.js")
        .catch(function (err) {
          console.log("SW falhou: ", err);
        });
    });
  }
})();
