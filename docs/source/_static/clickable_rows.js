document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("tr.clickable-row").forEach(function(row) {
    row.addEventListener("click", function(e) {
      if (e.target.closest("a")) return;

      const link = this.querySelector("a[href]");
      if (!link) return;

      // Respect modifier keys
      if (e.metaKey || e.ctrlKey) {
        window.open(link.href, "_blank", "noopener");
      } else {
        link.click();
      }
    });
  });
});
