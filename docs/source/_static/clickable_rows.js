document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("tr.clickable-row").forEach(function(row) {
    row.addEventListener("click", function(e) {
      // Avoid double navigation if clicking directly on the link
      if (e.target.closest("a")) return;

      const link = this.querySelector("a[href]");
      if (link) {
        window.location = link.href;
      }
    });
  });
});
