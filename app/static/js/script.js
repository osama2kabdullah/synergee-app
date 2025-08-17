document.addEventListener("DOMContentLoaded", () => {
  const productHandler = new ProductHandler();
  const uiManager = new UIManager(productHandler);

  uiManager.initialize();
});


// Drag start handler
function handleDragStart(e) {
  e.dataTransfer.setData('text/plain', this.dataset.id);
  this.classList.add('dragging'); // visual feedback
}

// Drag end handler (remove visual effect)
function handleDragEnd() {
  this.classList.remove('dragging');
}

// Drag over handler
function handleDragOver(e) {
  e.preventDefault();
  this.classList.add('hover');
}

// Drag leave handler
function handleDragLeave() {
  this.classList.remove('hover');
}

// Drop handler
function handleDrop(imageLookup, e) {
  e.preventDefault();
  this.classList.remove('hover');
  
  const imgId = e.dataTransfer.getData('text/plain');
  const draggedImg = document.querySelector(`img[draggable="true"][data-id="${imgId}"]`);
  if (!draggedImg) return;

  const contentArea = this.querySelector(".content");

  // If there was already an image in the box, restore it first
  const existingImg = contentArea.querySelector('img');
  if (existingImg) {
    const existingId = existingImg.dataset.id;
    const originalExistingImg = document.querySelector(`img[draggable="true"][data-id="${existingId}"]`);
    if (originalExistingImg) {
      originalExistingImg.parentElement.style.display = 'block'; // show old image back
    }
  }

  // Clone and disable dragging in drop zone
  const newImg = draggedImg.cloneNode(true);
  newImg.draggable = false;

  contentArea.replaceChildren(newImg);
  this.classList.add('filled');
  this.parentElement.classList.remove('error');
  // draggedImg.parentElement.style.display = 'none';

  // Success highlight
  this.classList.add('drop-success');
  setTimeout(() => this.classList.remove('drop-success'), 500);

  // Handle delete button
  const delBtn = this.querySelector('button[data-image-remove]');
  if (delBtn) {
    delBtn.onclick = () => {
      contentArea.textContent = 'Drop here';
      this.classList.remove('filled');
      // draggedImg.parentElement.style.display = 'block';

        updateImageData({
          variant_id: raw_image.dataset.variantId,
          raw_img_url: raw_image.src,
          product_img_id: "",
          product_img_url: "",
          matched: false,
          needs_upload: true
        }, imageLookup);

    };
  }

  const raw_image = this.parentElement.querySelector(".raw_img_url");

  updateImageData({
    variant_id: raw_image.dataset.variantId,
    raw_img_url: raw_image.src,
    product_img_id: imgId,
    product_img_url: newImg.src,
    matched: true,
    needs_upload: false
  }, imageLookup);
}

function updateImageData({ variant_id, raw_img_url, product_img_id, product_img_url, matched, needs_upload }, imageLookup) {
  const entry = imageLookup.get(raw_img_url);

  if (!entry) {
    console.warn(`Image with raw_img_url ${raw_img_url} not found`);
    return;
  }

  // Optional: check variant id mismatch here if you want

  // Update only the fields that are passed (avoid overwriting with undefined)
  if (product_img_id !== undefined) entry.image.product_img_id = product_img_id;
  if (product_img_url !== undefined) entry.image.product_img_url = product_img_url;
  if (matched !== undefined) entry.image.matched = matched;
  if (needs_upload !== undefined) entry.image.needs_upload = needs_upload;
}

