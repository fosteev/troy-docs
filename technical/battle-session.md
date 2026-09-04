# Battle Session — Архитектура real-time боя (MVP-2, контракт v2)

> **v2 (01.09):** бой идёт против **пака** — 1 игрок × N мобов
> ([group-battle/этап 1](../roadmap/group-battle/stage-1-packs.md)). В сессии и в
> DTO вместо одного `monster` — список `monsters[]` с `instanceId`, у игрока
> появилась цель (`targetInstanceId`), добавлено событие `battle:target`.
> Бой 1v1 — вырожденный случай: пак из одного, отдельной ветки кода нет.

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
  "packSize": 3,
  "status": "active",
  "startedAt": "2026-06-29T12:00:00.000Z",
  "tick": 42,
  "player": {
    "hp": 180, "maxHp": 240,
    "resourceType": "RAGE", "resource": 35, "maxResource": 100,
    "attackIntervalSec": 1.05, "nextAutoAtMs": 1380,
    "effects": [{ "type": "SLOW", "value": 30, "expiresAtMs": 4200 }],
    "cast": null,
    "targetInstanceId": "m2"
  },
  "monsters": [
    { "instanceId": "m1", "hp": 0, "maxHp": 64, "alive": false,
      "targetId": "player",
      "attackIntervalSec": 1.4, "nextAutoAtMs": 900,
      "effects": [], "cast": null, "cooldowns": { "mob_bite": 2100 } },
    { "instanceId": "m2", "hp": 41, "maxHp": 64, "alive": true, "…": "…" },
    { "instanceId": "m3", "hp": 64, "maxHp": 64, "alive": true, "…": "…" }
  ],
  "cooldowns": { "heavy_strike": 2.1, "whirlwind": 0 },
  "flee": null
}
```

> Время внутри сессии — относительное (`...Ms` от `startedAt`), чтобы тик не зависел от системных часов и сериализовался однозначно.

**Про пак:**

- `instanceId` — `m1`…`mN`, стабилен на весь бой; им адресуются цель, урон и лог.
- Кулдауны, `cast`, эффекты и «spent»-флаги скиллов моба — **per-инстанс**:
  каждый волк кастует сам за себя.
- Мёртвый инстанс: `alive: false`, каст и эффекты сброшены, движок его пропускает.
- `packSize` фиксируется на старте из `active_spawns.pack_size` и нужен на финале
  для наград.

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
| **VICTORY** | все мобы пака мертвы | XP → level progression → loot roll → `INSERT CharacterKill` → gold → BattleLog |
| **DEFEAT** | `player.hp ≤ 0` | XP −5% текущего уровня (без понижения) → `battleLockUntil = now+60s` → BattleLog |
| **ESCAPE** | успешный 3-сек channel побега | без XP/лута; моб «возвращается» (сессия просто закрывается, спавн не трогаем) → BattleLog(ESCAPE) |
| **TIMEOUT** | сессия живёт > `BATTLE_MAX_DURATION` | трактуем как DEFEAT (страховка от зависших сессий) |

Финализация — в одной Prisma-транзакции (см. «PostgreSQL по итогу»), затем `DEL battle:{characterId}`, отписка gateway, событие `battle:end` с наградами.

---

## Тик-движок (TickEngine)

`setInterval` на каждый активный бой в game-core. Двигает серверные часы боя и применяет всё, что «созрело» к текущему времени.

**Шаг тика** — фиксированный `BATTLE_TICK_MS` (250 мс ≈ 4 Гц). Темп боя на старте регулируется проще — множителем скорости атаки **`ATTACK_SPEED_FACTOR`** (.env, дефолт 1.0): эффективная AS = `attackSpeed * ATTACK_SPEED_FACTOR`, применяется к обеим сторонам при сборке Combatant'ов. Понижение фактора (<1) делает автоатаки реже → бой медленнее и читаемее. Затрагивает только автоатаки и завязанную на них генерацию ярости; касты/кулдауны не меняет. Полноценный множитель времени (`dtMs * k`, влияет и на касты/кд) — возможное расширение позже. Логика внутри тика:

1. продвинуть `elapsedMs`;
2. протикать эффекты: DOT — урон/сек, истёкшие STUN/SLOW/BUFF/ABSORB снять — у игрока и у **каждого живого** моба;
3. **касты:** каст игрока доводится в его цель (умерла по дороге — в новую, авто-выбранную); каст каждого живого моба — в игрока. **Канал** (`channelTicks > 0`) вместо одного применения даёт тик на каждый созревший момент `startedAt + i × (duration / ticks)`: урон — на каждом, эффект — на первом; закрывается после последнего тика;
4. **автоатаки:** если `nextAutoAtMs` достигнут и сторона не в стане и не кастует — провести автоатаку (формула урона из combat.md: raw → crit → defense → dodge), пересчитать `nextAutoAt += attackInterval`. Игрок бьёт цель, каждый живой моб — игрока; ярость воина растёт с каждого полученного удара, источников просто несколько;
5. **намерение игрока:** если в очереди есть валидный скилл (не на кд, хватает ресурса, не в стане) — списать ресурс, начать каст (или применить инстант) по текущей цели;
6. **скиллы мобов:** тот же алгоритм (приоритет + условие, см. combat.md → «Поведение моба в бою»), но **на каждый инстанс отдельно** — свои кулдауны, свой `spent`, `self_hp_below` читает HP этого инстанса;
7. **побег:** если идёт channel и его не прервали уроном/станом — по достижении 3с завершить как ESCAPE;
8. **смерть моба:** `alive = false`, каст и эффекты сброшены, в лог `kind: 'death'`; если это была цель игрока — авторетаргет на первого живого по порядку `instanceId`;
9. конец боя: все мобы мертвы → VICTORY; игрок мёртв → DEFEAT; timeout → DEFEAT.

Один павший волк ничего не решает — пак дерётся, пока жив хоть один. Чтобы урон
пака не приходил «пачкой», автоатаки инстансов разводятся на старте: `nextAutoAtMs`
i-го сдвигается на `i × PACK_AUTO_STAGGER_MS`.

**Эмиссия состояния:** снапшот в Redis — каждый тик; NATS-событие клиенту — на **значимое изменение** (урон, скилл, эффект, смена ресурса/кд) + keyframe не реже `BATTLE_KEYFRAME_MS` (1 с) для самосинхронизации. Голые «пустые» тики клиенту не шлём.

> **Дискретно-событийная оптимизация (позже):** вместо фикс-шага можно считать «время следующего события» (ближайшая автоатака / конец каста / тик DOT) и спать до него. Для MVP фикс-тик проще и предсказуемее; разнести можно в hardening.

---

## WS события (Flutter ↔ api-gateway, namespace `/battle`)

### Клиент → сервер

```typescript
// начать бой
'battle:start'   { monsterId: string; spawnId: string }
// использовать скилл (намерение; применится на тике) — бьёт по ТЕКУЩЕЙ цели
'battle:action'  { battleId: string; skillCode: string }
// сменить цель в паке (тап по мобу или его плашке)
'battle:target'  { battleId: string; targetInstanceId: string }
// побег: start=начать channel, stop=отпустил кнопку
'battle:flee'    { battleId: string; phase: 'start' | 'stop' }
// переподключение в идущий бой
'battle:resume'  { battleId?: string }
```

Ack на каждое: `{ accepted: boolean; reason?: 'on_cooldown' | 'no_resource' | 'stunned' | 'casting' | 'not_active' | 'invalid_target' | 'locked_out'; state?: BattleStateDto }`.
`locked_out` — игрок под локаутом (эффект `INTERRUPT`): скиллы с `castTimeSec > 0` нельзя начать, инстанты можно.

Смена цели — **отдельное намерение**, а не параметр `action`: тап по мобу и тап по
скиллу — независимые жесты, и клиент не должен угадывать цель в момент каста.
`battle:target` применяется **сразу**, не на тике: он не меняет игровое состояние,
только адресацию. `invalid_target` — инстанса нет в этом бою или он уже мёртв.

### Сервер → клиент

```typescript
'battle:state'  BattleStateDto   // снапшот по ходу боя
'battle:end'    BattleEndDto      // финал + награды
```

### `BattleStateDto` v2 (стримится)

```typescript
{
  battleId: string;
  status: 'active';
  elapsedMs: number;
  arenaBackground: ClassSpriteSheet | null;
  player: {
    hp: number; maxHp: number;
    resourceType: 'RAGE' | 'MANA'; resource: number; maxResource: number;
    effects: { type: EffectType; value: number; remainingSec: number }[];
    cast: { skillCode: string; remainingSec: number; totalSec: number;
            channel?: { ticks: number; done: number } } | null;  // канал: бар опустошается
    /** Кого бьёт игрок. null — все мобы мертвы (мгновение до battle:end). */
    targetInstanceId: string | null;
  };
  /** Пак: 1..N инстансов одного моба. 1v1 — один элемент. */
  monsters: {
    instanceId: string;            // m1…mN, стабилен на весь бой
    alive: boolean;
    targetId: 'player';            // кого бьёт моб; задел под кооп
    name: string; level: number;
    hp: number; maxHp: number;
    effects: { type: EffectType; value: number; remainingSec: number }[];
    cast: { skillCode: string; remainingSec: number; totalSec: number } | null;
    skills: BattleMonsterSkillDto[];  // лента намерений, per-инстанс
  }[];
  skills: { code: string; name: string; cooldownRemainingSec: number; usable: boolean }[];
  flee: { remainingSec: number } | null;
  log: BattleLogEntryDto[];
}
```

### `BattleLogEntryDto`

```typescript
{
  at: number;
  kind: 'hit'|'crit'|'miss'|'skill'|'effect'|'dot'
      | 'cast_start'|'cast_interrupted'|'effect_expired'
      | 'death';                   // умер инстанс пака
  source: 'player'|'monster';      // кто действовал
  target: 'player'|'monster';      // на кого пришлось
  sourceInstanceId?: string;       // инстанс на стороне источника, если это моб
  targetInstanceId?: string;       // инстанс на стороне цели, если это моб
  skillCode?: string; amount?: number;
  crit?: boolean; miss?: boolean;
  damageType?: 'PHYSICAL'|'MAGICAL';
  effectType?: EffectType;
  durationMs?: number;             // на cast_start
  channelTick?: boolean;           // skill-событие тика канала: без замаха
}
```

Инстансы в логе нужны клиенту для адресных цифр урона («−31 над вторым волком»),
строк вида «Волк №2 укусил» и авторетаргета: `kind: 'death'` — сигнал сыграть
death-анимацию; новую цель клиент не выбирает сам, а берёт из
`player.targetInstanceId` следующего снапшота.

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
| `battle.target` | RPC | сменить цель игрока в паке (применяется сразу) |
| `battle.flee` | RPC | старт/стоп channel побега |
| `battle.resume` | RPC | снапшот текущего боя для реконнекта |
| `battle.stream.{characterId}` | event (pub/sub) | тик-снапшоты от движка → gateway |

### Интерфейсы (`libs/shared/contracts`)

```typescript
interface BattleActionRequest { userId: string; battleId: string; skillCode: string; }
interface BattleTargetRequest { userId: string; battleId: string; targetInstanceId: string; }
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

