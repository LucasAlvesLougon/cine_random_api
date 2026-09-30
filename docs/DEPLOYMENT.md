# Deploy, disponibilidade gratuita e rollback

## Configuração obrigatória

Em produção, configure `ENVIRONMENT=production`, `SECRET_KEY` aleatória com pelo menos 32 bytes, `GOOGLE_CLIENT_ID`, `FRONTEND_BASE_URL`, `DATABASE_URL` e `TMDB_API_KEY` (ou `TMDB_API_READ_ACCESS_TOKEN`). O login demo permanece desabilitado. Para recuperação de senha, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` e `PASSWORD_RESET_FROM_EMAIL`; sem SMTP a API mantém resposta genérica, mas não consegue entregar o email. No frontend, configure somente `VITE_API_URL` e `VITE_GOOGLE_CLIENT_ID`; a credencial TMDB fica exclusivamente no backend.

O deploy executa `alembic upgrade head` antes de iniciar a API. A migration `0001_baseline` adota automaticamente um banco completo já existente; ela interrompe o deploy se encontrar um schema parcial. Para rollback apenas da identidade Google:

```bash
alembic downgrade 0001_baseline
```

## Eliminar o cold start sem custo

A opção mais simples é criar um monitor HTTP gratuito no UptimeRobot:

1. Crie um monitor `HTTP(s)` com a URL `https://SEU-SERVICO.onrender.com/health/ready`.
2. Selecione intervalo de 5 minutos e ative alerta por email.
3. Confirme no painel do Render que as chamadas chegam a cada 5 minutos.
4. Observe por 24 horas e registre latência, falhas e uso de horas do workspace.

Isso mantém tráfego de entrada mais frequente que a janela de inatividade do Render Free e também faz uma consulta mínima ao PostgreSQL. Não cria SLA: reinícios e indisponibilidades da camada gratuita ainda podem ocorrer. O workflow `keep_alive.yml` é apenas fallback, pois agendamentos do GitHub Actions podem atrasar ou ser desativados por inatividade.

Para medir antes/depois no PowerShell:

```powershell
1..10 | ForEach-Object { (Measure-Command { Invoke-WebRequest https://SEU-SERVICO.onrender.com/health/ready }).TotalMilliseconds }
```

## Migração segura para Supabase Free

Faça a troca em janela controlada:

```bash
pg_dump --format=custom --no-owner --no-acl "$OLD_DATABASE_URL" --file=cine-random.backup
pg_restore --clean --if-exists --no-owner --no-acl --dbname="$NEW_DATABASE_URL" cine-random.backup
DATABASE_URL="$NEW_DATABASE_URL" alembic upgrade head
```

Antes de alterar `DATABASE_URL` no Render, compare as contagens de `users`, `lists`, `movies`, `comments`, `draw_history` e `user_lists_association`, faça smoke test de login/lista/filme e preserve o banco antigo durante a janela de rollback. Se algo falhar, restaure a variável anterior e faça novo deploy.

## Limites de escala

Cache, rate limiter e broadcast WebSocket ainda são locais ao processo. Mantenha uma instância. Antes de escalar horizontalmente, migre esses três estados para Redis compartilhado e pub/sub.

O endpoint `/metrics` expõe contadores e duração acumulada em formato Prometheus. O middleware registra logs JSON com `request_id`, rota, status e duração, sem incluir tokens, senhas ou chaves. O workflow de monitoramento falha quando a API ou as métricas deixam de responder; habilite notificações de falha do GitHub Actions para receber alertas.
