/**
 * Zen-AI-Pentest - Shared JavaScript Utilities
 * =============================================
 */

// ============================================
// Initialize Lucide Icons
// ============================================
document.addEventListener('DOMContentLoaded', function() {
  // Initialize Lucide icons
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  // Initialize all components
  initNavigation();
  initMobileMenu();
  initScrollReveal();
  initCurrentYear();
});

// ============================================
// Navigation Scroll Effect
// ============================================
function initNavigation() {
  const nav = document.getElementById('main-nav');
  if (!nav) return;
  
  let lastScrollY = window.scrollY;
  let ticking = false;
  
  function updateNav() {
    const scrollY = window.scrollY;
    
    // Add glassmorphism effect when scrolled
    if (scrollY > 50) {
      nav.classList.add('bg-[#0a0a0f]/90', 'backdrop-blur-xl', 'border-b', 'border-white/5');
      nav.classList.remove('bg-transparent');
    } else {
      nav.classList.remove('bg-[#0a0a0f]/90', 'backdrop-blur-xl', 'border-b', 'border-white/5');
      nav.classList.add('bg-transparent');
    }
    
    // Hide/show on scroll direction (optional)
    if (scrollY > lastScrollY && scrollY > 100) {
      // Scrolling down - could hide nav here if desired
      // nav.style.transform = 'translateY(-100%)';
    } else {
      // Scrolling up
      nav.style.transform = 'translateY(0)';
    }
    
    lastScrollY = scrollY;
    ticking = false;
  }
  
  window.addEventListener('scroll', function() {
    if (!ticking) {
      window.requestAnimationFrame(updateNav);
      ticking = true;
    }
  }, { passive: true });
  
  // Initial check
  updateNav();
}

// ============================================
// Mobile Menu Toggle
// ============================================
function initMobileMenu() {
  const menuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  
  if (!menuBtn || !mobileMenu) return;
  
  const menuIcon = menuBtn.querySelector('.menu-icon');
  const closeIcon = menuBtn.querySelector('.close-icon');
  
  menuBtn.addEventListener('click', function() {
    const isExpanded = menuBtn.getAttribute('aria-expanded') === 'true';
    
    // Toggle menu
    mobileMenu.classList.toggle('hidden');
    
    // Toggle icons
    if (menuIcon && closeIcon) {
      menuIcon.classList.toggle('hidden');
      closeIcon.classList.toggle('hidden');
    }
    
    // Update aria attribute
    menuBtn.setAttribute('aria-expanded', !isExpanded);
    
    // Re-initialize icons in case new ones appeared
    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }
  });
  
  // Close menu when clicking on a link
  const menuLinks = mobileMenu.querySelectorAll('a');
  menuLinks.forEach(link => {
    link.addEventListener('click', function() {
      mobileMenu.classList.add('hidden');
      if (menuIcon && closeIcon) {
        menuIcon.classList.remove('hidden');
        closeIcon.classList.add('hidden');
      }
      menuBtn.setAttribute('aria-expanded', 'false');
    });
  });
  
  // Close menu when clicking outside
  document.addEventListener('click', function(e) {
    if (!menuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
      mobileMenu.classList.add('hidden');
      if (menuIcon && closeIcon) {
        menuIcon.classList.remove('hidden');
        closeIcon.classList.add('hidden');
      }
      menuBtn.setAttribute('aria-expanded', 'false');
    }
  });
}

// ============================================
// Scroll Reveal Animation
// ============================================
function initScrollReveal() {
  const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
  
  if (revealElements.length === 0) return;
  
  // Check if IntersectionObserver is supported
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
          revealObserver.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });
    
    revealElements.forEach(el => {
      revealObserver.observe(el);
    });
  } else {
    // Fallback for older browsers
    revealElements.forEach(el => {
      el.classList.add('active');
    });
  }
}

// Manual scroll reveal trigger (for dynamically added content)
function revealElement(selector) {
  const elements = document.querySelectorAll(selector);
  elements.forEach(el => {
    el.classList.add('active');
  });
}

