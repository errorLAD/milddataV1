// Dashboard & Global Search Interactive Scripts
document.addEventListener('DOMContentLoaded', () => {
    // Register PWA Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(reg => console.log('Machine OS PWA ServiceWorker registered', reg.scope))
            .catch(err => console.error('PWA SW registration failed', err));
    }

    // Modal toggles
    document.querySelectorAll('[data-modal-target]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = trigger.getAttribute('data-modal-target');
            const modal = document.getElementById(targetId);
            if (modal) {
                modal.classList.add('active');
                if (targetId === 'modal-global-search') {
                    const searchInput = document.getElementById('global-search-input');
                    if (searchInput) searchInput.focus();
                }
            }
        });
    });

    document.querySelectorAll('[data-modal-close]').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            const modal = closeBtn.closest('.kp-modal-backdrop');
            if (modal) modal.classList.remove('active');
        });
    });

    // Keyboard Shortcuts (Ctrl + K or / to trigger Global Search)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            const modal = document.getElementById('modal-global-search');
            if (modal) {
                modal.classList.add('active');
                const searchInput = document.getElementById('global-search-input');
                if (searchInput) searchInput.focus();
            }
        }
        if (e.key === 'Escape') {
            document.querySelectorAll('.kp-modal-backdrop.active').forEach(m => m.classList.remove('active'));
            const drawer = document.getElementById('mobile-drawer');
            if (drawer) drawer.classList.remove('active');
        }
    });

    // Global Search AJAX logic
    const searchInput = document.getElementById('global-search-input');
    const searchResults = document.getElementById('global-search-results');
    let debounceTimer;

    if (searchInput && searchResults) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            const query = searchInput.value.trim();

            if (query.length < 2) {
                searchResults.innerHTML = `
                    <div style="text-align: center; color: var(--text-tertiary); padding: 2rem; font-size: 0.72rem;">
                        Type 2 or more characters to search across equipment, permits, refuel logs, and invoices...
                    </div>
                `;
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`/search/api/?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (!data.results || data.results.length === 0) {
                            searchResults.innerHTML = `
                                <div style="text-align: center; color: var(--text-tertiary); padding: 2rem; font-size: 0.72rem;">
                                    No records matching "${query}" found.
                                </div>
                            `;
                            return;
                        }

                        let html = '';
                        data.results.forEach(item => {
                            html += `
                                <a href="${item.url}" style="display: flex; align-items: center; justify-content: space-between; padding: 0.6rem 0.85rem; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); margin-bottom: 0.4rem; text-decoration: none; transition: background 0.15s ease;">
                                    <div>
                                        <div style="font-weight: 650; font-size: 0.75rem; color: var(--brand);">${item.title}</div>
                                        <div style="font-size: 0.66rem; color: var(--text-secondary); margin-top: 0.1rem;">${item.subtitle}</div>
                                    </div>
                                    <span class="kp-badge kp-badge-brand">${item.badge}</span>
                                </a>
                            `;
                        });
                        searchResults.innerHTML = html;
                    })
                    .catch(err => {
                        searchResults.innerHTML = `<div style="text-align: center; color: var(--danger); padding: 1rem;">Search error occurred.</div>`;
                    });
            }, 250);
        });
    }

    // Mobile Navigation Drawer Toggles
    const drawerToggle = document.getElementById('mobile-drawer-toggle');
    const drawerClose = document.getElementById('mobile-drawer-close');
    const drawer = document.getElementById('mobile-drawer');

    if (drawerToggle && drawer) {
        drawerToggle.addEventListener('click', () => drawer.classList.add('active'));
    }

    if (drawerClose && drawer) {
        drawerClose.addEventListener('click', () => drawer.classList.remove('active'));
    }

    if (drawer) {
        drawer.addEventListener('click', (e) => {
            if (e.target === drawer) drawer.classList.remove('active');
        });
    }
});
