// Site configuration — fill in IDs after creating accounts
const GA_MEASUREMENT_ID = '';
const BLOG_AD_CLIENT = 'ca-pub-4668633509273232';
const BLOG_SIDEBAR_AD_SLOT = '8015849679';
const BLOG_BOTTOM_AD_SLOT = '7377555423';

const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

document.addEventListener('DOMContentLoaded', function() {
    initAnalytics();
    initBlogAds();
    initNavbar();
    initSmoothScroll();
    initReveal();
    initCounters();
    initTerminal();
    initCarousels();
});

/* ---------------------------------------------------------
   Navbar: mobile menu + scrolled state
   --------------------------------------------------------- */
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    if (navbar) {
        const onScroll = function() {
            navbar.classList.toggle('scrolled', window.scrollY > 24);
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            navMenu.classList.toggle('active');

            const spans = hamburger.querySelectorAll('span');
            if (navMenu.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });

        // Close menu when clicking on a link
        const navLinks = document.querySelectorAll('.nav-menu a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
                const spans = hamburger.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            });
        });
    }
}

/* ---------------------------------------------------------
   Smooth scroll for anchor links
   --------------------------------------------------------- */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: REDUCED_MOTION ? 'auto' : 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

/* ---------------------------------------------------------
   Scroll reveal — [data-reveal] plus auto-tagged cards
   --------------------------------------------------------- */
function initReveal() {
    // Auto-tag common cards on pages whose markup doesn't carry data-reveal
    const autoSelectors = [
        '.portfolio-item', '.blog-card', '.feature-card', '.service-item',
        '.result-card', '.pipeline-step', '.tech-card-product', '.practice-card',
        '.about-stat', '.spec-card', '.product-stat'
    ];
    autoSelectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
            if (!el.hasAttribute('data-reveal')) {
                el.setAttribute('data-reveal', '');
            }
        });
    });

    const targets = document.querySelectorAll('[data-reveal]');
    if (!targets.length) {
        return;
    }

    if (REDUCED_MOTION || !('IntersectionObserver' in window)) {
        targets.forEach(el => el.classList.add('revealed'));
        return;
    }

    // Stagger siblings that share a parent
    const parentCounts = new Map();
    targets.forEach(el => {
        const parent = el.parentElement;
        const idx = parentCounts.get(parent) || 0;
        el.style.setProperty('--reveal-delay', (Math.min(idx, 5) * 0.09) + 's');
        parentCounts.set(parent, idx + 1);
    });

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    targets.forEach(el => observer.observe(el));
}

/* ---------------------------------------------------------
   Count-up stats — [data-count]
   --------------------------------------------------------- */
function initCounters() {
    const counters = document.querySelectorAll('[data-count]');
    if (!counters.length || REDUCED_MOTION || !('IntersectionObserver' in window)) {
        return;
    }

    const animate = function(el) {
        const target = parseInt(el.getAttribute('data-count'), 10);
        if (isNaN(target)) {
            return;
        }
        const duration = 1300;
        const start = performance.now();
        const tick = function(now) {
            const p = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(eased * target);
            if (p < 1) {
                requestAnimationFrame(tick);
            }
        };
        requestAnimationFrame(tick);
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animate(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.4 });

    counters.forEach(el => observer.observe(el));
}

/* ---------------------------------------------------------
   Hero terminal typing animation
   --------------------------------------------------------- */