function getIcon(name) {
  let icon = ``
  if (name == 'eye') {
    icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
      <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
      <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
    </svg>`;
  }
  if (name == 'zoom-in') {
    icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-zoom-in" viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M6.5 12a5.5 5.5 0 1 0 0-11 5.5 5.5 0 0 0 0 11M13 6.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0"/>
      <path d="M10.344 11.742q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1 6.5 6.5 0 0 1-1.398 1.4z"/>
      <path fill-rule="evenodd" d="M6.5 3a.5.5 0 0 1 .5.5V6h2.5a.5.5 0 0 1 0 1H7v2.5a.5.5 0 0 1-1 0V7H3.5a.5.5 0 0 1 0-1H6V3.5a.5.5 0 0 1 .5-.5"/>
    </svg>`;
  }
  if (name == 'zoom-out') {
    icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-zoom-out" viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M6.5 12a5.5 5.5 0 1 0 0-11 5.5 5.5 0 0 0 0 11M13 6.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0"/>
      <path d="M10.344 11.742q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1 6.5 6.5 0 0 1-1.398 1.4z"/>
      <path fill-rule="evenodd" d="M3 6.5a.5.5 0 0 1 .5-.5h6a.5.5 0 0 1 0 1h-6a.5.5 0 0 1-.5-.5"/>
    </svg>`;
  }
  if (name == 'zoom-reset') {
    icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrows-move" viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M7.646.146a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1-.708.708L8.5 1.707V5.5a.5.5 0 0 1-1 0V1.707L6.354 2.854a.5.5 0 1 1-.708-.708zM8 10a.5.5 0 0 1 .5.5v3.793l1.146-1.147a.5.5 0 0 1 .708.708l-2 2a.5.5 0 0 1-.708 0l-2-2a.5.5 0 0 1 .708-.708L7.5 14.293V10.5A.5.5 0 0 1 8 10M.146 8.354a.5.5 0 0 1 0-.708l2-2a.5.5 0 1 1 .708.708L1.707 7.5H5.5a.5.5 0 0 1 0 1H1.707l1.147 1.146a.5.5 0 0 1-.708.708zM10 8a.5.5 0 0 1 .5-.5h3.793l-1.147-1.146a.5.5 0 0 1 .708-.708l2 2a.5.5 0 0 1 0 .708l-2 2a.5.5 0 0 1-.708-.708L14.293 8.5H10.5A.5.5 0 0 1 10 8"/>
    </svg>`;
  }
  if (name == 'delete') {
    icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash3" viewBox="0 0 16 16">
      <path d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5M11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84l.853-10.66h.538a.5.5 0 0 0 0-1zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53Zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47M8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5"/>
    </svg>`;
  }
  return icon;
}

class ProductHandler {
  async populate(button) {
    
    const productId = button.dataset.productId.split("/").pop();
    const resultEl = button.parentElement.querySelector(".result");

    try {
      const response = await fetch("/api/populate-single-product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: productId }),
      }).then(res => res.json());
      if (response.message.includes("unmatched")) {
        this.showUnmatchedImages(response, productId);
      }
      if (response.status === "success") {
        button.innerHTML = "✅ Done";
        return true;
      } else {
        button.innerHTML = "❌ Error";
        button.disabled = false;
        return false;
      }
    } catch {
      button.innerHTML = "❌ Error";
      button.disabled = false;
      return false;
    }
  }

  async delete(button) {
    const productId = button.dataset.productId.split("/").pop();

    try {
      const response = await fetch("/api/delete-populated-single-product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: productId }),
      }).then(res => res.json());

      if (response.status === "success") {
        button.innerHTML = "✅ Done";
        return true;
      } else {
        button.innerHTML = "❌ Error";
        button.disabled = false;
        return false;
      }
    } catch {
      button.innerHTML = "❌ Error";
      button.disabled = false;
      return false;
    }
  }

  showUnmatchedImages(response, productId) {
    const mainImages = response.data.media.map(item => `
      <div class="image-wrap position-relative border p-2">
        <button data-image-popup class="position-absolute btn btn-light btn-sm">
          ${getIcon('eye')}
        </button>
        <img draggable="true" data-id="${item.id}" src="${item.img_url}&width=200" alt="Product Image" class="img-fluid">
      </div>
    `).join('');

    const unmatchedZones = response.data.results.map(result => {
      const variantId = result.variant_id;
      const unmatched = result.data_images.filter(img => !img.matched).map(img => `
        <div class="zone-wrap d-flex align-items-center gap-3 border p-2">
          <div class="image-wrap position-relative border p-2">
            <button data-image-popup class="position-absolute btn btn-light btn-sm">
              ${getIcon('eye')}
            </button>
            <img src="${img.raw_img_url}" data-variant-id="${variantId}" width="200" alt="Unmatched Image" class="img-fluid raw_img_url">
          </div>
          <h1>+</h1>
          <div class="drop-zone">
            <button data-image-popup class="position-absolute start-0 top-0 btn btn-light btn-sm">
              ${getIcon('eye')}
            </button>
            <span class="content">Drop here</span>
            <button data-image-remove class="position-absolute end-0 top-0 btn btn-light btn-sm">
              ${getIcon('delete')}
            </button>
          </div>
        </div>
      `).join('');

      return `<p><strong>Variant Title:</strong> ${result.variant_title}</p><div class="missing-zones-list d-flex flex-wrap gap-3">${unmatched}</div>`;
    }).join('');

    new CustomModal().show({
      id: "unmatchedModal",
      fullScreen: true,
      titleHtml: `<h5>${response.data.product_title}</h5>`,
      footerHtml: `
        <form id="matchPush" action="/submit" name="matchPush" method="POST" hidden>
        </form>
        <button type="submit" form="matchPush" class="btn btn-primary">Save</button>
      `,
      bodyHtml: `
        <div class="product-details">
          <div>
            <h3>Product Images</h3>
            <div class="product-images-list d-flex flex-wrap gap-3">${mainImages}</div>
          </div>
          <div>
            <h3>Unmatched Zones</h3>
            <div class="missing-zones-list-wrap">${unmatchedZones}</div>
          </div>
        </div>
      `
    });

    // Cache selectors
    const images = document.querySelectorAll('img[draggable="true"]');
    const boxes = document.querySelectorAll('.drop-zone');

    // Attach events
    images.forEach(img => {
      img.addEventListener('dragstart', handleDragStart);
      img.addEventListener('dragend', handleDragEnd);
    });

    const results = response.data.results;

    // Build a lookup map keyed by raw_img_url for O(1) access to images inside results
    const imageLookup = new Map();

    results.forEach(variant => {
      variant.data_images.forEach(image => {
        imageLookup.set(image.raw_img_url, { image, variant_id: variant.variant_id });
      });
    });

    boxes.forEach(box => {
      box.addEventListener('dragover', handleDragOver);
      box.addEventListener('dragleave', handleDragLeave);
      box.addEventListener('drop', handleDrop.bind(box, imageLookup));
    });

    
    document.addEventListener('submit', (event) => {
      const form = event.target;
      if (form?.name === 'matchPush') {
        event.preventDefault();

        // Remove all previous error highlights first
        document.querySelectorAll('.error').forEach(el => el.classList.remove('error'));

        // Flag to detect if any unmatched images found
        let hasUnmatched = false;

        // Loop through results to find any unmatched images
        results.forEach(variant => {
          variant.data_images.forEach(image => {
            if (image.matched === false) {
              hasUnmatched = true;
              const variantImageElement = document.querySelector(`img[src="${image.raw_img_url}"][data-variant-id="${variant.variant_id}"]`);
              if (variantImageElement) {
                const zoneWrapParent = variantImageElement.closest('.zone-wrap');
                if (zoneWrapParent) {
                  zoneWrapParent.classList.add('error');
                }
              }
            }
          });
        });

        if (hasUnmatched) {
          alert('There are images still unmatched. Please fix them before submitting.');
          return; // prevent submission
        }
        
        try {
          fetch("/api/populate-unmatched-images", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data: results, product_id: productId }),
          })
            .then(res => res.json())
            .then(data => {
              console.log(data);
              if (data.status === "success") {
                console.log('success');
              } else {
                console.log('not success');
              }
            })
            .catch(() => {
              console.log('catch error');
            });
        } catch {
          console.log('catch error');
        }
        
      }
    });

  }
}

class UIManager {
  constructor(handler) {
    this.handler = handler;
  }

  initialize() {
    this.setupIndividualButtons();
    this.setupBulkButton();
    this.setupImagePopups();
    this.setupDeleteButtons();
  }

  setupIndividualButtons() {
    document.querySelectorAll("button[data-populate-button]").forEach(button => {
      button.addEventListener("click", () => {
        if (button.disabled) return;
        this.setLoading(button);
        this.handler.populate(button);
      });
    });
  }

  setupDeleteButtons() {
    document.querySelectorAll("button[data-populate-button-delete]").forEach(button => {
      button.addEventListener("click", () => {
        if (button.disabled) return;
        this.setLoading(button);
        this.handler.delete(button);
      });
    });
  }

  setupBulkButton() {
    document.getElementById("perform_all")?.addEventListener("click", () => {
      const buttons = Array.from(document.querySelectorAll("button[data-populate-button]")).filter(btn => !btn.disabled);
      const bulk = new BulkProcessor(buttons, this.handler);
      bulk.start();
    });
  }

  setupImagePopups() {
    document.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-image-popup]");
      if (!button) return;

      this.setLoading(button);
      let imgUrl = button.nextElementSibling?.src;
      if (!imgUrl) {
        imgUrl = button.nextElementSibling.querySelector("img").src;
      }
      ZoomableImageModal.show(
        imgUrl.split("&width")[0],
        {
          zoomInIcon: getIcon('zoom-in'),
          zoomOutIcon: getIcon('zoom-out'),
          resetIcon: getIcon('zoom-reset'),
          maxScale: 5
        }
      );

      button.disabled = false;
      button.innerHTML = getIcon('eye');
    });
  }

  setLoading(button) {
    button.disabled = true;
    button.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>`;
  }
}

