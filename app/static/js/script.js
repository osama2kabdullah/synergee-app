document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("button[data-product-id]").forEach((button) => {
    button.addEventListener("click", function () {
      const buttonEl = this;

      // Don't re-click if already disabled
      if (buttonEl.disabled) return;

      // ✅ UI feedback
      buttonEl.disabled = true;
      buttonEl.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>`;

      // ✅ Trigger the product logic
      handleProductButtonClick(buttonEl);
    });
  });

  document.getElementById("perform_all").addEventListener("click", function () {
    // Get all buttons, then filter only those that are not already disabled
    const allButtons = Array.from(document.querySelectorAll("button[data-product-id]"));
    const buttonsToProcess = allButtons.filter(btn => !btn.disabled);
    const total = buttonsToProcess.length;

    // Create and show modal dynamically
    let modalEl = document.getElementById("bulkProgressModal");
    if (!modalEl) {
      modalEl = document.createElement("div");
      modalEl.className = "modal fade";
      modalEl.id = "bulkProgressModal";
      modalEl.tabIndex = -1;
      modalEl.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Bulk Image Population</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div id="bulkProgressStatus">Starting...</div>
              <div class="progress mt-2">
                <div id="bulkProgressBar" class="progress-bar" role="progressbar" style="width: 0%">0%</div>
              </div>
              <div id="bulkProgressErrors" class="text-danger mt-2"></div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modalEl);
    }

    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    const progressBar = modalEl.querySelector("#bulkProgressBar");
    const statusText = modalEl.querySelector("#bulkProgressStatus");
    const errorText = modalEl.querySelector("#bulkProgressErrors");

    // If no buttons can be processed, show message and exit early
    if (total === 0) {
      progressBar.style.width = "100%";
      progressBar.classList.add("bg-warning");
      progressBar.textContent = "0%";
      statusText.textContent = "⚠️ No products available to perform bulk operation.";
      return;
    }

    // ✅ Proceed with processing
    let completed = 0;
    let errors = 0;
    const maxConcurrency = 3;
    let inProgress = 0;
    let queueIndex = 0;

    // Disable buttons & show spinner only for those being processed
    buttonsToProcess.forEach((button) => {
      button.disabled = true;
      button.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>`;
    });

    function updateProgress() {
      const percent = Math.round((completed / total) * 100);
      progressBar.style.width = `${percent}%`;
      progressBar.textContent = `${percent}%`;
      statusText.textContent = `Processed ${completed} of ${total}`;
      errorText.textContent = errors > 0 ? `❌ ${errors} error(s)` : "";
    }

    function next() {
      if (queueIndex >= total && inProgress === 0) {
        statusText.textContent = `✅ Completed ${completed} of ${total}`;
        progressBar.classList.add("bg-success");

        // Auto-close modal after 2 seconds (optional)
        // setTimeout(() => {
        //   modal.hide();
        // }, 2000);

        return;
      }

      while (inProgress < maxConcurrency && queueIndex < total) {
        const button = buttonsToProcess[queueIndex++];
        inProgress++;

        handleProductButtonClick(button)
          .catch(() => {
            errors++;
          })
          .finally(() => {
            completed++;
            inProgress--;
            updateProgress();
            next();
          });
      }
    }

    updateProgress();
    next();
  });


});

function handleProductButtonClick(button) {
  return new Promise((resolve, reject) => {
    const productId = button.getAttribute("data-product-id").split("/").pop();
    const resultEl = button.parentElement.querySelector(".result");

    fetch("/api/populate-single-product", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId }),
    })
      .then((response) => response.json())
      .then(({ data, success }) => {
        if (success) {
          const summary = data.metafield_update_summary || {};
          const successList = (summary.success || []).map(id => `<li>${id}</li>`).join("");
          const errorList = (summary.errors || []).map(err => `<li>${err}</li>`).join("");
          const skippedList = (summary.skipped || []).map(item => `<li>${item}</li>`).join("");

          resultEl.innerHTML = `
            <p><strong>Created Images:</strong> ${data.created_images}</p>
            <p><strong>Message:</strong> ${data.message}</p>

            <div>
              <p><strong>Metafield Update Summary:</strong></p>

              <p>✅ Success:</p>
              <ul>${successList || "<li>None</li>"}</ul>

              <p>⚠️ Skipped:</p>
              <ul>${skippedList || "<li>None</li>"}</ul>

              <p>❌ Errors:</p>
              <ul>${errorList || "<li>None</li>"}</ul>
            </div>
          `;
          button.innerHTML = "✅ Done";
          resolve();
        } else {
          button.innerHTML = "❌ Error";
          button.disabled = false;
          reject();
        }
      })
      .catch(() => {
        button.innerHTML = "❌ Error";
        button.disabled = false;
        reject();
      });
  });
}