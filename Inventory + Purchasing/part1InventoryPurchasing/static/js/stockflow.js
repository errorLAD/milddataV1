// StockFlow Global JavaScript & StockFlow AI Copilot Engine

document.addEventListener('DOMContentLoaded', () => {
  initGlobalSearch();
  initDynamicForms();
});

// --- GLOBAL SEARCH ---
function initGlobalSearch() {
  const searchInput = document.getElementById('global-search-input');
  const resultsContainer = document.getElementById('global-search-results');

  if (!searchInput || !resultsContainer) return;

  let debounceTimer;

  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    const query = e.target.value.trim();

    if (query.length < 2) {
      resultsContainer.style.display = 'none';
      resultsContainer.innerHTML = '';
      return;
    }

    debounceTimer = setTimeout(() => {
      fetch(`/api/search/?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
          if (data.results && data.results.length > 0) {
            resultsContainer.innerHTML = data.results.map(item => `
              <a href="${item.url}" class="search-result-item">
                <div class="search-result-type">${item.type}</div>
                <div class="search-result-title">${item.title}</div>
                <div class="search-result-subtitle">${item.subtitle}</div>
              </a>
            `).join('');
            resultsContainer.style.display = 'block';
          } else {
            resultsContainer.innerHTML = `<div class="p-3 text-center text-muted">No matches found for "${query}"</div>`;
            resultsContainer.style.display = 'block';
          }
        });
    }, 250);
  });

  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
      resultsContainer.style.display = 'none';
    }
  });

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();
    }
  });
}

// --- DYNAMIC INVOICE & PO FORM ROW CALCULATIONS ---
function initDynamicForms() {
  const itemsTable = document.getElementById('line-items-body');
  if (!itemsTable) return;

  itemsTable.addEventListener('input', (e) => {
    if (e.target.matches('.calc-input')) {
      recalculateLineRows();
    }
  });

  itemsTable.addEventListener('change', (e) => {
    if (e.target.matches('.product-select')) {
      const selectedOpt = e.target.options[e.target.selectedIndex];
      const price = selectedOpt.getAttribute('data-price') || '0.00';
      const row = e.target.closest('tr');
      const priceInput = row.querySelector('.unit-price-input');
      if (priceInput) {
        priceInput.value = price;
        recalculateLineRows();
      }
    }
  });
}

function addLineItemRow() {
  const itemsTable = document.getElementById('line-items-body');
  const templateRow = itemsTable.querySelector('tr');
  if (!templateRow) return;

  const newRow = templateRow.cloneNode(true);
  newRow.querySelectorAll('input').forEach(i => i.value = i.defaultValue || '');
  itemsTable.appendChild(newRow);
  recalculateLineRows();
}

function removeLineItemRow(btn) {
  const itemsTable = document.getElementById('line-items-body');
  if (itemsTable.querySelectorAll('tr').length > 1) {
    btn.closest('tr').remove();
    recalculateLineRows();
  }
}

function recalculateLineRows() {
  let grandSub = 0;

  document.querySelectorAll('#line-items-body tr').forEach(row => {
    const qtyInput = row.querySelector('.qty-input');
    const priceInput = row.querySelector('.unit-price-input');
    const totalCell = row.querySelector('.line-total-cell');

    if (qtyInput && priceInput && totalCell) {
      const qty = parseFloat(qtyInput.value) || 0;
      const price = parseFloat(priceInput.value) || 0;
      const total = qty * price;
      totalCell.innerText = total.toFixed(2);
      grandSub += total;
    }
  });

  const subtotalEl = document.getElementById('summary-subtotal');
  const grandTotalEl = document.getElementById('summary-grandtotal');

  if (subtotalEl) subtotalEl.innerText = grandSub.toFixed(2);
  if (grandTotalEl) grandTotalEl.innerText = grandSub.toFixed(2);
}

// --- BARCODE SCANNER CAMERA INTEGRATION ---
function openBarcodeScannerModal() {
  const modal = document.getElementById('barcode-scanner-modal');
  if (!modal) return;

  modal.style.display = 'flex';
  const video = document.getElementById('barcode-video');

  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
      .then(stream => {
        video.srcObject = stream;
        video.play();
      })
      .catch(err => {
        alert('Camera access denied or unavailable: ' + err.message);
      });
  }
}

function closeBarcodeScannerModal() {
  const modal = document.getElementById('barcode-scanner-modal');
  if (!modal) return;
  modal.style.display = 'none';

  const video = document.getElementById('barcode-video');
  if (video && video.srcObject) {
    video.srcObject.getTracks().forEach(track => track.stop());
  }
}

function triggerManualBarcodeLookup() {
  const code = document.getElementById('manual-barcode-input').value.trim();
  if (!code) return;

  fetch(`/api/barcode-lookup/?code=${encodeURIComponent(code)}`)
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        window.location.href = data.product.detail_url;
      } else {
        alert(data.error);
      }
    });
}

// --- STOCKFLOW AI COPILOT DRAWER & CHAT ENGINE ---
function toggleAICopilotDrawer() {
  const drawer = document.getElementById('ai-copilot-drawer');
  const backdrop = document.getElementById('mobile-drawer-backdrop');
  if (drawer) {
    const isOpen = drawer.style.transform === 'translateX(0px)' || drawer.style.transform === 'translateX(0%)';
    drawer.style.transform = isOpen ? 'translateX(100%)' : 'translateX(0%)';
    if (backdrop) backdrop.classList.toggle('active', !isOpen);
  }
}

function askAICopilot(promptText) {
  const input = document.getElementById('ai-input-prompt');
  if (input) {
    input.value = promptText;
    sendAICopilotQuery();
  }
}

function sendAICopilotQuery() {
  const input = document.getElementById('ai-input-prompt');
  const chatBody = document.getElementById('ai-chat-body');
  if (!input || !chatBody) return;

  const prompt = input.value.trim();
  if (!prompt) return;

  // Append User message
  const userMsgNode = document.createElement('div');
  userMsgNode.style.cssText = 'background: var(--brand-soft); border: 1px solid var(--brand-soft-border); padding: 0.65rem; border-radius: var(--radius-sm); font-size: 0.72rem; align-self: flex-end; width: 85%;';
  userMsgNode.innerHTML = `<strong>You:</strong> ${prompt}`;
  chatBody.appendChild(userMsgNode);
  input.value = '';

  // Append Thinking Indicator
  const thinkingNode = document.createElement('div');
  thinkingNode.style.cssText = 'background: var(--surface-alt); padding: 0.65rem; border-radius: var(--radius-sm); font-size: 0.68rem; color: var(--text-secondary);';
  thinkingNode.innerText = '🤖 Analyzing live company database...';
  chatBody.appendChild(thinkingNode);
  chatBody.scrollTop = chatBody.scrollHeight;

  fetch(`/api/ai/copilot/?prompt=${encodeURIComponent(prompt)}`)
    .then(res => res.json())
    .then(data => {
      thinkingNode.remove();
      if (data.success) {
        const aiMsgNode = document.createElement('div');
        aiMsgNode.style.cssText = 'background: var(--surface); border: 1px solid var(--border); padding: 0.75rem; border-radius: var(--radius-sm); font-size: 0.72rem; line-height: 1.45; white-space: pre-line;';
        aiMsgNode.innerHTML = `<strong>StockFlow AI:</strong>\n${data.answer}`;

        // Append Human-in-the-Loop Action Proposal Card if present
        if (data.action_proposal) {
          const prop = data.action_proposal;
          const propNode = document.createElement('div');
          propNode.style.cssText = 'margin-top: 0.6rem; padding: 0.65rem; background: var(--warning-soft); border: 1px solid var(--warning-border); border-radius: var(--radius-sm);';
          propNode.innerHTML = `
            <div style="font-weight: 700; font-size: 0.68rem; color: var(--warning); margin-bottom: 0.2rem;">⚡ Action Proposal (Requires Human Confirmation)</div>
            <div style="font-weight: 650; font-size: 0.72rem;">${prop.title}</div>
            <div style="font-size: 0.65rem; color: var(--text-secondary); margin-bottom: 0.5rem;">${prop.description}</div>
            <a href="${prop.action_url}" class="btn btn-primary btn-sm" style="width: 100%;">Confirm & Proceed →</a>
          `;
          aiMsgNode.appendChild(propNode);
        }

        chatBody.appendChild(aiMsgNode);
      } else {
        const errNode = document.createElement('div');
        errNode.style.cssText = 'color: var(--danger); font-size: 0.68rem;';
        errNode.innerText = `AI Error: ${data.error}`;
        chatBody.appendChild(errNode);
      }
      chatBody.scrollTop = chatBody.scrollHeight;
    });
}
