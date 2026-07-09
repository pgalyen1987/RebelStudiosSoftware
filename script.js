// Site configuration — fill in IDs after creating accounts
const GA_MEASUREMENT_ID = '';
const BLOG_AD_CLIENT = 'ca-pub-4668633509273232';
const BLOG_SIDEBAR_AD_SLOT = '8015849679';
const BLOG_BOTTOM_AD_SLOT = '7377555423';

const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

document.addEventListener('DOMContentLoaded', function() {
    initAnalytics();
    initBlogAds();
    initArticleShare();
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
   Article share buttons
   --------------------------------------------------------- */
function initArticleShare() {
    const article = document.querySelector('.blog-article .article-wrapper');
    if (!article || article.querySelector('.article-share')) {
        return;
    }

    const footerNav = article.querySelector('.article-footer-nav');
    if (!footerNav) {
        return;
    }

    const url = getArticleShareUrl();
    const title = getArticleShareTitle();
    const share = document.createElement('div');
    share.className = 'article-share';
    share.setAttribute('aria-label', 'Share this article');

    const label = document.createElement('span');
    label.className = 'article-share-label';
    label.textContent = 'Share';
    share.appendChild(label);

    const actions = document.createElement('div');
    actions.className = 'article-share-actions';
    actions.appendChild(createShareLink('x', 'Share on X', buildShareUrl('x', url, title)));
    actions.appendChild(createShareLink('linkedin', 'Share on LinkedIn', buildShareUrl('linkedin', url, title)));
    actions.appendChild(createShareLink('facebook', 'Share on Facebook', buildShareUrl('facebook', url, title)));
    actions.appendChild(createCopyLinkButton(url));
    share.appendChild(actions);

    footerNav.parentNode.insertBefore(share, footerNav);
}

function getArticleShareUrl() {
    const canonical = document.querySelector('link[rel="canonical"]');
    return canonical ? canonical.href : window.location.href;
}

function getArticleShareTitle() {
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle && ogTitle.content) {
        return ogTitle.content;
    }

    return document.title.replace(/\s*-\s*Rebel Studios Software\s*$/, '');
}

function buildShareUrl(platform, url, title) {
    const encodedUrl = encodeURIComponent(url);
    const encodedTitle = encodeURIComponent(title);

    if (platform === 'x') {
        return 'https://twitter.com/intent/tweet?url=' + encodedUrl + '&text=' + encodedTitle;
    }
    if (platform === 'linkedin') {
        return 'https://www.linkedin.com/sharing/share-offsite/?url=' + encodedUrl;
    }
    if (platform === 'facebook') {
        return 'https://www.facebook.com/sharer/sharer.php?u=' + encodedUrl;
    }

    return url;
}

function createShareLink(platform, label, href) {
    const link = document.createElement('a');
    link.className = 'article-share-btn article-share-btn-' + platform;
    link.href = href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.setAttribute('aria-label', label);
    link.innerHTML = getShareIcon(platform) + '<span>' + platformLabel(platform) + '</span>';
    return link;
}

function platformLabel(platform) {
    if (platform === 'x') {
        return 'X';
    }
    if (platform === 'linkedin') {
        return 'LinkedIn';
    }
    if (platform === 'facebook') {
        return 'Facebook';
    }
    return platform;
}

function createCopyLinkButton(url) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'article-share-btn article-share-btn-copy';
    button.setAttribute('aria-label', 'Copy article link');
    button.innerHTML = getShareIcon('copy') + '<span>Copy link</span>';

    button.addEventListener('click', function() {
        copyArticleLink(url, button);
    });

    return button;
}

function copyArticleLink(url, button) {
    const onSuccess = function() {
        button.classList.add('is-copied');
        const label = button.querySelector('span');
        const original = label.textContent;
        label.textContent = 'Copied!';
        window.setTimeout(function() {
            button.classList.remove('is-copied');
            label.textContent = original;
        }, 1800);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(onSuccess).catch(function() {
            fallbackCopy(url, onSuccess);
        });
        return;
    }

    fallbackCopy(url, onSuccess);
}

function fallbackCopy(url, onSuccess) {
    const input = document.createElement('input');
    input.value = url;
    input.setAttribute('readonly', '');
    input.style.position = 'absolute';
    input.style.left = '-9999px';
    document.body.appendChild(input);
    input.select();
    try {
        document.execCommand('copy');
        onSuccess();
    } catch (error) {
        console.error('Copy failed:', error);
    }
    document.body.removeChild(input);
}

function getShareIcon(platform) {
    if (platform === 'x') {
        return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>';
    }
    if (platform === 'linkedin') {
        return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 114.126 0 2.063 2.063 0 01-2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>';
    }
    if (platform === 'facebook') {
        return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>';
    }
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>';
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