// ============================================
// GSAP ScrollTrigger Integration
// ============================================
function initGSAPAnimations() {
  // Check if GSAP is available
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;
  
  // Register ScrollTrigger
  gsap.registerPlugin(ScrollTrigger);
  
  // Parallax effect for hero elements
  gsap.utils.toArray('.parallax').forEach(element => {
    const speed = element.dataset.speed || 0.5;
    gsap.to(element, {
      yPercent: speed * 100,
      ease: 'none',
      scrollTrigger: {
        trigger: element,
        start: 'top bottom',
        end: 'bottom top',
        scrub: true
      }
    });
  });
  
  // Stagger animation for grids
  gsap.utils.toArray('.stagger-grid').forEach(grid => {
    const items = grid.children;
    gsap.from(items, {
      y: 30,
      opacity: 0,
      duration: 0.6,
      stagger: 0.1,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: grid,
        start: 'top 80%',
        toggleActions: 'play none none none'
      }
    });
  });
}

// Initialize GSAP if available
document.addEventListener('DOMContentLoaded', function() {
  if (typeof gsap !== 'undefined') {
    initGSAPAnimations();
  }
});

// ============================================
// Stats Counter Animation
// ============================================
function animateCounter(element, target, duration = 2000, suffix = '') {
  const start = 0;
  const startTime = performance.now();
  
  function updateCounter(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Easing function (ease-out)
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = Math.floor(start + (target - start) * easeOut);
    
    element.textContent = current.toLocaleString('de-DE') + suffix;
    
    if (progress < 1) {
      requestAnimationFrame(updateCounter);
    } else {
      element.textContent = target.toLocaleString('de-DE') + suffix;
    }
  }
  
  requestAnimationFrame(updateCounter);
}

// Auto-initialize counters when they come into view
function initCounterAnimations() {
  const counters = document.querySelectorAll('[data-counter]');
  
  if (counters.length === 0) return;
  
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
        const target = parseInt(entry.target.dataset.counter, 10);
        const suffix = entry.target.dataset.suffix || '';
        const duration = parseInt(entry.target.dataset.duration, 10) || 2000;
        
        entry.target.classList.add('counted');
        animateCounter(entry.target, target, duration, suffix);
      }
    });
  }, { threshold: 0.5 });
  
  counters.forEach(counter => {
    counterObserver.observe(counter);
  });
}

document.addEventListener('DOMContentLoaded', initCounterAnimations);

// ============================================
// Copy to Clipboard
// ============================================
async function copyToClipboard(text, button = null) {
  try {
    await navigator.clipboard.writeText(text);
    
    // Show feedback on button if provided
    if (button) {
      const originalContent = button.innerHTML;
      button.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i>';
      button.classList.add('text-green-400');
      
      if (typeof lucide !== 'undefined') {
        lucide.createIcons();
      }
      
      setTimeout(() => {
        button.innerHTML = originalContent;
        button.classList.remove('text-green-400');
        if (typeof lucide !== 'undefined') {
          lucide.createIcons();
        }
      }, 2000);
    }
    
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
      document.execCommand('copy');
      if (button) {
        const originalContent = button.innerHTML;
        button.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i>';
        if (typeof lucide !== 'undefined') {
          lucide.createIcons();
        }
        setTimeout(() => {
          button.innerHTML = originalContent;
          if (typeof lucide !== 'undefined') {
            lucide.createIcons();
          }
        }, 2000);
      }
      return true;
    } catch (err) {
      console.error('Fallback copy failed:', err);
      return false;
    } finally {
      document.body.removeChild(textArea);
    }
  }
}

// ============================================
// Current Year in Footer
// ============================================
function initCurrentYear() {
  const yearElements = document.querySelectorAll('#footer-year, .current-year');
  const currentYear = new Date().getFullYear();
  
  yearElements.forEach(el => {
    el.textContent = currentYear;
  });
}

