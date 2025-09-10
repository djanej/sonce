// Performance optimizations for news section

(function() {
    'use strict';

    // Register service worker for offline support
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/news/sw.js')
                .then(registration => console.log('SW registered:', registration))
                .catch(error => console.log('SW registration failed:', error));
        });
    }

    // Lazy load images with Intersection Observer
    function lazyLoadImages() {
        const images = document.querySelectorAll('img[loading="lazy"]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                        }
                        imageObserver.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });

            images.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for browsers without IntersectionObserver
            images.forEach(img => {
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                }
            });
        }
    }

    // Debounce function for scroll/resize events
    function debounce(func, wait, immediate) {
        let timeout;
        return function() {
            const context = this, args = arguments;
            const later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    }

    // Optimize scroll performance
    let ticking = false;
    function requestTick() {
        if (!ticking) {
            window.requestAnimationFrame(updateScrollProgress);
            ticking = true;
        }
    }

    function updateScrollProgress() {
        // Update scroll progress indicator if exists
        const progressBar = document.getElementById('scroll-progress');
        if (progressBar) {
            const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            progressBar.style.width = scrolled + '%';
        }
        ticking = false;
    }

    // Prefetch links on hover
    function prefetchLinks() {
        const links = document.querySelectorAll('a[href^="/news/"]');
        
        links.forEach(link => {
            link.addEventListener('mouseenter', () => {
                const prefetchLink = document.createElement('link');
                prefetchLink.rel = 'prefetch';
                prefetchLink.href = link.href;
                document.head.appendChild(prefetchLink);
            }, { once: true });
        });
    }

    // Optimize animations for users who prefer reduced motion
    function respectReducedMotion() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        
        if (prefersReducedMotion.matches) {
            document.documentElement.classList.add('reduce-motion');
        }
        
        prefersReducedMotion.addEventListener('change', (e) => {
            if (e.matches) {
                document.documentElement.classList.add('reduce-motion');
            } else {
                document.documentElement.classList.remove('reduce-motion');
            }
        });
    }

    // Cache API responses in sessionStorage
    function cacheAPIResponse(url, data) {
        try {
            const cache = {
                data: data,
                timestamp: Date.now()
            };
            sessionStorage.setItem('cache_' + btoa(url), JSON.stringify(cache));
        } catch (e) {
            // SessionStorage might be full or disabled
            console.warn('Failed to cache response:', e);
        }
    }

    function getCachedResponse(url, maxAge = 300000) { // 5 minutes default
        try {
            const cached = sessionStorage.getItem('cache_' + btoa(url));
            if (cached) {
                const cache = JSON.parse(cached);
                if (Date.now() - cache.timestamp < maxAge) {
                    return cache.data;
                }
            }
        } catch (e) {
            console.warn('Failed to get cached response:', e);
        }
        return null;
    }

    // Optimize fetch requests
    window.optimizedFetch = function(url, options = {}) {
        // Check cache first for GET requests
        if (!options.method || options.method === 'GET') {
            const cached = getCachedResponse(url);
            if (cached) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve(cached),
                    text: () => Promise.resolve(JSON.stringify(cached))
                });
            }
        }

        return fetch(url, options).then(response => {
            if (response.ok && (!options.method || options.method === 'GET')) {
                response.clone().json().then(data => {
                    cacheAPIResponse(url, data);
                }).catch(() => {});
            }
            return response;
        });
    };

    // Initialize performance optimizations
    function init() {
        lazyLoadImages();
        prefetchLinks();
        respectReducedMotion();
        
        // Optimize scroll events
        window.addEventListener('scroll', requestTick, { passive: true });
        
        // Re-run lazy loading when new content is added
        const observer = new MutationObserver(debounce(() => {
            lazyLoadImages();
            prefetchLinks();
        }, 100));
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export for use in other scripts
    window.NewsPerformance = {
        lazyLoadImages,
        prefetchLinks,
        cacheAPIResponse,
        getCachedResponse,
        optimizedFetch: window.optimizedFetch
    };
})();