function initTerminal() {
    const body = document.getElementById('terminal-body');
    if (!body) {
        return;
    }

    const lines = [
        { type: 'cmd', text: 'rebel new --client you' },
        { type: 'out', html: '<span class="t-dim">scaffolding project…</span>' },
        { type: 'out', html: '<span class="t-ok">✓</span> ui         <span class="t-dim">designed &amp; responsive</span>' },
        { type: 'out', html: '<span class="t-ok">✓</span> backend    <span class="t-dim">wired &amp; tested</span>' },
        { type: 'out', html: '<span class="t-ok">✓</span> payments   <span class="t-dim">stripe · live mode</span>' },
        { type: 'cmd', text: 'rebel deploy --prod' },
        { type: 'out', html: '<span class="t-accent">→</span> build <span class="t-dim">passed in 1.2s</span>' },
        { type: 'out', html: '<span class="t-ok">✓</span> deployed — <span class="t-ok">0 errors, 0 excuses</span>' },
        { type: 'cmd', text: 'status' },
        { type: 'out', html: '<span class="t-ok">●</span> live <span class="t-dim">· monitored · maintained</span>' }
    ];

    const renderStatic = function() {
        body.innerHTML = lines.map(function(line) {
            return line.type === 'cmd'
                ? '<div class="t-line"><span class="t-prompt">$ </span><span class="t-cmd">' + line.text + '</span></div>'
                : '<div class="t-line">' + line.html + '</div>';
        }).join('') + '<div class="t-line"><span class="t-prompt">$ </span><span class="t-caret"></span></div>';
    };

    if (REDUCED_MOTION || !('IntersectionObserver' in window)) {
        renderStatic();
        return;
    }

    let started = false;
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting && !started) {
                started = true;
                observer.disconnect();
                playTerminal(body, lines);
            }
        });
    }, { threshold: 0.3 });
    observer.observe(body);
}

function playTerminal(body, lines) {
    let i = 0;

    const caretLine = function() {
        const div = document.createElement('div');
        div.className = 't-line';
        div.innerHTML = '<span class="t-prompt">$ </span><span class="t-caret"></span>';
        return div;
    };

    const next = function() {
        if (i >= lines.length) {
            body.appendChild(caretLine());
            return;
        }
        const line = lines[i++];
        const div = document.createElement('div');
        div.className = 't-line';
        body.appendChild(div);

        if (line.type === 'cmd') {
            div.innerHTML = '<span class="t-prompt">$ </span><span class="t-cmd"></span><span class="t-caret"></span>';
            const cmdEl = div.querySelector('.t-cmd');
            const caret = div.querySelector('.t-caret');
            let c = 0;
            const typeChar = function() {
                if (c < line.text.length) {
                    cmdEl.textContent += line.text.charAt(c++);
                    setTimeout(typeChar, 34 + Math.random() * 40);
                } else {
                    caret.remove();
                    setTimeout(next, 300);
                }
            };
            setTimeout(typeChar, 250);
        } else {
            div.innerHTML = line.html;
            setTimeout(next, 190);
        }
    };

    next();
}

/* ---------------------------------------------------------
   Analytics
   --------------------------------------------------------- */
function initAnalytics() {
    if (!GA_MEASUREMENT_ID) {
        return;
    }

    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_MEASUREMENT_ID;
    document.head.appendChild(script);

    window.dataLayer = window.dataLayer || [];
    window.gtag = function() {
        window.dataLayer.push(arguments);
    };
    window.gtag('js', new Date());
    window.gtag('config', GA_MEASUREMENT_ID);
}

/* ---------------------------------------------------------
   Blog ads (AdSense)
   --------------------------------------------------------- */
function initBlogAds() {
    if (!document.querySelector('script[src*="adsbygoogle"]')) {
        return;
    }

    const sectionEl = document.querySelector('.blog-article');
    if (!sectionEl) {
        return;
    }

    const container = sectionEl.querySelector('.container');
    const mainEl = container && container.querySelector('.article-wrapper');
    if (!container || !mainEl || container.querySelector('.blog-layout')) {
        return;
    }

    const layout = document.createElement('div');
    layout.className = 'blog-layout';

    const leftSidebar = createAdSidebar('blog-sidebar-left');
    const rightSidebar = createAdSidebar('blog-sidebar-right');

    mainEl.classList.add('blog-main');
    container.insertBefore(layout, mainEl);
    layout.appendChild(leftSidebar);
    layout.appendChild(mainEl);
    layout.appendChild(rightSidebar);

    const footerNav = mainEl.querySelector('.article-footer-nav');
    const bottomAd = createBottomAdUnit();
    if (footerNav) {
        mainEl.insertBefore(bottomAd, footerNav);
    } else {
        mainEl.appendChild(bottomAd);
    }

    document.querySelectorAll('.adsbygoogle').forEach(function(ins) {
        // Skip slots hidden at this viewport (e.g. sidebars < 1200px) —
        // pushing them throws "No slot size for availableWidth=0"
        if (ins.offsetWidth === 0) {
            return;
        }
        try {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
        } catch (error) {
            console.error('AdSense init failed:', error);
        }
    });
}

