// Modal de confirmación de eliminación
function confirmarEliminacion(url, nombre) {
    const modal = document.getElementById('deleteModal');
    if (!modal) {
        console.error('Modal de eliminación no encontrado');
        return;
    }
    
    const form = document.getElementById('deleteForm');
    const message = document.getElementById('deleteMessage');
    
    if (form) form.action = url;
    if (message) message.textContent = `¿Está seguro que desea eliminar ${nombre}?`;
    
    modal.classList.remove('hidden');
}

function cerrarModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Cerrar modal al hacer clic fuera
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                cerrarModal();
            }
        });
    }
});
