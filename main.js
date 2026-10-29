document.addEventListener("DOMContentLoaded", function () {
  const search = document.getElementById("tableSearch");
  const table = document.getElementById("searchTable");
  if (search && table) {
    search.addEventListener("input", function () {
      const query = search.value.toLowerCase().trim();
      table.querySelectorAll("tbody tr").forEach(function (row) {
        row.style.display = row.innerText.toLowerCase().includes(query) ? "" : "none";
      });
    });
  }
});
