# MVP-5 — Hardening

Цель: убрать технические дыры, которые мешают тестировать MVP на реальных устройствах.

## Backend

- Logout / refresh token revocation.
- WebSocket CORS whitelist.
- Rate limiting для WebSocket events.
- Anti-cheat fix: `checkSpeed()` не должен разрешать teleport при `timeDelta = 0`.
- Логировать ошибки отправки email.
- Проверить health endpoints в Docker.
- Минимальные integration tests:
  - auth;
  - character flow;
  - battle result;
  - inventory equip.

## Flutter

- Обработка истекшего access token.
- Recovery при refresh failure.
- Единый error UI для network/backend ошибок.
- Smoke test auth → character → map.
- Проверка iOS/Android permissions для location.
- Release config для backend base URL.

## DevOps

- Docker compose должен поднимать рабочий backend.
- Seed должен выполняться одной командой.
- Swagger должен быть доступен в dev и отключаем в production.
- Документировать локальный запуск backend + Flutter.

## Definition of Done

- Backend проходит build и базовые tests.
- Flutter проходит analyze.
- Docker compose поднимает рабочий dev backend.
- MVP можно поставить на устройство и пройти core loop без ручных SQL/API вмешательств.