// ============================================
// Smooth Scroll to Anchor
// ============================================
document.addEventListener('click', function(e) {
  const anchor = e.target.closest('a[href^="#"]');
  if (!anchor) return;
  
  const targetId = anchor.getAttribute('href');
  if (targetId === '#') return;
  
  const targetElement = document.querySelector(targetId);
  if (!targetElement) return;
  
  e.preventDefault();
  
  const navHeight = document.getElementById('main-nav')?.offsetHeight || 80;
  const targetPosition = targetElement.getBoundingClientRect().top + window.scrollY - navHeight;
  
  window.scrollTo({
    top: targetPosition,
    behavior: 'smooth'
  });
});

// ============================================
// Tooltip Utility
// ============================================
function showTooltip(element, text) {
  // Remove existing tooltips
  hideTooltip();
  
  const tooltip = document.createElement('div');
  tooltip.className = 'tooltip';
  tooltip.textContent = text;
  tooltip.style.cssText = `
    position: absolute;
    background: #1e1e2e;
    color: #f8fafc;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    font-size: 0.75rem;
    white-space: nowrap;
    z-index: 1000;
    border: 1px solid #2a2a3e;
    pointer-events: none;
  `;
  
  document.body.appendChild(tooltip);
  
  const rect = element.getBoundingClientRect();
  const tooltipRect = tooltip.getBoundingClientRect();
  
  tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltipRect.width / 2)}px`;
  tooltip.style.top = `${rect.top - tooltipRect.height - 8}px`;
  
  // Store reference
  element._tooltip = tooltip;
}

function hideTooltip() {
  const existingTooltip = document.querySelector('.tooltip');
  if (existingTooltip) {
    existingTooltip.remove();
  }
}

// ============================================
// Debounce Utility
// ============================================
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ============================================
// Throttle Utility
// ============================================
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// ============================================
// Typewriter Effect
// ============================================
function typewriter(element, text, speed = 50) {
  let i = 0;
  element.textContent = '';
  
  function type() {
    if (i < text.length) {
      element.textContent += text.charAt(i);
      i++;
      setTimeout(type, speed);
    }
  }
  
  type();
}

// ============================================
// Loading State Utility
// ============================================
function setLoading(element, isLoading) {
  if (isLoading) {
    element.disabled = true;
    element.dataset.originalContent = element.innerHTML;
    element.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i>';
    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }
  } else {
    element.disabled = false;
    if (element.dataset.originalContent) {
      element.innerHTML = element.dataset.originalContent;
      if (typeof lucide !== 'undefined') {
        lucide.createIcons();
      }
    }
  }
}

// ============================================
// Toast Notification
// ============================================
function showToast(message, type = 'info', duration = 3000) {
  // Remove existing toasts
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {
    existingToast.remove();
  }
  
  const toast = document.createElement('div');
  toast.className = 'toast-notification';
  
  const colors = {
    info: 'border-indigo-500 text-indigo-400',
    success: 'border-green-500 text-green-400',
    warning: 'border-amber-500 text-amber-400',
    error: 'border-red-500 text-red-400'
  };
  
  const icons = {
    info: 'info',
    success: 'check-circle',
    warning: 'alert-triangle',
    error: 'x-circle'
  };
  
  toast.style.cssText = `
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    background: #13131f;
    border: 1px solid #2a2a3e;
    border-left: 4px solid;
    padding: 1rem 1.5rem;
    border-radius: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    z-index: 9999;
    animation: slideInRight 0.3s ease;
  `;
  
  toast.classList.add(colors[type].split(' ')[0]);
  
  toast.innerHTML = `
    <i data-lucide="${icons[type]}" class="w-5 h-5 ${colors[type].split(' ')[1]}"></i>
    <span class="text-sm text-gray-200">${message}</span>
  `;
  
  document.body.appendChild(toast);
  
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  setTimeout(() => {
    toast.style.animation = 'slideInRight 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ============================================
// Export utilities for module usage
// ============================================
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initNavigation,
    initMobileMenu,
    initScrollReveal,
    initCounterAnimations,
    animateCounter,
    copyToClipboard,
    debounce,
    throttle,
    typewriter,
    setLoading,
    showToast,
    showTooltip,
    hideTooltip
  };
}
