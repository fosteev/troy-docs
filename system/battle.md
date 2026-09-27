---
verified: 2026-09-27
backend: 7fe8024
flutter: 8be7b47
paths:
  - troy-backend/apps/game-core/src/app/battle/
  - troy-backend/apps/api-gateway/src/app/ws/game.gateway.ts
  - troy-backend/apps/api-gateway/src/app/battle/battle.controller.ts
  - troy-flutter/lib/features/battle/
---
# Battle — real-time бой против пака

> Игрок дерётся с паком из 1–4 мобов в реальном времени: автоатаки, скиллы с кастом/каналом, сервер решает всё.

## Как работает

- Бой всегда против пака: `BattleService.start` создаёт `packSize` (1..`MONSTER_PACK_MAX=4`) инстансов
  одного `Monster` (`m1…mN`); сам ряд `Monster` не масштабируется — HP/урон пака считает
  `troy-backend/apps/game-core/src/app/battle/engine/formulas.ts:packHpFactor`/`packDamageFactor`. Игрок
  целится в один инстанс (`targetInstanceId`), смена цели — `battle:target`, применяется мгновенно.
- Старт проверяет: персонаж не в defeat-локе, `active_spawns` жив (raw SQL), моб ещё не убит на этой неделе
  (`CharacterKill`), дистанция ≤ `INTERACTION_RADIUS_M` (дефолт 50 м, дев-обход — `IGNORE_BATTLE_DISTANCE`)
  `troy-backend/apps/game-core/src/app/battle/battle.service.ts:start`.
- Тик каждые `BATTLE_TICK_MS=250` мс, safety-net `BATTLE_MAX_DURATION_S=300` форсит поражение
  `troy-backend/apps/game-core/src/app/battle/battle.service.ts:tickOnce`.
- Автоатака — раз в `1/(attackSpeed*ATTACK_SPEED_FACTOR)`; в паке старты автоатак мобов разведены
  `PACK_AUTO_STAGGER_MS=400`, чтобы не бить одним тиком `troy-backend/apps/game-core/src/app/battle/engine/engine.ts:applyAutos`.
- Каст/канал — данные скилла: `castTimeSec>0` кастует, `channelTicks>0` канал (урон на каждый тик, эффект
  один раз на первом); у игрока `castTimeSec`/`cooldownSec` делятся на `1+agility*0.01` `troy-backend/apps/game-core/src/app/battle/battle.service.ts:mapClassSkill`.
- `EffectType.INTERRUPT` рвёт текущий каст/канал и локаутит новые касты (инстанты работают); `STUN` рвёт
  каст так же. Никакого pushback от урона — осознанно `troy-backend/apps/game-core/src/app/battle/engine/types.ts:EffectKind`.
- Формула урона (`resolveHit`): raw → crit (0–100%, `×CRIT_MULTIPLIER=2.0`, у мобов жёстко занулён в коде,
  не через данные монстра) → защита `reduction=defense/(defense+100)` → dodge-ролл (**доля 0–1**, не 0–100
  как крит) → итог `max(1, round(raw*(1-reduction)))` при непромахе — минимум 1 урон гарантирован
  `troy-backend/apps/game-core/src/app/battle/engine/formulas.ts:resolveHit`.
- Ресурс — `CharacterClass.resourceType`: RAGE стартует с 0, растёт от автоатак и получения урона, максимум
  `WARRIOR_MAX_RAGE=100`; MANA стартует полной, регенерирует каждый тик
  `troy-backend/apps/game-core/src/app/battle/battle.service.ts:buildPlayerCombatant`.
- Побег — 3-секундный channel (`FLEE_CHANNEL_MS=3000`), сбрасывается любым уроном или станом игрока; конец
  боя (victory/defeat/escape) → `BattleService.finalize` считает лут/XP/прогрессию одной транзакцией
  (`Character`, `CharacterKill.upsert`, инвентарь, `BattleLog`)
  `troy-backend/apps/game-core/src/app/battle/battle.service.ts:finalize`.
- Loot — `generateLoot` фильтрует `Item.allowedClassCodes`/`itemLevel`/`requiredLevel` **до** взвешивания
  (личный лут), ролл на каждого моба пака `troy-backend/apps/game-core/src/app/battle/battle.service.ts:generateLoot`.
- Reconnect — `rehydrate` поднимает сессию из Redis после рестарта процесса; сессии старого (не-пакового)
  формата намеренно дропаются без слоя совместимости `troy-backend/apps/game-core/src/app/battle/battle.service.ts:rehydrate`.

## Данные

- Prisma: `Character` (battleLockUntil, атрибуты, gold/exp/level), `CharacterClass` (resourceType,
  base-статы, спрайты), `ClassSkill`/`MonsterSkill` (castTimeSec, cooldownSec, resourceCost, damageType,
  effectType, channelTicks), `Monster` (packMin/packMax, attackSpeed, dodge), `DropTable`, `Item`
  (allowedClassCodes, itemLevel, requiredLevel, critChanceBonus, dodgeBonus), `CharacterKill`
  (`@@unique([characterId, spawnId])`; недельный сброс — cron сносит все kills, а чтения ещё и фильтруют
  `killedAt >= currentWeekStart()`, см. [world](world.md)), `BattleLog`.
- Вне Prisma: `active_spawns` (PostGIS) — читается raw SQL в `loadAliveSpawn` (JOIN на `SpawnZone` за
  `arenaBackground`).
