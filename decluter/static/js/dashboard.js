// Abre o pop-up correspondente ao card clicado
document.querySelectorAll('.dash-card').forEach(card => {
    card.addEventListener('click', () => {
        document.getElementById(card.dataset.popup).classList.add('aberto');
    });
});

// Fecha pelo X
document.querySelectorAll('.dash-popup-fechar').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.target.closest('.dash-popup-overlay').classList.remove('aberto');
    });
});

// Fecha clicando fora da caixa
document.querySelectorAll('.dash-popup-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('aberto');
    });
});