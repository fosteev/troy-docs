# MVP-5 — Hardening

> **Статус: не начат.** По ходу уже закрыто: health endpoints в api-gateway. Открыто: logout / revocation refresh-токена, WS CORS whitelist, rate limiting WS-событий, `checkSpeed()` при `timeDelta = 0`, логирование ошибок `emitEmail`, перф-baseline.

Цель: убрать технические дыры, которые мешают тестировать MVP на реальных устройствах.

## Backend

- [ ] Logout / refresh token revocation.
- [ ] WebSocket CORS whitelist.
- [ ] Rate limiting для WebSocket events.
- [ ] Anti-cheat fix: `checkSpeed()` не должен разрешать teleport при `timeDelta = 0`. *(`libs/shared/utils/src/lib/geo.ts` всё ещё возвращает 0)*
- [ ] Логировать ошибки отправки email.
- [x] Проверить health endpoints в Docker. *(эндпоинты есть — `api-gateway/src/app/health`, раздел «Healthcheck» в `troy-backend/README.md`)*
- [ ] Минимальные integration tests:
  - auth;
  - character flow;
  - battle result;
  - inventory equip.

## Flutter

- [x] Обработка истекшего access token. *(`core/api/auth_interceptor.dart` — refresh по 401)*
- [ ] Recovery при refresh failure.
- [ ] Единый error UI для network/backend ошибок.
- [ ] Smoke test auth → character → map.
- [ ] Проверка iOS/Android permissions для location.
- [ ] Release config для backend base URL.

## DevOps

- [x] Docker compose должен поднимать рабочий backend.
- [x] Seed должен выполняться одной командой.
- [x] Swagger должен быть доступен в dev и отключаем в production.
- [x] Документировать локальный запуск backend + Flutter. *(`troy-backend/README.md` «Local setup», `troy-flutter/README.md` «Run app»)*

## Definition of Done

- [ ] Backend проходит build и базовые tests.
- [ ] Flutter проходит analyze.
- [ ] Docker compose поднимает рабочий dev backend.
- [ ] MVP можно поставить на устройство и пройти core loop без ручных SQL/API вмешательств.

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила (архитектура, тесты, делегирование) — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy (backend + Flutter + DevOps).

Прочитай troy-docs/roadmap/mvp-5-hardening/README.md.

Backend (troy-backend):
- logout / revocation refresh-токена; WebSocket CORS whitelist; rate limiting WS-событий;
- anti-cheat: checkSpeed() не должен разрешать teleport при timeDelta = 0;
- логировать ошибки отправки email; проверить health endpoints в Docker;
- integration/e2e на сквозной флоу: auth → character → battle result → inventory equip (unit-тесты сервисов уже есть с прошлых шагов — здесь закрыть пробелы).

Flutter (troy-flutter):
- unit-тесты блоков/репозиториев уже есть с прошлых шагов — здесь закрыть пробелы покрытия и добавить widget-smoke ключевых экранов; опционально вернуть bloc_test (совместимой с Flutter 3.44 версией) как сахар для уже написанных тестов;
- обработка истёкшего access token; recovery при refresh failure; единый error UI;
- smoke test auth → character → map; проверка iOS/Android location permissions; release config для backend base URL.

DevOps: docker compose поднимает рабочий dev backend; seed одной командой; Swagger в dev и отключаем в prod; задокументировать локальный запуск backend + Flutter.

Перформанс/нагрузочные (фаза-гейт, не per-step): инструмент k6 или artillery; сценарии по горячим путям — GET /map/entities, POST /battle/start, WS character:move (N клиентов с движением), латентность NATS-RPC валидации. Снять baseline (p50/p95/RPS). По результатам решить про кэш активного персонажа в Redis (инвалидация на select) — не оптимизировать без данных.

DoD: backend проходит build и тесты (unit+integration); flutter analyze чисто и flutter test зелёный; docker compose поднимает рабочий backend; снят перф-baseline горячих путей (p50/p95/RPS); MVP можно поставить на устройство и пройти core loop без ручных SQL/API вмешательств. Коммит. Отметить фазу [x] в troy-docs/roadmap/README.md.
```
