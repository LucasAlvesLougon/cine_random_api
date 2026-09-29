# ADR 0001 — Disponibilidade gratuita em uma única instância

## Decisão

Manter a API em uma única instância Render Free, usar `/health/ready` como alvo de um monitor UptimeRobot a cada 5 minutos e migrar a persistência para PostgreSQL Supabase Free.

## Motivos

O intervalo do monitor fica abaixo da janela de inatividade do Render e a consulta `SELECT 1` verifica API e banco. A solução não adiciona custo recorrente e atende ao uso pessoal/baixo tráfego.

## Consequências

Não há SLA e reinícios continuam possíveis. Cache, rate limit e broadcast WebSocket são locais; escala horizontal exige Redis compartilhado e pub/sub. O GitHub Actions permanece somente como fallback, com a URL real fornecida no secret `RENDER_API_URL`.
