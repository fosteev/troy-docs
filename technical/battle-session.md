# Battle Session — Архитектура real-time боя (MVP-2)

## Обзор

Бой — **real-time, server-authoritative**. Сервер держит живую боевую сессию и сам тикает её во времени; клиент шлёт только намерения (использовать скилл, начать побег) и рисует состояние, которое прилетает с сервера. Никаких game-authoritative расчётов на клиенте — это пункт DoD ([MVP-2](../roadmap/mvp-2-battle-loop/README.md)).

Боевые правила (ресурсы, формулы, эффекты, тайм– автоатаки и касты) — в [combat.md](../game-design/combat.md). Этот документ описывает **инфраструктуру**: где живёт состояние боя, кто его тикает, как api-gateway и game-core общаются в реальном времени.

> **Ключевое архитектурное решение:** вся игровая логика и тик-движок живут в **game-core** (как и весь остальной геймплей, см. design decision #1 в корневом `CLAUDE.md`). **api-gateway** — тонкий WS-транспорт: принимает действия игрока, форвардит снапшоты состояния. Логика боя в gateway не дублируется.

---

## Что уже готово, а что добавляем

Схема Prisma уже подготовлена под этот дизайн — отдельная миграция не нужна для моделей, только сиды и движок.

| Артефакт | Статус | Действие в Шаге 3 |
|---|---|---|
| `ClassSkill` (slot, castTimeSec, cooldownSec, resourceType, resourceCost, damage, scaling, effect) | ✅ в схеме | засидить скиллы Warrior/Mage стартовых уровней |
| `MonsterSkill` (castTimeSec, cooldownSec, damage, effect, sortOrder) | ✅ в схеме | засидить 1–2 скилла мобам |
| `CharacterKill` (characterId, spawnId, killedAt, `@@unique`) | ✅ в схеме | **начать использовать** вместо `alive=FALSE` |
| Энумы `ResourceType/DamageType/ScalingStat/EffectType/BattleResult(+ESCAPE)` | ✅ в схеме | — |
| `Character.battleLockUntil` (лок поражения) | ✅ в схеме | переиспользовать |
| `BattleLog` (история, lootJson, durationSec) | ✅ в схеме | писать по факту реальной длительности |
| Текущий `battle.service.ts` — one-shot симуляция 50 раундов + глобальный `alive=FALSE` | ⚠️ переписываем | заменить на tick-движок + `CharacterKill` |
| Tick-движок, BattleSession в Redis, WS-стрим | ❌ нет | **строим** |

> **Долг из MVP-1:** текущая победа делает `UPDATE active_spawns SET alive=FALSE` — глобально для всех игроков. Это ломает персональную видимость мобов, заложенную в Шаге 2. В MVP-2 победа должна делать `INSERT CharacterKill`, а `alive` не трогать.

---

## Где живёт состояние

### Redis — `battle:{characterId}` (TTL = BATTLE_MAX_DURATION + grace)

Единственный источник истины о текущем бое. Ключ по **персонажу** (один активный бой на персонажа). Хранит полный снапшот сессии — переживает реконнект клиента и (при наличии) рестарт процесса не теряет прогресс.

```json
{
  "battleId": "uuid",
  "characterId": "uuid",
  "monsterId": "uuid",
  "spawnId": "uuid",
  "status": "active",
  "startedAt": "2026-06-29T12:00:00.000Z",
  "tick": 42,
  "player": {
    "hp": 180, "maxHp": 240,
    "resourceType": "RAGE", "resource": 35, "maxResource": 100,
    "attackIntervalSec": 1.05, "nextAutoAtMs": 1380,
    "effects": [{ "type": "SLOW", "value": 30, "expiresAtMs": 4200 }],
    "cast": null
  },
  "monster": {
    "hp": 60, "maxHp": 320,
    "attackIntervalSec": 1.4, "nextAutoAtMs": 900,
    "effects": [{ "type": "DOT", "value": 8, "expiresAtMs": 3000 }],
    "cast": { "skillCode": "mob_smash", "endsAtMs": 1600 }
  },
  "cooldowns": { "heavy_strike": 2.1, "whirlwind": 0 },
  "flee": null
}
```

> Время внутри сессии — относительное (`...Ms` от `startedAt`), чтобы тик не зависел от системных часов и сериализовался однозначно.

### Redis — `battle:lock:{characterId}` (опционально, SET NX)

Гард от двойного старта боя в гонке (две вкладки / ретрай запроса). Берётся на время создания сессии.

### PostgreSQL — по итогу боя (в транзакции)

Тик-движок работает по Redis, в Postgres пишем **только финал** (один раз, не каждый тик):

- `Character` — level/exp/атрибуты (прогрессия), gold, `battleLockUntil` (при поражении);
- `CharacterKill` — `INSERT (characterId, spawnId)` при победе (вместо `alive=FALSE`);
- `CharacterInventory` — лут (upsert, как сейчас);
- `BattleLog` — запись истории (result, expDelta, goldDelta, lootJson, реальный durationSec).

---

## Архитектура: gateway ↔ game-core

```
┌─────────────┐   WS /battle    ┌──────────────────┐   NATS RPC    ┌──────────────────┐
│   Flutter   │ ◄─────────────► │   api-gateway    │ ◄───────────► │    game-core     │
│ BattleBloc  │  battle:start   │  BattleGateway   │  battle.start │  BattleService   │
│             │  battle:action  │  (тонкий транспорт)│ battle.action │  + TickEngine    │
│             │  battle:flee    │                  │               │   (setInterval)  │
│             │ ◄─ battle:state │                  │ ◄─ NATS event │  state → Redis   │
│             │ ◄─ battle:end   │                  │ battle.stream.*│  публикует тики  │
└─────────────┘                 └──────────────────┘               └──────────────────┘
```

**Поток управления (клиент → сервер):** запрос-ответ через NATS RPC.
- `battle:start` / `battle:action` / `battle:flee` приходят на BattleGateway по WS → транслируются в NATS RPC (`battle.start` / `battle.action` / `battle.flee`) → game-core валидирует и **ставит намерение в сессию**, отвечает ack'ом (`{ accepted, reason? }` + актуальный снапшот). Эффект применяется движком на ближайшем тике, не синхронно в ответе.

**Поток состояния (сервер → клиент):** события через NATS pub/sub.
- TickEngine в game-core на каждом значимом тике пишет снапшот в Redis и **публикует** NATS-событие в субъект `battle.stream.{characterId}`.
- BattleGateway подписан на субъекты тех боёв, чьи сокеты он держит; получив событие — эмитит клиенту `battle:state` (или `battle:end`).
- Подписка заводится при `battle:start`/`battle:resume`, снимается при `battle:end` или disconnect.

> **Транспорт стрима — Redis Pub/Sub** по каналу `battle:{characterId}`, не NATS. Причина: NestJS NATS не умеет динамические per-battle подписки в рантайме (`@EventPattern` статичен), а канал создаётся на лету при старте боя; Redis уже общий для обоих процессов и ioredis даёт `subscribe/publish` из коробки. NATS остаётся на RPC (start/action/flee/resume). Субъект `battle.stream.{characterId}` на схеме — концептуальный «поток состояния»; в реализации это Redis-канал. At-most-once допустимо: следующий keyframe-тик исправит пропуск.

---

## Жизненный цикл боя

```
START ──► ACTIVE ──(hp≤0 / flee / timeout)──► ENDED ──► (persist + cleanup)
```

### 1. Старт (`battle.start`)

Валидация (как сейчас + позиция с сервера):
1. активный персонаж существует;
2. персонаж не `incapacitated` (`battleLockUntil > now`);
3. **нет уже идущего боя** (`battle:{characterId}` отсутствует) — иначе вернуть текущий снапшот (idempotent resume);
4. моб существует, спавн жив (`active_spawns.alive=TRUE`);
5. **этот персонаж ещё не убивал этот спавн на этой неделе** (нет `CharacterKill` с `killedAt >= weekStart()`);
6. дистанция ≤ `INTERACTION_RADIUS_M` (50) — берём **серверную позицию** персонажа, не из payload клиента (anti-spoof, см. [geolocation.md](./geolocation.md)).

Инициализация по [combat.md](../game-design/combat.md): `hp=maxHp`; Mage — полная мана; Warrior — `rage=0`. Грузятся `ClassSkill` персонажа (по `class`, `unlockLevel <= level`) и `MonsterSkill` моба. Сессия пишется в Redis, запускается TickEngine, возвращается первый снапшот.

### 2. Активная фаза (TickEngine)

См. раздел «Тик-движок».

### 3. Конец боя

| Исход | Триггер | Эффект |
|---|---|---|
| **VICTORY** | `monster.hp ≤ 0` | XP → level progression → loot roll → `INSERT CharacterKill` → gold → BattleLog |
| **DEFEAT** | `player.hp ≤ 0` | XP −5% текущего уровня (без понижения) → `battleLockUntil = now+60s` → BattleLog |
| **ESCAPE** | успешный 3-сек channel побега | без XP/лута; моб «возвращается» (сессия просто закрывается, спавн не трогаем) → BattleLog(ESCAPE) |
| **TIMEOUT** | сессия живёт > `BATTLE_MAX_DURATION` | трактуем как DEFEAT (страховка от зависших сессий) |

Финализация — в одной Prisma-транзакции (см. «PostgreSQL по итогу»), затем `DEL battle:{characterId}`, отписка gateway, событие `battle:end` с наградами.

---

## Тик-движок (TickEngine)

`setInterval` на каждый активный бой в game-core. Двигает серверные часы боя и применяет всё, что «созрело» к текущему времени.

**Шаг тика** — фиксированный `BATTLE_TICK_MS` (250 мс ≈ 4 Гц). Темп боя на старте регулируется проще — множителем скорости атаки **`ATTACK_SPEED_FACTOR`** (.env, дефолт 1.0): эффективная AS = `attackSpeed * ATTACK_SPEED_FACTOR`, применяется к обеим сторонам при сборке Combatant'ов. Понижение фактора (<1) делает автоатаки реже → бой медленнее и читаемее. Затрагивает только автоатаки и завязанную на них генерацию ярости; касты/кулдауны не меняет. Полноценный множитель времени (`dtMs * k`, влияет и на касты/кд) — возможное расширение позже. Логика внутри тика:

1. продвинуть `elapsedMs`;
2. протикать эффекты: DOT — урон/сек, истёкшие STUN/SLOW/BUFF/ABSORB снять;
3. **касты:** если у игрока/моба идёт каст и `endsAtMs` достигнут — применить урон/эффект, снять каст, поставить кулдаун;
4. **автоатаки:** если `nextAutoAtMs` достигнут и сторона не в стане и не кастует — провести автоатаку (формула урона из combat.md: raw → crit → defense → dodge), пересчитать `nextAutoAt += attackInterval`; автоатака воина генерит Rage;
5. **намерение игрока:** если в очереди есть валидный скилл (не на кд, хватает ресурса, не в стане) — списать ресурс, начать каст (или применить инстант);
6. **скиллы моба:** по запрограммированному алгоритму (приоритет + условие, см. combat.md → «Поведение моба в бою»): первый скилл, который не на кулдауне и чьё условие выполнено; иначе автоатака;
7. **побег:** если идёт channel и его не прервали уроном/станом — по достижении 3с завершить как ESCAPE;
8. проверить конец боя (`hp ≤ 0` любой стороны) → финализация.

**Эмиссия состояния:** снапшот в Redis — каждый тик; NATS-событие клиенту — на **значимое изменение** (урон, скилл, эффект, смена ресурса/кд) + keyframe не реже `BATTLE_KEYFRAME_MS` (1 с) для самосинхронизации. Голые «пустые» тики клиенту не шлём.

> **Дискретно-событийная оптимизация (позже):** вместо фикс-шага можно считать «время следующего события» (ближайшая автоатака / конец каста / тик DOT) и спать до него. Для MVP фикс-тик проще и предсказуемее; разнести можно в hardening.

---

## WS события (Flutter ↔ api-gateway, namespace `/battle`)

### Клиент → сервер

```typescript
// начать бой
'battle:start'   { monsterId: string; spawnId: string }
// использовать скилл (намерение; применится на тике)
'battle:action'  { battleId: string; skillCode: string }
// побег: start=начать channel, stop=отпустил кнопку
'battle:flee'    { battleId: string; phase: 'start' | 'stop' }
// переподключение в идущий бой
'battle:resume'  { battleId?: string }
```

Ack на каждое: `{ accepted: boolean; reason?: 'on_cooldown' | 'no_resource' | 'stunned' | 'not_active' | 'too_far' | 'incapacitated'; state?: BattleStateDto }`.

### Сервер → клиент

```typescript
'battle:state'  BattleStateDto   // снапшот по ходу боя
'battle:end'    BattleEndDto      // финал + награды
```

### `BattleStateDto` (стримится)

```typescript
{
  battleId: string;
  status: 'active';
  elapsedMs: number;
  player: {
    hp: number; maxHp: number;
    resourceType: 'RAGE' | 'MANA'; resource: number; maxResource: number;
    effects: { type: EffectType; value: number; remainingSec: number }[];
    cast: { skillCode: string; remainingSec: number; totalSec: number } | null;
  };
  monster: {
    name: string; level: number;
    hp: number; maxHp: number;
    effects: { type: EffectType; value: number; remainingSec: number }[];
    cast: { skillCode: string; remainingSec: number; totalSec: number } | null;
  };
  skills: { code: string; name: string; cooldownRemainingSec: number; usable: boolean }[];
  flee: { remainingSec: number } | null;
  log: { at: number; kind: 'hit'|'crit'|'miss'|'skill'|'effect'|'dot'; source: 'player'|'monster'; skillCode?: string; amount?: number }[];
}
```

### `BattleEndDto`

```typescript
{
  battleId: string;
  result: 'VICTORY' | 'DEFEAT' | 'ESCAPE';
  expDelta: number;
  goldDelta: number;
  leveledUpBy: number;
  // лут резолвится на сервере — клиент не ходит за именем предмета по UUID
  loot: {
    itemId: string; quantity: number;
    name: string; rarity: ItemRarity; iconUrl: string | null;
  }[];
  battleLockUntil: string | null;   // ISO, при поражении
  character: {
    level: number; exp: number; gold: number;
    expToNextLevel: number;                        // вся шкала уровня, не остаток
    attributeGains: {                              // null, если апа не было
      strength: number; intelligence: number; stamina: number;
      agility: number; spirit: number;
    } | null;
  };
  log: BattleLogEntryDto[];         // полный лог боя, не окно
}
```

---

## NATS контракты

### Новые паттерны (добавить в `NATS_PATTERNS`)

| Паттерн | Тип | Описание |
|---|---|---|
| `battle.start` | RPC | уже есть; меняется ответ (snapshot + battleId) |
| `battle.action` | RPC | поставить намерение использовать скилл |
| `battle.flee` | RPC | старт/стоп channel побега |
| `battle.resume` | RPC | снапшот текущего боя для реконнекта |
| `battle.stream.{characterId}` | event (pub/sub) | тик-снапшоты от движка → gateway |

### Интерфейсы (`libs/shared/contracts`)

```typescript
interface BattleActionRequest { userId: string; battleId: string; skillCode: string; }
interface BattleFleeRequest   { userId: string; battleId: string; phase: 'start' | 'stop'; }
interface BattleResumeRequest { userId: string; battleId?: string; }
// событие в субъект battle.stream.{characterId}
interface BattleStreamEvent   { battleId: string; characterId: string; payload: BattleStateDto | BattleEndDto; final: boolean; }
```

> `BattleStartRequest` теряет `characterLat/characterLng` — позицию берём серверную (см. anti-cheat).

---

## Поток данных (атака скиллом)

```
Flutter: тап по скиллу
  │  WS: battle:action { battleId, skillCode }
  ▼
api-gateway / BattleGateway
  │  NATS RPC: battle.action { userId, battleId, skillCode }
  ▼
game-core / BattleService
  ├─ найти сессию в Redis battle:{characterId}
  ├─ валидация: бой активен, скилл не на кд, хватает ресурса, не в стане
  ├─ поставить намерение в сессию (player.pendingSkill = skillCode)
  └─ ack { accepted: true }  ──► gateway ──► клиенту
  │
  ▼  (на ближайшем тике TickEngine)
  ├─ списать ресурс, начать каст / применить инстант
  ├─ применить урон (crit → defense → dodge), эффект
  ├─ записать снапшот в Redis
  └─ NATS publish battle.stream.{characterId} { BattleStateDto }
       │
       ▼
   gateway (подписан) ──► WS battle:state ──► BattleBloc рисует
```

---

## Anti-cheat

Раз сервер authoritative и сам тикает — клиент не может ускорить бой или ударить вне правил.

- **Позиция для старта** — серверная (`Character.lat/lng`, после гео-рефактора `User.lat/lng`), не из payload. Исключает спуфинг координат ради боя с далёким мобом (см. [geolocation.md](./geolocation.md) → Anti-cheat).
- **Тайминги — на сервере.** Кулдауны, каст-тайм, интервалы автоатак считает движок по своим часам. Действие клиента, пришедшее «слишком рано» (скилл на кд / нет ресурса / в стане), отклоняется ack'ом `accepted:false`, состояние не меняется.
- **Один бой на персонажа.** Старт при существующем `battle:{characterId}` не плодит вторую сессию (resume). Гард гонки — `battle:lock:{characterId}` (SET NX).
- **Награды считает только сервер** на финале, в транзакции. Клиент получает результат, не формирует его.
- **Лок поражения** (`battleLockUntil`, 60с) проверяется на старте — нельзя сразу перезайти в бой.

---

## Edge cases

### Реконнект во время боя
Состояние в Redis по `characterId` переживает разрыв WS. Клиент при переподключении шлёт `battle:resume` → gateway переподписывается на `battle.stream.{characterId}`, отдаёт текущий снапшот. **Движок тикает всё это время** (бой не на паузе — сервер authoritative): моб продолжает бить, мог и убить персонажа, пока тот был offline.

### Клиент не вернулся
Бой идёт server-side до исхода или до `BATTLE_MAX_DURATION` (timeout → DEFEAT). Сессия не висит вечно — TTL Redis + cap длительности.

### Двойной старт (две вкладки / ретрай)
`battle:lock:{characterId}` (SET NX) + проверка существующей сессии. Второй старт получает снапшот первого, новую сессию не создаёт.

### Прерывание каста станом
Если во время каста прилетает STUN — каст срывается, эффект не применяется, ресурс **не возвращается**, на скилл ставится штрафной кд 50% (combat.md). Инстанты не прерываются.

### Побег прерван
Любой полученный урон или STUN во время 3-сек channel сбрасывает `flee` → побег не засчитан, бой продолжается.

### Моб уже убит этим персонажем на неделе
Старт отклоняется (`CharacterKill` с `killedAt >= weekStart()` существует) — согласовано с read-фильтром `/map/entities`.

### Рестарт game-core с активными боями (single-instance MVP)
Снапшоты в Redis живы, но in-memory таймеры теряются. Для MVP допустимо (бои короткие; «осиротевшие» сессии добьёт TTL/timeout). Восстановление таймеров из Redis и/или вынос боёв в отдельный воркер — кандидат на hardening; масштабирование game-core в несколько инстансов требует sticky-владения боем.

---

## Константы

| Константа | Значение | Описание |
|---|---|---|
| INTERACTION_RADIUS_M | 50 (env) | макс. дистанция для старта боя (= `canInteract` на карте) |
| BATTLE_TICK_MS | 250 | шаг серверного тика (≈4 Гц) |
| ATTACK_SPEED_FACTOR | 1.0 (env) | множитель скорости атаки (hits/sec) обеих сторон; <1 замедляет бой |
| BATTLE_KEYFRAME_MS | 1000 | максимальный интервал между keyframe-снапшотами клиенту |
| BATTLE_MAX_DURATION_S | 300 | потолок длительности боя (timeout → DEFEAT) |
| DEFEAT_LOCK_SECONDS | 60 | `incapacitated` после поражения |
| FLEE_CHANNEL_S | 3 | удержание кнопки побега |
| DEFEAT_XP_PENALTY | 0.05 | штраф −5% XP текущего уровня |

> **Несоответствие для правки:** сейчас в коде `MAX_BATTLE_DISTANCE_METERS = 100`, а радиус взаимодействия на карте — 50. В MVP-2 свести к единому `INTERACTION_RADIUS_M` (50), чтобы «вижу кнопку боя» = «могу начать бой».

---

## Связанные документы

- [mvp-2-battle-loop/README.md](../roadmap/mvp-2-battle-loop/README.md) — scope и DoD фазы MVP-2
- [combat.md](../game-design/combat.md) — боевые правила, формулы, ресурсы, эффекты
- [stats-and-formulas.md](../game-design/stats-and-formulas.md) — computed stats
- [leveling.md](../game-design/leveling.md) — XP/level progression
- [geolocation.md](./geolocation.md) — серверная позиция, anti-cheat
- [database-schema.md](./database-schema.md) — модели ClassSkill/MonsterSkill/CharacterKill/BattleLog
