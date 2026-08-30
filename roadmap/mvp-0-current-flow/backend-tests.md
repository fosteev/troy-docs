# MVP-0 · Backend: тест-фундамент

> **Статус: сделано** (влито в `main`: Jest + `@swc/jest` через Nx, 6 suites/16 тестов на старте; сейчас 18 спек в game-core/api-gateway).

Часть [MVP-0](./README.md). Тесты — часть DoD каждой фазы, правила — раздел «Тестирование» в [roadmap/README.md](../README.md) и «Testing» в корневом `troy/CLAUDE.md`.

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила (архитектура, тесты, делегирование) — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy/troy-backend (NestJS + Nx, Jest).

Прочитай раздел "## Testing" и архитектуру в /Users/fost/Projects/troy/CLAUDE.md.

Задача — тест-фундамент + покрытие существующих сервисов:
1. Настроить Jest для game-core (и api-gateway): jest.config.ts + tsconfig.spec.json под @nx/jest; убедиться, что `npx nx test game-core` запускается.
2. Эталонная unit-спека auth.service (мок PrismaService, JWT, Redis/NATS): хэш пароля, JWT, верификация 6-значного кода и TTL — образец для остальных спек.
3. По образцу покрыть unit-тестами критичную логику (инфраструктуру мокать — Prisma/NATS/Redis):
   - battle.service — формула урона reduction=defense/(defense+100), loot roll, XP/level progression, in-process Player/Inventory;
   - character.service — create/select оставляют ровно одного активного (updateMany isActive=false → нужный true);
   - map.service — distance/сборка DTO (raw SQL мокать на уровне Prisma);
   - spawn-cron.service — добор зоны до threshold 8;
   - inventory.service — equip/unequip + проверка слотов.

DoD: `npx nx test game-core` зелёный; покрыты battle/auth/character/map/spawn/inventory на уровне чистой логики. Коммит в troy-backend. Отметить фазу [x] в troy-docs/roadmap/README.md.
```