function createAdSidebar(className) {
    const sidebar = document.createElement('aside');
    sidebar.className = 'blog-sidebar ' + className;
    sidebar.setAttribute('aria-label', 'Advertisement');
    sidebar.appendChild(createSidebarAdUnit());
    return sidebar;
}

function createSidebarAdUnit() {
    const wrapper = document.createElement('div');
    wrapper.className = 'sidebar-ad-unit';

    const ins = document.createElement('ins');
    ins.className = 'adsbygoogle';
    ins.style.display = 'block';
    ins.setAttribute('data-ad-client', BLOG_AD_CLIENT);
    ins.setAttribute('data-ad-slot', BLOG_SIDEBAR_AD_SLOT);
    ins.setAttribute('data-ad-format', 'auto');
    ins.setAttribute('data-full-width-responsive', 'true');

    wrapper.appendChild(ins);
    return wrapper;
}

function createBottomAdUnit() {
    const wrapper = document.createElement('div');
    wrapper.className = 'article-bottom-ad';

    const ins = document.createElement('ins');
    ins.className = 'adsbygoogle';
    ins.style.display = 'block';
    ins.setAttribute('data-ad-client', BLOG_AD_CLIENT);
    ins.setAttribute('data-ad-slot', BLOG_BOTTOM_AD_SLOT);
    ins.setAttribute('data-ad-format', 'auto');
    ins.setAttribute('data-full-width-responsive', 'true');

    wrapper.appendChild(ins);
    return wrapper;
}

/* ---------------------------------------------------------
   Screenshot carousels
   --------------------------------------------------------- */
function initCarousels() {
    const carousels = document.querySelectorAll('.screenshot-carousel');
    carousels.forEach(carousel => {
        let currentIndex = 0;
        const slides = carousel.querySelectorAll('.screenshot-slide');

        if (slides.length > 1 && !REDUCED_MOTION) {
            setInterval(() => {
                currentIndex = (currentIndex + 1) % slides.length;
                showSlide(carousel.id, currentIndex);
            }, 4000);
        }
    });
}

function changeSlide(carouselId, direction) {
    const carousel = document.getElementById(carouselId);
    const slides = carousel.querySelectorAll('.screenshot-slide');
    let currentIndex = 0;

    slides.forEach((slide, index) => {
        if (slide.classList.contains('active')) {
            currentIndex = index;
        }
    });

    let newIndex = currentIndex + direction;
    if (newIndex < 0) {
        newIndex = slides.length - 1;
    } else if (newIndex >= slides.length) {
        newIndex = 0;
    }

    showSlide(carouselId, newIndex);
}

function currentSlide(carouselId, index) {
    showSlide(carouselId, index);
}

function showSlide(carouselId, index) {
    const carousel = document.getElementById(carouselId);
    const slides = carousel.querySelectorAll('.screenshot-slide');
    const dots = carousel.querySelectorAll('.dot');

    slides.forEach(slide => slide.classList.remove('active'));
    dots.forEach(dot => dot.classList.remove('active'));

    if (slides[index]) {
        slides[index].classList.add('active');
    }
    if (dots[index]) {
        dots[index].classList.add('active');
    }
}