class BulkProcessor {
  constructor(buttons, handler) {
    this.buttons = buttons;
    this.handler = handler;
    this.total = buttons.length;
    this.completed = 0;
    this.errors = 0;
    this.maxConcurrency = 3;
    this.queueIndex = 0;
    this.inProgress = 0;

    this.setupModal();
  }

  setupModal() {
    this.modalEl = document.getElementById("bulkProgressModal") || this.createModal();
    this.modal = new bootstrap.Modal(this.modalEl);
    this.progressBar = this.modalEl.querySelector("#bulkProgressBar");
    this.statusText = this.modalEl.querySelector("#bulkProgressStatus");
    this.errorText = this.modalEl.querySelector("#bulkProgressErrors");
  }

  createModal() {
    const modal = document.createElement("div");
    modal.className = "modal fade";
    modal.id = "bulkProgressModal";
    modal.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header"><h5 class="modal-title">Bulk Image Population</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body">
            <div id="bulkProgressStatus">Starting...</div>
            <div class="progress mt-2"><div id="bulkProgressBar" class="progress-bar" role="progressbar" style="width: 0%">0%</div></div>
            <div id="bulkProgressErrors" class="text-danger mt-2"></div>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    return modal;
  }

  start() {
    if (this.total === 0) {
      this.progressBar.style.width = "100%";
      this.progressBar.classList.add("bg-warning");
      this.statusText.textContent = "⚠️ No products to process.";
      return;
    }

    this.buttons.forEach(button => {
      button.disabled = true;
      button.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status"></span>`;
    });

    this.modal.show();
    this.updateProgress();
    this.processNext();
  }

