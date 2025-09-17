document.addEventListener("DOMContentLoaded", () => {
  const scanBtn = document.getElementById("scanBtn");
  if (scanBtn) {
    scanBtn.addEventListener("click", () => {
      fetch("/scan", { method: "POST" })
        .then(res => res.json())
        .then(data => {
          const resultDiv = document.getElementById("scanResult");
          if (data.name) {
            resultDiv.innerHTML = `<p>✅ ${data.name} marked as ${data.status}</p>`;
          } else {
            resultDiv.innerHTML = "<p>❌ No face recognized.</p>";
          }
        });
    });
  }
});
