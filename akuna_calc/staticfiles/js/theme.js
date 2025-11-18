// Tema fijo (diseño único claro y moderno)
document.addEventListener('DOMContentLoaded', () => {
    document.documentElement.removeAttribute('data-theme');
    document.body.className = document.body.className.replace(/theme-\w+/g, '');

    const toggleBtn = document.getElementById('theme-toggle');
    const toggleIcon = document.getElementById('theme-toggle-icon');

    if (toggleBtn && toggleIcon) {
        // El botón queda solo como icono decorativo (sin cambiar colores)
        toggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
        });
        toggleIcon.className = 'fas fa-sun';
    }
});
