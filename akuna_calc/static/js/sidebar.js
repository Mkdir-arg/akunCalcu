document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebarClose = document.getElementById('sidebar-close');
    const mobileOverlay = document.getElementById('mobile-overlay');
    
    let isMobile = window.innerWidth < 1024;
    
    // Detectar cambios de tamaño de pantalla
    window.addEventListener('resize', function() {
        const wasMobile = isMobile;
        isMobile = window.innerWidth < 1024;
        
        if (wasMobile && !isMobile) {
            closeMobileSidebar();
        }
    });
    
    // Abrir sidebar en móvil
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Mobile menu clicked');
            openMobileSidebar();
        });
    }
    
    // Cerrar sidebar en móvil
    if (sidebarClose) {
        sidebarClose.addEventListener('click', function(e) {
            e.preventDefault();
            closeMobileSidebar();
        });
    }
    
    // Cerrar sidebar al hacer click en overlay
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', function() {
            closeMobileSidebar();
        });
    }
    
    // Cerrar sidebar al hacer click en un enlace (móvil)
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            if (isMobile) {
                setTimeout(() => closeMobileSidebar(), 150);
            }
        });
    });
    
    function openMobileSidebar() {
        console.log('Opening sidebar');
        if (sidebar) {
            sidebar.style.transform = 'translateX(0)';
            sidebar.classList.remove('-translate-x-full');
            sidebar.classList.add('translate-x-0');
        }
        if (mobileOverlay) {
            mobileOverlay.classList.remove('hidden');
            mobileOverlay.style.display = 'block';
        }
        document.body.style.overflow = 'hidden';
    }
    
    function closeMobileSidebar() {
        console.log('Closing sidebar');
        if (sidebar) {
            sidebar.style.transform = 'translateX(-100%)';
            sidebar.classList.add('-translate-x-full');
            sidebar.classList.remove('translate-x-0');
        }
        if (mobileOverlay) {
            mobileOverlay.classList.add('hidden');
            mobileOverlay.style.display = 'none';
        }
        document.body.style.overflow = '';
    }
    
    // Debug: mostrar estado inicial
    console.log('Sidebar initialized:', {
        sidebar: !!sidebar,
        mobileMenuBtn: !!mobileMenuBtn,
        sidebarClose: !!sidebarClose,
        mobileOverlay: !!mobileOverlay,
        isMobile: isMobile
    });
    
    // Animaciones de entrada
    const animatedElements = document.querySelectorAll('.animate-fade-in, .card-hover');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease-out';
        observer.observe(el);
    });
});