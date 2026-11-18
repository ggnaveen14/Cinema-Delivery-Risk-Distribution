// CinemaPredict - Report Generation Controller

document.addEventListener("DOMContentLoaded", () => {
  const downloadExcelLinks = document.querySelectorAll('a[href="/api/reports/download/excel"]');
  const downloadPdfLinks = document.querySelectorAll('a[href="/api/reports/download/pdf"]');

  downloadExcelLinks.forEach(link => {
    link.addEventListener("click", () => {
      showToast("Generating multi-sheet Excel operational report...", "info");
    });
  });

  downloadPdfLinks.forEach(link => {
    link.addEventListener("click", () => {
      showToast("Compiling formal executive PDF report...", "info");
    });
  });
});
