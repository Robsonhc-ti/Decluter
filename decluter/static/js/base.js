function aplicarTema(tema) {
    document.documentElement.setAttribute('data-theme', tema);
    localStorage.setItem('decluter-tema', tema);
}

function alternarTema() {
    const atual = document.documentElement.getAttribute('data-theme');
    aplicarTema(atual === 'dark' ? 'light' : 'dark');
}

// Ao carregar a página, aplica o tema salvo (ou 'light' se for a primeira vez)
const temaSalvo = localStorage.getItem('decluter-tema') || 'light';
aplicarTema(temaSalvo);