  async processNext() {
    while (this.inProgress < this.maxConcurrency && this.queueIndex < this.total) {
      const button = this.buttons[this.queueIndex++];
      this.inProgress++;

      const success = await this.handler.populate(button).catch(() => false);
      this.completed++;
      this.inProgress--;

      if (!success) this.errors++;

      this.updateProgress();
      this.processNext();
    }

    if (this.queueIndex >= this.total && this.inProgress === 0) {
      this.statusText.textContent = `✅ Completed ${this.completed} of ${this.total}`;
      this.progressBar.classList.add("bg-success");
    }
  }

  updateProgress() {
    const percent = Math.round((this.completed / this.total) * 100);
    this.progressBar.style.width = `${percent}%`;
    this.progressBar.textContent = `${percent}%`;
    this.statusText.textContent = `Processed ${this.completed} of ${this.total}`;
    this.errorText.textContent = this.errors > 0 ? `❌ ${this.errors} error(s)` : "";
  }
}

class CustomModal {
  static modalStack = [];

  constructor() {
    this.modalId = `customModal_${Date.now()}_${Math.random().toString(36).substring(2)}`;
    this.createModalElement();

    this.bsModal = new bootstrap.Modal(this.modalElement, {
      backdrop: 'static',
      keyboard: false
    });

    // Optional: allow manual close via internal button
    this.modalElement.addEventListener('click', (e) => {
      if (e.target.closest('[data-custom-close]')) {
        this.close();
      }
    });
  }