- Redis: сессия `battle:{characterId}` (TTL `SESSION_TTL_SECONDS=330`), лок `battle:lock:{characterId}`
  (`LOCK_TTL_SECONDS=10`), и **отдельно** pub/sub-канал `battle:stream:{userId}` — по `userId`, т.к. gateway
  не знает characterId на момент подписки `troy-backend/apps/game-core/src/app/battle/battle-session.store.ts`.

## Контракт

- WS, namespace `/game` (не `/battle`): клиент→сервер `battle:start`, `battle:action`, `battle:target`,
  `battle:flee`, `battle:resume`; сервер→клиент `battle:state` (`BattleStateDto`), `battle:end`
  (`BattleEndDto`) — форвардятся из Redis pub/sub `troy-backend/apps/api-gateway/src/app/ws/game.gateway.ts`.
- NATS (RPC): `battle.start/action/target/flee/resume` — стрим состояния идёт через Redis pub/sub, не NATS.
- REST `POST /battle/start` тоже существует и отдаёт настоящий `BattleStateDto`, но вести бой дальше можно
  только через WS `troy-backend/apps/api-gateway/src/app/battle/battle.controller.ts`.
- DTO — `troy-backend/libs/shared/contracts/src/lib/contracts.ts`: `BattleStateDto`, `BattlePlayerDto`,
  `BattleMonsterDto`, `BattleSkillDto`, `BattleLogEntryDto`, `BattleActionAckDto`, `BattleEndDto`, `BattleLootDto`.

## Где в коде

| Слой | Путь |
|---|---|
| backend — движок и сессия | `troy-backend/apps/game-core/src/app/battle/battle.service.ts`, `battle-session.store.ts`, `battle.controller.ts`, `engine/{engine,formulas,types}.ts` |
| backend — computed stats | `troy-backend/apps/game-core/src/app/character/character.service.ts:computeStats` |
| backend — WS | `troy-backend/apps/api-gateway/src/app/ws/game.gateway.ts` |
| backend — REST | `troy-backend/apps/api-gateway/src/app/battle/battle.controller.ts` |
| flutter | `troy-flutter/lib/features/battle/` |

## Где потрогать

- В приложении: карта → моб в радиусе 50 м → экран боя (скиллы, смена цели тапом по мобу, побег).
- WS: подключиться к namespace `/game` с JWT в `handshake.auth.token`, затем `battle:start
  {monsterId, spawnId}` живого спауна рядом (либо `IGNORE_BATTLE_DISTANCE=true` для дев-обхода дистанции).
- REST: `POST /battle/start` в Swagger UI (`/api`) — схема ответа там устарела, см. «Известные дыры».

## Конфиг и ручки баланса

- `BATTLE_TICK_MS=250`, `BATTLE_MAX_DURATION_S=300`, `SESSION_TTL_SECONDS=330`, `LOCK_TTL_SECONDS=10`.
- `INTERACTION_RADIUS_M` (env, дефолт 50) — макс. дистанция до моба для старта боя.
- `ATTACK_SPEED_FACTOR` (env, дефолт 1), `IGNORE_BATTLE_DISTANCE` (env, дефолт false, дев-обход).
- `DEFEAT_LOCK_SECONDS=60`, `DEFEAT_XP_PENALTY=0.05` — штраф за поражение.
- `WARRIOR_MAX_RAGE=100`, `CRIT_MULTIPLIER=2.0`, `SLOW_FACTOR=0.7`, `FLEE_CHANNEL_MS=3000`, `PACK_AUTO_STAGGER_MS=400`.
- `PACK_DMG_PER_EXTRA` (env, 0.15) / `PACK_HP_PER_EXTRA` (env, 0.25) — рост суммарного урона/HP пака за
  каждого лишнего моба.

## Известные дыры

- Swagger `BattleStartResponseDto` описывает устаревший пораундовый ответ (`rounds`), хотя `POST /battle/start`
  реально отдаёт `BattleStateDto`; `battle:end` в Swagger не описан вовсе (`troy/CLAUDE.md`, Known issues).
- `troy-flutter/CLAUDE.md` описывает бой полностью устаревшей моделью (пораундовый REST) — не источник правды.

## Отличия от геймдизайна

- `game-design/combat.md` даёт формулу автоатаки `base_weapon_dmg + STR*0.8` (Warrior) — код считает
  `physAtk = totalStrength*2 + bonus.physDamage` (`character.service.ts:computeStats`); формула моба
  (`8 + monster.strength*0.8 + monster.intelligence*0.2`) в доке не описана вовсе.
- Дока подаёт crit и dodge как одинаковый ролл `random(0,100)` — в коде dodge хранится как доля 0–1.
- Дока не упоминает минимум 1 урона при непромахе, паки (`monsters[]`, `targetInstanceId`) — описывает
  только бой 1×1.

## Глубже и история

- [technical/battle-session.md](../technical/battle-session.md) — контракт v2, снапшот сессии, edge cases
- [game-design/combat.md](../game-design/combat.md) — замысел формул и скиллов (расхождения — выше)
- [roadmap/group-battle/stage-1-packs.md](../roadmap/group-battle/stage-1-packs.md) — контракт паков (сделан, 1:1 с кодом)
- [roadmap/combat-casting/README.md](../roadmap/combat-casting/README.md) — каналы, INTERRUPT, локаут (сделано, 1:1 с кодом)
