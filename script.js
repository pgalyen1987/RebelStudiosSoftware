// Site configuration — fill in IDs after creating accounts
const GA_MEASUREMENT_ID = '';
const BLOG_AD_CLIENT = 'ca-pub-4668633509273232';
const BLOG_SIDEBAR_AD_SLOT = '8015849679';
const BLOG_BOTTOM_AD_SLOT = '7377555423';

// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    initAnalytics();
    initBlogAds();

    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            
            // Animate hamburger
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

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Add scroll animation to portfolio items
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe portfolio items
    const portfolioItems = document.querySelectorAll('.portfolio-item');
    portfolioItems.forEach(item => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(item);
    });

    // Observe feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });

    // Auto-rotate carousel
    const carousels = document.querySelectorAll('.screenshot-carousel');
    carousels.forEach(carousel => {
        let currentIndex = 0;
        const slides = carousel.querySelectorAll('.screenshot-slide');
        const dots = carousel.querySelectorAll('.dot');
        
        if (slides.length > 1) {
            setInterval(() => {
                currentIndex = (currentIndex + 1) % slides.length;
                showSlide(carousel.id, currentIndex);
            }, 4000);
        }
    });
});

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

    document.querySelectorAll('.adsbygoogle').forEach(function() {
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

// Carousel functions
function changeSlide(carouselId, direction) {
    const carousel = document.getElementById(carouselId);
    const slides = carousel.querySelectorAll('.screenshot-slide');
    const dots = carousel.querySelectorAll('.dot');
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
