#  Decluter

> Sistema de gestão de projetos escolares e planejamento de estudos individuais.

---

##  Sobre o Projetos

O **Decluter** é um SaaS educacional desenvolvido como Trabalho de Conclusão de Curso (TCC). O projeto resolve a falta de ferramentas de organização adequadas para estudantes do ensino médio, unindo em um único lugar a colaboração em equipe e a rotina de estudos individuais:

- **Simplicidade:** Uma alternativa enxuta a ferramentas complexas do mercado corporativo (como Trello e Monday.com).
- **Estudo Guiado:** Geração automática de planos de estudo personalizados com IA.
- **Trabalho em Equipe:** Organização simples de trabalhos escolares sem dependência do WhatsApp.

---

##  Principais Funcionalidades

-  **Gestão de Projetos (Kanban):** Criação de boards, colunas, tarefas e definição de prioridades.
-  **Sincronização em Tempo Real:** Atualizações instantâneas no board e chat por canais via WebSocket.
-  **Cronograma de Estudos com IA:** Planos de estudo individuais gerados automaticamente pela API do Google Gemini com base no tempo disponível e nível do aluno.
-  **Acompanhamento de Progresso:** Visualização das etapas concluídas do cronograma e status do projeto.
-  **Interface Personalizável:** Suporte a modo claro e modo escuro.

---

##  Tecnologias Utilizadas

- **Back-end:** Python, Django (Padrão MVT / Monolito Modular)
- **Comunicação em Tempo Real:** Django Channels & WebSocket (ASGI)
- **Banco de Dados:** PostgreSQL (com suporte a JSONB)
- **Inteligência Artificial:** Google Gemini API
- **Design / UX:** Foco em usabilidade e heurísticas de Nielsen
