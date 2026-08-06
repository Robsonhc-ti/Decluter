// Seleção dos elementos do DOM
const tabEntrar = document.getElementById('tab-entrar');
const tabCriar = document.getElementById('tab-criar');
const groupName = document.getElementById('group-name');
const inputName = document.getElementById('name');
const inputPassword = document.getElementById('password');
const submitBtn = document.getElementById('submit-btn');
const formFooter = document.getElementById('form-footer');

// Função para mudar para a tela de Login
tabEntrar.addEventListener('click', () => {
    tabCriar.classList.remove('active');
    tabEntrar.classList.add('active');
    
    // Oculta campo nome e remove obrigatoriedade
    groupName.classList.add('hidden');
    inputName.removeAttribute('required');
    
    // Atualiza placeholders e textos
    inputPassword.placeholder = "Sua senha";
    submitBtn.textContent = "Entrar";
    
    // Altera o rodapé
    formFooter.innerHTML = '<p class="social-login">Ou continue com Google</p>';
});

// Função para mudar para a tela de Cadastro
tabCriar.addEventListener('click', () => {
    tabEntrar.classList.remove('active');
    tabCriar.classList.add('active');
    
    // Mostra campo nome e adiciona obrigatoriedade
    groupName.classList.remove('hidden');
    inputName.setAttribute('required', '');
    
    // Atualiza placeholders e textos
    inputPassword.placeholder = "Crie uma senha";
    submitBtn.textContent = "Criar conta";
    
    // Altera o rodapé
    formFooter.innerHTML = '<p class="terms-text">Ao continuar, você concorda com os termos de uso</p>';
});