  createModalElement() {
    this.modalElement = document.createElement('div');
    this.modalElement.className = 'modal fade';
    this.modalElement.id = this.modalId;
    this.modalElement.tabIndex = -1;
    this.modalElement.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"></h5>
            <button type="button" class="btn-close" aria-label="Close" data-custom-close></button>
          </div>
          <div class="modal-body"></div>
          <div class="modal-footer"></div>
        </div>
      </div>
    `;
    document.body.appendChild(this.modalElement);
  }

  show({ titleHtml = '', bodyHtml = '', footerHtml = '', fullScreen = false, scrollable = false, extraDialogClass = '' }) {
    const dialog = this.modalElement.querySelector('.modal-dialog');
    dialog.className = 'modal-dialog'; // Reset

    if (fullScreen) dialog.classList.add('modal-fullscreen');
    if (scrollable) dialog.classList.add('modal-dialog-scrollable');
    if (extraDialogClass) dialog.classList.add(...extraDialogClass.split(' '));

    this.modalElement.querySelector('.modal-title').innerHTML = titleHtml;
    this.modalElement.querySelector('.modal-body').innerHTML = bodyHtml;
    this.modalElement.querySelector('.modal-footer').innerHTML = footerHtml;

    // Hide the current modal if there is one
    const currentModal = CustomModal.modalStack.at(-1);
    if (currentModal) {
      currentModal.bsModal.hide(); // Just hide, don't remove
    }

    CustomModal.modalStack.push(this);
    this.bsModal.show();
  }

  close() {
    // Listen for Bootstrap's hidden event before cleanup
    this.modalElement.addEventListener('hidden.bs.modal', () => {
      this.bsModal.dispose();
      this.modalElement.remove();

      CustomModal.modalStack.pop();

      // Restore previous modal if exists
      const previousModal = CustomModal.modalStack.at(-1);
      if (previousModal) {
        previousModal.bsModal.show();
      }
    }, { once: true });

    this.bsModal.hide(); // Let Bootstrap handle removing modal-open & body styles
  }
}

class ZoomableImageModal {
  static show(imgUrl, options = {}) {
    const {
      maxScale = 4,
      minScale = 1,
      id = 'zoomableImageModal',
      title = '',
      resetIcon = '⟳',
      zoomInIcon = '+',
      zoomOutIcon = '−',
    } = options;

    const zoomId = `zoomTarget-${Date.now()}`;
    const containerId = `zoomContainer-${Date.now()}`;

    const modal = new CustomModal();

    modal.show({
      id,
      titleHtml: `
        <div class="d-flex gap-2">
          <button class="btn btn-light btn-sm" data-action="zoom-in">${zoomInIcon}</button>
          <button class="btn btn-light btn-sm" data-action="zoom-out">${zoomOutIcon}</button>
          <button class="btn btn-light btn-sm" data-action="reset">${resetIcon}</button>
        </div>
      `,
      bodyHtml: `
        <div id="${containerId}" style="overflow: hidden; touch-action: none;">
          <div id="${zoomId}">
            <img src="${imgUrl}" class="img-fluid" alt="Zoomable Image">
          </div>
        </div>
      `
    });

    // defer Panzoom initialization until modal DOM is inserted
    setTimeout(() => {
      const zoomElem = document.getElementById(zoomId);
      const containerElem = document.getElementById(containerId);
      if (!zoomElem || !containerElem) return;

      const panzoom = Panzoom(zoomElem, {
        maxScale,
        minScale,
        contain: 'outside'
      });

      containerElem.addEventListener('wheel', panzoom.zoomWithWheel);

      const buttons = document.querySelectorAll(`[data-action]`);
      buttons.forEach((btn) => {
        const action = btn.getAttribute('data-action');
        if (action === 'zoom-in') btn.addEventListener('click', () => panzoom.zoomIn());
        if (action === 'zoom-out') btn.addEventListener('click', () => panzoom.zoomOut());
        if (action === 'reset') btn.addEventListener('click', () => panzoom.reset());
      });
    }, 50);
  }
}