### Прерывание каста станом или киком
Если во время каста прилетает STUN или INTERRUPT — каст срывается, эффект не применяется, ресурс **не возвращается**, на скилл ставится штрафной кд 50% (combat.md). У канала прилетевшие тики остаются. INTERRUPT вдобавок вешает на цель одноимённый эффект-локаут на `effectDurationSec`: пока он висит, цель не начинает касты (движок — `canUseSkill` игрока и выбор скилла моба), в ack — `locked_out`. Инстанты не прерываются.

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
| PACK_DMG_PER_EXTRA | 0.15 (env) | прирост суммарного урона пака за каждого моба сверх первого |
| PACK_HP_PER_EXTRA | 0.25 (env) | то же для суммарного HP; он же множитель награды за пак |
| PACK_AUTO_STAGGER_MS | 400 | сдвиг первой автоатаки i-го инстанса пака |

**Награды за пак** (финализация, в той же транзакции): XP и gold — базовые
`× PACK_REWARD_TOTAL(n)`, где `PACK_REWARD_TOTAL = PACK_TOTAL_HP`; лут — по одному
роллу дроп-таблицы на каждого моба пака, склеенному по `itemId`. `CharacterKill` —
**один** (пак это один спавн), `BattleLog` — одна запись. Статы инстанса
масштабируются при сборке Combatant'ов, строка `Monster` в БД не трогается —
таблица коэффициентов в [stage-1-packs.md](../roadmap/group-battle/stage-1-packs.md#5-баланс-черновые-числа-финальная-настройка--mvp-4).

> **Несоответствие для правки:** сейчас в коде `MAX_BATTLE_DISTANCE_METERS = 100`, а радиус взаимодействия на карте — 50. В MVP-2 свести к единому `INTERACTION_RADIUS_M` (50), чтобы «вижу кнопку боя» = «могу начать бой».

---

## Связанные документы

- [mvp-2-battle-loop/README.md](../roadmap/mvp-2-battle-loop/README.md) — scope и DoD фазы MVP-2
- [combat.md](../game-design/combat.md) — боевые правила, формулы, ресурсы, эффекты
- [stats-and-formulas.md](../game-design/stats-and-formulas.md) — computed stats
- [leveling.md](../game-design/leveling.md) — XP/level progression
- [geolocation.md](./geolocation.md) — серверная позиция, anti-cheat
- [database-schema.md](./database-schema.md) — модели ClassSkill/MonsterSkill/CharacterKill/BattleLog
