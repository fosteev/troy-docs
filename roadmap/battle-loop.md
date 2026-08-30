# MVP-2 — Battle Loop

> **Статус: сделано** (Шаг 3). Ниже — спека, по которой бой строился; она
> остаётся источником требований. Полировка живёт отдельно, в
> [battle-polish.md](./battle-polish.md) — там же чек-лист остатка.

Цель: бой должен быть полноценным server-driven gameplay loop, который меняет состояние персонажа.

## Продуктовый результат

Игрок начинает бой с мобом, использует доступные действия, побеждает или проигрывает, получает результат и возвращается в игровой цикл.

## Backend

- `POST /battle/start` должен проверять:
  - активного персонажа;
  - существование моба;
  - дистанцию до моба;
  - доступность моба.
- Battle state должен включать:
  - HP игрока;
  - HP моба;
  - class resource: Rage или Mana;
  - cooldowns;
  - active effects;
  - battle result.
- Реализовать skill usage.
- Реализовать autoattack timing.
- Реализовать победу:
  - XP;
  - level progression;
  - loot roll;
  - запись персонального убийства: НЕ глобальный `alive=FALSE`, а INSERT
    `CharacterKill (characterId, spawnId=active_spawns.id, killedAt)` — моб
    исчезает только для этого персонажа, для других остаётся (read-фильтр уже
    в /map/entities, см. playable-map.md). Недельный сброс — среда 00:00 UTC.
- Реализовать поражение:
  - результат боя;
  - безопасный возврат на карту.

## Flutter

- Экран боя должен получать состояние с backend.
- UI должен показывать:
  - HP игрока и моба;
  - Rage или Mana;
  - cooldowns;
  - cast/progress state;
  - результат боя.
- Нельзя рассчитывать исход боя на клиенте.
- После победы показать XP, level up и loot.
- После окончания боя вернуть пользователя на карту.

## Связанные документы

- [battle-session.md](../technical/battle-session.md) — техническая архитектура: real-time tick-движок, BattleSession в Redis, gateway↔game-core, WS/NATS контракты
- [combat.md](../game-design/combat.md)
- [classes.md](../game-design/classes.md)
- [stats-and-formulas.md](../game-design/stats-and-formulas.md)
- [leveling.md](../game-design/leveling.md)

## Definition of Done

- Бой можно пройти от старта до результата.
- Результат боя сохраняется в backend.
- XP и loot не теряются после restart приложения.
- Клиент не содержит game-authoritative расчетов.
