// PropFlow SaaS - Global Application JS

document.addEventListener('DOMContentLoaded', () => {
  // Command Palette Cmd+K listener
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      const modalElem = document.getElementById('commandPaletteModal');
      if (modalElem) {
        const modal = new bootstrap.Modal(modalElem);
        modal.show();
        setTimeout(() => {
          document.getElementById('commandSearchInput')?.focus();
        }, 150);
      }
    }
  });

  // Search API handler
  const searchInput = document.getElementById('commandSearchInput');
  const resultsContainer = document.getElementById('commandSearchResults');

  if (searchInput && resultsContainer) {
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();

      if (query.length < 2) {
        resultsContainer.innerHTML = '<div class="text-center text-muted p-3">Type to search properties, tenants, units, or maintenance...</div>';
        return;
      }

      debounceTimer = setTimeout(() => {
        fetch(`/api/search/?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => {
            if (!data.results || data.results.length === 0) {
              resultsContainer.innerHTML = '<div class="text-center text-muted p-3">No matching records found.</div>';
              return;
            }

            let html = '<div class="list-group list-group-flush">';
            data.results.forEach(item => {
              html += `
                <a href="${item.url}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center py-2 px-3">
                  <div>
                    <div class="fw-semibold text-dark" style="font-size: 0.78rem;">${item.title}</div>
                    <div class="text-muted" style="font-size: 0.68rem;">${item.subtitle}</div>
                  </div>
                  <span class="kp-status-badge kp-status-brand">${item.category}</span>
                </a>
              `;
            });
            html += '</div>';
            resultsContainer.innerHTML = html;
          })
          .catch(err => {
            console.error(err);
            resultsContainer.innerHTML = '<div class="text-center text-danger p-3">Error searching records.</div>';
          });
      }, 250);
    });
  }

  // Register PWA Service Worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/pwa/service-worker.js')
      .then(reg => console.log('PropFlow PWA ServiceWorker registered:', reg.scope))
      .catch(err => console.log('ServiceWorker registration failed:', err));
  }
});
