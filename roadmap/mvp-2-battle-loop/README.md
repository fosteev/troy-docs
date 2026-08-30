# MVP-2 — Battle Loop

> **Статус: сделано** (Шаг 3). Ниже — спека, по которой бой строился; она остаётся источником требований. Полировка — [polish/](./polish/README.md): P0/P1/P3/P4/P5 закрыты, P2 ждёт ассетов.

Цель: бой должен быть полноценным server-driven gameplay loop, который меняет состояние персонажа.

## Продуктовый результат

Игрок начинает бой с мобом, использует доступные действия, побеждает или проигрывает, получает результат и возвращается в игровой цикл.

## Backend

- [x] `POST /battle/start` должен проверять:
  - активного персонажа;
  - существование моба;
  - дистанцию до моба;
  - доступность моба.
- [x] Battle state должен включать:
  - HP игрока;
  - HP моба;
  - class resource: Rage или Mana;
  - cooldowns;
  - active effects;
  - battle result.
- [x] Реализовать skill usage.
- [x] Реализовать autoattack timing.
- [x] Реализовать победу:
  - XP;
  - level progression;
  - loot roll;
  - запись персонального убийства: НЕ глобальный `alive=FALSE`, а INSERT
    `CharacterKill (characterId, spawnId=active_spawns.id, killedAt)` — моб
    исчезает только для этого персонажа, для других остаётся (read-фильтр уже
    в /map/entities, см. mvp-1-playable-map). Недельный сброс — среда 00:00 UTC.
- [x] Реализовать поражение:
  - результат боя;
  - безопасный возврат на карту.

## Flutter

- [x] Экран боя должен получать состояние с backend.
- [x] UI должен показывать:
  - HP игрока и моба;
  - Rage или Mana;
  - cooldowns;
  - cast/progress state;
  - результат боя.
- [x] Нельзя рассчитывать исход боя на клиенте.
- [x] После победы показать XP, level up и loot.
- [x] После окончания боя вернуть пользователя на карту.

## Связанные документы

- [battle-session.md](../../technical/battle-session.md) — техническая архитектура: real-time tick-движок, BattleSession в Redis, gateway↔game-core, WS/NATS контракты
- [combat.md](../../game-design/combat.md)
- [classes.md](../../game-design/classes.md)
- [stats-and-formulas.md](../../game-design/stats-and-formulas.md)
- [leveling.md](../../game-design/leveling.md)

## Definition of Done

- [x] Бой можно пройти от старта до результата.
- [x] Результат боя сохраняется в backend.
- [x] XP и loot не теряются после restart приложения.
- [x] Клиент не содержит game-authoritative расчетов.

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила (архитектура, тесты, делегирование) — в [roadmap/README.md](../README.md).

> Бой — **real-time, server-authoritative**. Техническая архитектура — [battle-session.md](../../technical/battle-session.md). Промт ниже — высокоуровневый обзор шага.

```
Работаем в /Users/fost/Projects/troy (Flutter + backend).

Прочитай:
- troy-docs/roadmap/mvp-2-battle-loop/README.md, troy-docs/game-design/combat.md, classes.md, stats-and-formulas.md, leveling.md;
- "Architecture rules" в troy-flutter/CLAUDE.md, эталон auth;
- заглушку lib/features/battle/** (37 LOC).

Backend (troy-backend) — battle:
- POST /battle/start проверяет: активного персонажа, существование моба, дистанцию, доступность;
- battle state: HP игрока/моба, class resource (Rage/Mana), cooldowns, active effects, result;
- skill usage, autoattack timing; победа (XP, level progression, loot roll, удаление/деактивация моба); поражение (result, безопасный возврат).

Flutter — фича battle по стандарту (domain/data/presentation):
- domain: BattleState/BattleResult/BattleRound entities, repository-интерфейс (Either);
- data: datasource (POST /battle/start), repo_impl, мапперы;
- presentation: BattleBloc, экран боя из backend-состояния (HP, Rage/Mana, cooldowns, cast/progress, result); НИКАКИХ game-authoritative расчётов на клиенте; после победы — XP/level up/loot; после боя — возврат на карту.

Тесты (по эталону auth): battle repository_impl, BattleBloc, мапперы; backend — integration на battle result (XP/level/loot/деактивация моба).

DoD: бой проходится от старта до результата; результат сохраняется в backend; XP/loot не теряются после рестарта; flutter analyze чисто; flutter test зелёный; backend тесты зелёные. Коммит. Отметить фазу [x] в troy-docs/roadmap/README.md.
```
