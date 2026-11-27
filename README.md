#  Decluter

> Sistema de gestão de projetos escolares e planejamento de estudos individuais.

---

##  Sobre o Projetos

O **Decluter** é um SaaS educacional desenvolvido como Trabalho de Conclusão de Curso (TCC). O projeto resolve a falta de ferramentas de organização adequadas para estudantes do ensino médio, unindo em um único lugar a colaboração em equipe e a rotina de estudos individuais:

- **Simplicidade:** Uma alternativa enxuta a ferramentas complexas do mercado corporativo (como Trello e Monday.com).
- **Estudo Guiado:** Geração automática de planos de estudo personalizados com IA.
- **Trabalho em Equipe:** Organização simples de trabalhos escolares em equipe.

---

##  Principais Funcionalidades

-  **Gestão de Projetos (Kanban):** Criação de boards, colunas, tarefas e definição de prioridades.
-  **Cronograma de Estudos com IA:** Planos de estudo individuais gerados automaticamente pela API do Google Gemini com base no tempo disponível e nível do aluno.
-  **Acompanhamento de Progresso:** Visualização das etapas concluídas do cronograma e status do projeto.
-  **Interface Personalizável:** Suporte a modo claro e modo escuro.

---

##  Tecnologias Utilizadas

- **Back-end:** Python, Django (Padrão MVT / Monolito Modular)
- **Banco de Dados:** PostgreSQL (com suporte a JSONB)
- **Inteligência Artificial:** Google Gemini API
- **Design / UX:** Foco em usabilidade e heurísticas de Nielsen

## Como publicar na Render

1. Envie a branch do projeto para o repositório conectado à Render.
2. No painel, selecione **New → Blueprint**, escolha o repositório e aplique o `render.yaml` da raiz. O serviço usa `decluter/` como diretório raiz; o `build.sh` instala `../requirements.txt`, coleta os arquivos estáticos e aplica as migrations.
3. Configure `GEMINI_API_KEY`, `GEMINI_MODEL` e `DEMO_PASSWORD` nas variáveis do serviço. Quando `DEMO_PASSWORD` estiver definida, o build cria ou atualiza os usuários e dados de demonstração de forma idempotente.
4. Troque os exemplos de `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` pelo domínio atribuído à aplicação. `RENDER_EXTERNAL_HOSTNAME` é incluído automaticamente pelos settings.

Opcionalmente, configure `DJANGO_SUPERUSER_EMAIL` e `DJANGO_SUPERUSER_PASSWORD` nas variáveis do serviço para criar um superusuário durante o build, caso ainda não exista. O username será derivado da parte local do email. Não publique arquivos `.env` nem senhas.

O Blueprint fixa Python 3.13.14 e cria um serviço web e PostgreSQL no plano gratuito. O PostgreSQL gratuito expira após 30 dias; exporte os dados antes desse prazo se precisar preservá-los.
