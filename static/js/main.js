/**
 * FandomVerse - Interactive Client Application
 * Master JavaScript Engine
 * Conceived & Crafted by Alishba Shahid
 * Contact: marinacaipher09@gmail.com
 */

document.addEventListener('DOMContentLoaded', () => {
    initPreloader();
    initHeaderScroll();
    initUserMenu();
    initMobileDrawer();
    initFlashAlerts();
    initLiveSearch();
    initLikeSystem();
    initStatCounters();
    initBackToTop();
    initFaqAccordion();
});

/* ── Preloader ────────────────────────────────────────────────────────── */
function initPreloader() {
    const preloader = document.getElementById('preloader');
    if (!preloader) return;
    window.addEventListener('load', () => {
        setTimeout(() => {
            preloader.classList.add('hidden');
        }, 300);
    });
    // Fallback if window load already fired
    setTimeout(() => {
        if (!preloader.classList.contains('hidden')) {
            preloader.classList.add('hidden');
        }
    }, 1200);
}

/* ── Header Scroll Blur & Sticky Effect ────────────────────────────────── */
function initHeaderScroll() {
    const header = document.getElementById('mainHeader');
    if (!header) return;
    window.addEventListener('scroll', () => {
        if (window.scrollY > 40) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }, { passive: true });
}

/* ── User Dropdown Menu ───────────────────────────────────────────────── */
function initUserMenu() {
    const wrapper = document.getElementById('userMenuWrapper');
    const btn = document.getElementById('userMenuBtn');
    if (!wrapper || !btn) return;

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = wrapper.classList.toggle('open');
        btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) {
            wrapper.classList.remove('open');
            btn.setAttribute('aria-expanded', 'false');
        }
    });
}

/* ── Mobile Drawer Navigation ─────────────────────────────────────────── */
function initMobileDrawer() {
    const toggleBtn = document.getElementById('mobileToggleBtn');
    const drawer = document.getElementById('mobileDrawer');
    const closeBtn = document.getElementById('mobileCloseBtn');

    if (!toggleBtn || !drawer) return;

    toggleBtn.addEventListener('click', () => {
        drawer.classList.add('open');
        document.body.style.overflow = 'hidden';
    });

    const closeDrawer = () => {
        drawer.classList.remove('open');
        document.body.style.overflow = '';
    };

    if (closeBtn) {
        closeBtn.addEventListener('click', closeDrawer);
    }

    document.addEventListener('click', (e) => {
        if (drawer.classList.contains('open') && !drawer.contains(e.target) && !toggleBtn.contains(e.target)) {
            closeDrawer();
        }
    });
}

/* ── Auto-dismiss Flash Alerts ────────────────────────────────────────── */
function initFlashAlerts() {
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(50px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });
}

/* ── Live AJAX Search with Autocomplete Dropdown ──────────────────────── */
function initLiveSearch() {
    const searchInput = document.getElementById('globalSearch');
    const dropdown = document.getElementById('searchDropdown');
    if (!searchInput || !dropdown) return;

    let debounceTimer = null;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(debounceTimer);

        if (query.length < 2) {
            dropdown.innerHTML = '';
            dropdown.classList.remove('active');
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/api/search/quick?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    dropdown.innerHTML = '';
                    if (!data || data.length === 0) {
                        dropdown.innerHTML = `
                            <div class="autocomplete-item text-muted">
                                <i class="fas fa-search autocomplete-item-icon"></i>
                                <div>No fandoms or discussions found for "${escapeHtml(query)}"</div>
                            </div>
                        `;
                        dropdown.classList.add('active');
                        return;
                    }

                    data.forEach(item => {
                        const a = document.createElement('a');
                        a.href = item.url;
                        a.className = 'autocomplete-item';
                        a.innerHTML = `
                            <div class="autocomplete-item-icon">${item.icon || '✨'}</div>
                            <div class="autocomplete-item-info">
                                <div class="autocomplete-item-title">${escapeHtml(item.name)}</div>
                                <div class="autocomplete-item-type">${escapeHtml(item.type)}</div>
                            </div>
                            <i class="fas fa-arrow-right text-muted" style="font-size: 0.8rem;"></i>
                        `;
                        dropdown.appendChild(a);
                    });

                    // View all results link
                    const viewAll = document.createElement('a');
                    viewAll.href = `/search?q=${encodeURIComponent(query)}`;
                    viewAll.className = 'autocomplete-item text-center';
                    viewAll.style.justifyContent = 'center';
                    viewAll.style.background = 'rgba(108, 92, 231, 0.15)';
                    viewAll.innerHTML = `<strong>View all results for "${escapeHtml(query)}" &rarr;</strong>`;
                    dropdown.appendChild(viewAll);

                    dropdown.classList.add('active');
                })
                .catch(err => {
                    console.error('Search error:', err);
                });
        }, 250);
    });

    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/* ── Interactive AJAX Post Liking ─────────────────────────────────────── */
function initLikeSystem() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.like-btn');
        if (!btn) return;

        e.preventDefault();
        const postId = btn.dataset.postId;
        if (!postId) return;

        // Check if user is logged in
        fetch(`/post/${postId}/like`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.redirected) {
                // Not authenticated, redirect to login
                window.location.href = response.url;
                return;
            }
            return response.json();
        })
        .then(data => {
            if (!data) return;
            const countEl = btn.querySelector('.like-count');
            const icon = btn.querySelector('i');

            if (data.liked) {
                btn.classList.add('liked');
                if (icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                }
            } else {
                btn.classList.remove('liked');
                if (icon) {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
            }

            if (countEl) {
                countEl.textContent = data.count;
            }
        })
        .catch(err => {
            console.error('Like error:', err);
        });
    });
}

/* ── Animated Statistics Counter Bar ──────────────────────────────────── */
function initStatCounters() {
    const counters = document.querySelectorAll('.stat-number');
    if (!counters.length) return;

    let animated = false;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !animated) {
                animated = true;
                counters.forEach(counter => {
                    const target = parseInt(counter.dataset.count, 10);
                    if (isNaN(target)) return;

                    let current = 0;
                    const duration = 1500;
                    const stepTime = 25;
                    const steps = duration / stepTime;
                    const increment = target / steps;

                    const timer = setInterval(() => {
                        current += increment;
                        if (current >= target) {
                            counter.textContent = target.toLocaleString();
                            clearInterval(timer);
                        } else {
                            counter.textContent = Math.floor(current).toLocaleString();
                        }
                    }, stepTime);
                });
            }
        });
    }, { threshold: 0.3 });

    const statsSection = document.querySelector('.stats-bar-wrapper');
    if (statsSection) {
        observer.observe(statsSection);
    }
}

/* ── Back to Top Button ───────────────────────────────────────────────── */
function initBackToTop() {
    const btn = document.getElementById('backToTop');
    if (!btn) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 400) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    }, { passive: true });

    btn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/* ── Interactive FAQ Accordion ────────────────────────────────────────── */
function initFaqAccordion() {
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        if (!question) return;
        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            faqItems.forEach(i => i.classList.remove('active'));
            if (!isActive) {
                item.classList.add('active');
            }
        });
    });
}
