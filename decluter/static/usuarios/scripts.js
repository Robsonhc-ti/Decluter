const tabEntrar = document.getElementById('tab-entrar');
const tabCriar = document.getElementById('tab-criar');
const groupName = document.getElementById('group-name');
const groupConfirmarSenha = document.getElementById('group-confirmar-senha');
const submitBtn = document.getElementById('submit-btn');

function mostrarEntrar() {
    tabEntrar.classList.add('active');
    tabCriar.classList.remove('active');
    groupName.classList.add('hidden');
    groupConfirmarSenha.classList.add('hidden');
    submitBtn.textContent = 'Entrar';
    submitBtn.name = 'entrar';
}

function mostrarCriarConta() {
    tabCriar.classList.add('active');
    tabEntrar.classList.remove('active');
    groupName.classList.remove('hidden');
    groupConfirmarSenha.classList.remove('hidden');
    submitBtn.textContent = 'Criar conta';
    submitBtn.name = 'criar_conta';
}

tabEntrar.addEventListener('click', mostrarEntrar);
tabCriar.addEventListener('click', mostrarCriarConta);