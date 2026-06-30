# Шаг 3 (MVP-2 battle) — playbook делегирования

Детальная разбивка реализации real-time боя на **мелкие самодостаточные промты** под делегирование слабым моделям (codex / kimi). Архитектура — [battle-session.md](../technical/battle-session.md), правила боя — [combat.md](../game-design/combat.md). Высокоуровневый промт шага — [execution-plan.md](./execution-plan.md) (Шаг 3); этот файл — его детализация.

> Зачем дробить: real-time движок целиком — нетривиальная логика, слабая модель захлебнётся. Поэтому крутая часть вынесена в **чистое детерминированное ядро** (pure-функции, легко тестируются и ревьюятся), а stateful-обвязка (Redis, тик-таймер, WS) — тонкими отдельными фазами.

---

## Принципы (читать перед каждой делегацией)

1. **Одна фаза = одна сессия делегата.** Не давать весь Шаг 3 разом. После фазы — прогнать DoD, проверить, потом следующая.
2. **Чистое ядро отдельно от I/O.** Вся боевая математика — pure-функции без Redis/NATS/таймеров/`Date.now()`. Слабые модели на чистой логике с тестами справляются кратно лучше, чем на оркестрации.
3. **RNG только инъекцией.** Все функции с рандомом принимают `rng: () => number` (0..1) параметром. **Запрещён `Math.random()` внутри ядра** — иначе тесты недетерминированы. В тестах передаём фейковый rng.
4. **Точность вместо свободы.** Промт даёт точные пути файлов, сигнатуры, формулы, константы и таблицу тест-кейсов с числами. Не «реализуй бой», а «реализуй `f(a,b)->c` по формуле X, тест: f(10,50)=…».
5. **Явный список «НЕ делай»** в каждом промте (см. ниже общий стоп-лист).
6. **Переиспользовать существующее.** Прогрессию (`applyProgression`/`levelGrowth`), лут (`generateLoot`), маппинг атрибутов уже написаны в текущем `battle.service.ts` — указывать, что копировать, а не переписывать.
7. **DoD = команды.** Каждая фаза заканчивается конкретной командой (`npx nx test game-core` и т.п.) и «зелёным».

### Общий стоп-лист (вставлять в каждый промт)

- НЕ использовать `Math.random()` / `Date.now()` / `new Date()` внутри ядра — только через инъекцию.
- НЕ менять формулы баланса (урон/XP/рост статов) — берём как заданы; баланс — это Шаг 5.
- НЕ делать `UPDATE active_spawns SET alive=FALSE` на победе — вместо этого `INSERT CharacterKill` (см. фазу B3).
- НЕ считать исход боя/награды на клиенте (Flutter) — только рисуем то, что прислал сервер.
- НЕ трогать чужие фичи/файлы вне списка в промте.

---

## Карта фаз (порядок и кто делает)

| Фаза | Что | Риск | Кто |
|---|---|---|---|
| **B0** | Контракты: NATS-паттерны + DTO/интерфейсы | низкий | делегат |
| **B1** | Чистое боевое ядро `battle-engine/` + unit-тесты | средний | делегат (Opus ревьюит формулы) |
| **B2** | `BattleSessionStore` (Redis adapter) | низкий | делегат |
| **B3** | `BattleService` + TickEngine + финализация (транзакция, CharacterKill, loot, BattleLog) | **высокий** | Opus пишет / тяжёлое ревью |
| **B4** | WS-хендлеры в `GameGateway` + Redis Pub/Sub стрим | **высокий** | Opus пишет / тяжёлое ревью |
| **B5** | Seed скиллов (ClassSkill/MonsterSkill) | низкий | делегат |
| **F1** | Flutter domain (entities + repo-интерфейс) | низкий | делегат (зеркалит auth) |
| **F2** | Flutter data (WS datasource + repo_impl + мапперы) | средний | делегат (зеркалит auth) |
| **F3** | Flutter presentation (BattleBloc + экран) | средний | делегат + ревью |

Зависимости: B0 → B1 → B2 → B3 → B4 → (B5 параллельно B1+). Flutter F1→F2→F3 после B0 (нужны DTO-формы), реально тестируется после B4.

> **Транспорт стрима — Redis Pub/Sub, не NATS.** NestJS NATS не умеет динамические per-battle подписки в рантайме, а канал `battle:{characterId}` создаётся на лету. Redis уже общий для обоих процессов и ioredis даёт `subscribe/publish` из коробки. NATS остаётся на RPC (start/action/flee/resume). Это уточняет «альтернативу», помеченную в battle-session.md.

---

## Базовые факты для всех backend-промтов

Вставлять как контекст (это уже в коде, проверено):

- `character.service.ts → getMe(userId)` возвращает активного персонажа: сырые поля (`id, class, level, exp, strength…spirit, battleLockUntil`) **плюс** `computedStats`.
- `computedStats` содержит: `maxHp, maxMana, physAtk, magicAtk, armor, magicResist, attackSpeed, critChance, dodge (=0), ragePerAuto, manaRegen, totalAttributes{strength,intelligence,stamina,agility,spirit}`.
- `Monster` (Prisma): `id, level, hp, strength, intelligence, armor, magicResist, attackSpeed, dodge, expReward, goldReward` + связи `dropTables`, `monsterSkills`.
- `ClassSkill` (Prisma): `class, slot, unlockLevel, code, name, castTimeSec, cooldownSec, resourceType(RAGE|MANA), resourceCost, damageType(PHYSICAL|MAGICAL|null), baseDamage, scalingStat(STR|INT|null), scalingRatio, effectType(NONE|STUN|SLOW|DOT|BUFF|ABSORB|HEAL), effectValue, effectDurationSec, isActive`.
- `MonsterSkill` (Prisma): как ClassSkill, но без ресурса/слота: `code, castTimeSec, cooldownSec, damageType, baseDamage, scalingStat, scalingRatio, effectType, effectValue, effectDurationSec, sortOrder`.
- `CharacterKill` (Prisma): `characterId, spawnId, killedAt`, `@@unique([characterId, spawnId])` — **уже в схеме, миграции не надо**.
- В текущем `battle.service.ts` уже реализованы и переиспользуются: `applyProgression`, `levelGrowth`, `generateLoot`, `getCharacterOffenseProfile`, `randomInt`, константа `DEFEAT_LOCK_SECONDS=60`. `weekStart()` — хелпер из map-логики (фильтр недели).
- `RedisService.getClient()` → ioredis-клиент (`get/set/del/setnx/expire/duplicate/subscribe/publish`).

---

## Фаза B0 — Контракты

```
Работаем в /Users/fost/Projects/troy/troy-backend (NestJS + Nx, TypeScript).

Файл: libs/shared/contracts/src/lib/contracts.ts

Задача — только типы и константы, без логики.

1. В объект NATS_PATTERNS добавь рядом с BATTLE_START:
   BATTLE_ACTION: 'battle.action',
   BATTLE_FLEE: 'battle.flee',
   BATTLE_RESUME: 'battle.resume',

2. Замени интерфейс BattleStartRequest — убери characterLat/characterLng
   (позицию сервер берёт сам). Оставь:
   interface BattleStartRequest { userId: string; monsterId: string; spawnId: string; }

3. Добавь интерфейсы:
   interface BattleActionRequest { userId: string; battleId: string; skillCode: string; }
   interface BattleFleeRequest   { userId: string; battleId: string; phase: 'start' | 'stop'; }
   interface BattleResumeRequest { userId: string; battleId?: string; }

4. Добавь DTO-типы состояния (стримятся клиенту). Скопируй ТОЧНО:

   type EffectKind = 'NONE'|'STUN'|'SLOW'|'DOT'|'BUFF'|'ABSORB'|'HEAL';

   interface BattleEffectDto { type: EffectKind; value: number; remainingSec: number; }
   interface BattleCastDto   { skillCode: string; remainingSec: number; totalSec: number; }
   interface BattleSkillDto  { code: string; name: string; cooldownRemainingSec: number; usable: boolean; }
   interface BattleLogEntryDto {
     at: number; kind: 'hit'|'crit'|'miss'|'skill'|'effect'|'dot';
     source: 'player'|'monster'; skillCode?: string; amount?: number;
   }
   interface BattleCombatantDto {
     hp: number; maxHp: number;
     effects: BattleEffectDto[]; cast: BattleCastDto | null;
   }
   interface BattlePlayerDto extends BattleCombatantDto {
     resourceType: 'RAGE'|'MANA'; resource: number; maxResource: number;
   }
   interface BattleMonsterDto extends BattleCombatantDto { name: string; level: number; }
   interface BattleStateDto {
     battleId: string; status: 'active'; elapsedMs: number;
     player: BattlePlayerDto; monster: BattleMonsterDto;
     skills: BattleSkillDto[]; flee: { remainingSec: number } | null;
     log: BattleLogEntryDto[];
   }
   interface BattleLootDto { itemId: string; quantity: number; }
   interface BattleEndDto {
     battleId: string; result: 'VICTORY'|'DEFEAT'|'ESCAPE';
     expDelta: number; goldDelta: number; leveledUpBy: number;
     loot: BattleLootDto[]; battleLockUntil: string | null;
     character: { level: number; exp: number; gold: number };
   }

5. Экспортируй всё новое (тот же стиль export interface, что в файле).

НЕ делай: ничего кроме правки этого файла. Не трогай battle.service/controller.

DoD: контракты-либа компилируется, `npx nx build api-gateway` проходит. **`npx nx build game-core` будет КРАСНЫМ** на `battle.service.ts:106-107` (`payload.characterLat/Lng` — удалённые поля): это ожидаемо, B0 связан с B3, который переводит сервис на серверную позицию и закрывает ошибку. Не «чинить» здесь — либо сразу делать B3, либо временно не удалять эти поля. Никакой логики не добавлено.
```

---

## Фаза B1 — Чистое боевое ядро (сердце, но pure)

```
Работаем в /Users/fost/Projects/troy/troy-backend.

Цель — ЧИСТЫЙ детерминированный движок боя. Ни одного обращения к БД, Redis, NATS,
таймерам, Date, Math.random. Только функции (вход → выход). Это позволяет покрыть
его тестами на 100%.

Создай каталог apps/game-core/src/app/battle/engine/ с файлами:
- types.ts        — типы движка
- formulas.ts     — чистые формулы урона/ресурсов
- engine.ts       — функция tick() + initBattleState()
- engine.spec.ts, formulas.spec.ts — тесты

### types.ts

type CharClass = 'WARRIOR' | 'MAGE';
type DamageType = 'PHYSICAL' | 'MAGICAL';
type ScalingStat = 'STR' | 'INT';
type EffectKind = 'NONE'|'STUN'|'SLOW'|'DOT'|'BUFF'|'ABSORB'|'HEAL';

interface SkillDef {
  code: string; name: string;
  castTimeSec: number; cooldownSec: number;
  resourceCost: number;               // 0 для мобов
  damageType: DamageType | null; baseDamage: number;
  scalingStat: ScalingStat | null; scalingRatio: number;
  effectType: EffectKind; effectValue: number; effectDurationSec: number;
}
interface ActiveEffect { type: EffectKind; value: number; expiresAtMs: number; }
interface CastState { skillCode: string; endsAtMs: number; }
interface Combatant {
  class: CharClass | 'MONSTER';
  hp: number; maxHp: number;
  armor: number; magicResist: number; dodge: number;
  critChance: number; critMultiplier: number;     // игрок 2.0; моб 0
  attackIntervalSec: number; nextAutoAtMs: number;
  autoRawDamage: number;                            // готовый raw авто-урона
  attrs: { STR: number; INT: number };              // для скейла скиллов
  // только игрок:
  resourceType?: 'RAGE'|'MANA'; resource?: number; maxResource?: number;
  ragePerAuto?: number; manaRegenPerSec?: number;
  rageOnHitFactor?: number;          // = 0.15*(1+SPI*0.02); 0 для не-воина. Считает B3, движок только умножает
  effects: ActiveEffect[];
  cast: CastState | null;
  skills: SkillDef[];
  cooldowns: Record<string, number>;                // code -> готов в ...Ms (абсолют)
}
type BattleResult = 'VICTORY'|'DEFEAT'|'ESCAPE';
interface BattleState {
  elapsedMs: number;
  player: Combatant; monster: Combatant;
  pendingSkill: string | null;                      // намерение игрока
  flee: { startedAtMs: number } | null;
  status: 'active'|'ended'; result: BattleResult | null;
}
interface BattleEvent {
  at: number; kind: 'hit'|'crit'|'miss'|'skill'|'effect'|'dot';
  source: 'player'|'monster'; skillCode?: string; amount?: number;
}
interface TickInput {
  dtMs: number;                                     // шаг времени
  rng: () => number;                                // ИНЪЕКЦИЯ рандома (0..1)
  intent?: { skillCode?: string; flee?: 'start'|'stop' };
}
interface TickResult { state: BattleState; events: BattleEvent[]; }

### formulas.ts — ТОЧНЫЕ формулы из combat.md (все pure, rng параметром)

// reduction по защите
defenseReduction(defense: number): number
  = max(0,defense) / (max(0,defense) + 100)

// raw урона скилла
skillRawDamage(skill, attrs): number
  = skill.baseDamage + (skill.scalingStat ? attrs[skill.scalingStat] * skill.scalingRatio : 0)

// полный расчёт одного удара → итоговый урон + был ли крит/мисс
resolveHit(args: {
  raw: number; damageType: 'PHYSICAL'|'MAGICAL';
  critChance: number; critMultiplier: number;
  targetArmor: number; targetMagicResist: number; targetDodge: number;
  rng: () => number;
}): { damage: number; crit: boolean; miss: boolean }
  ШАГИ строго по combat.md:
  1. crit: if rng()*100 < critChance → raw *= critMultiplier, crit=true
  2. defense = damageType==='PHYSICAL' ? targetArmor : targetMagicResist
     reduction = defenseReduction(defense)
  3. dodge: if rng()*100 < targetDodge → damage=0, miss=true
     else damage = round( raw * (1 - reduction) )   // минимум 1, если raw>0 и не мисс
  (порядок rng-вызовов: сначала крит-ролл, потом dodge-ролл — фиксируй, тесты на это завязаны)

КОНСТАНТА: CRIT_MULTIPLIER = 2.0 (экспортируй).

### engine.ts

initBattleState(player: Combatant, monster: Combatant): BattleState
  — status='active', result=null, elapsedMs=0, pendingSkill=null, flee=null.
  (Combatant'ы собирает вызывающий код в B3 из computedStats/Monster — движок их не строит.)

tick(state, input: TickInput): TickResult — ЧИСТАЯ (возвращает НОВЫЙ state, не мутирует вход).
  Порядок внутри одного тика (now = state.elapsedMs + dtMs):
  1. elapsedMs = now.
  2. Эффекты: DOT — value это урон/СЕК, наносить `value * dtMs/1000` (НЕ flat per tick —
     иначе урон привязан к частоте тика), источник по эффекту, событие kind:'dot';
     урон от DOT по воину тоже генерит ярость (gainRageFromDamage); снять эффекты с expiresAtMs <= now.
  2a. Bounds: как только у любой стороны hp<=0 — бой решён; дальнейшие НАСТУПАТЕЛЬНЫЕ действия
      в этом же тике не выполняются (мёртвый не бьёт в ответ, скилл мёртвого игрока не «докидывает»
      победу). Хелпер isDecided(state); гейтить им касты/автоатаки/скиллы игрока и моба.
  3. Касты: для игрока и моба — если cast и cast.endsAtMs <= now → применить
     урон/эффект скилла (resolveHit + наложить effect), снять cast, поставить cooldown
     (готов в now + cooldownSec*1000), событие kind:'skill'.
  4. Автоатаки: для стороны, если now >= nextAutoAtMs И не застанена (нет STUN в effects)
     И cast===null → resolveHit по autoRawDamage; nextAutoAtMs += attackIntervalSec*1000.
     Воин-игрок: resource += ragePerAuto (clamp 0..maxResource). DamageType автоатаки:
     WARRIOR/MONSTER→PHYSICAL, MAGE→MAGICAL.
  5. Получение урона воином (игрок WARRIOR) от любого источника final>0:
     resource += final * 0.15 * (1 + SPI*0.02) — НО SPI здесь не нужен, ragePerAuto уже
     инкапсулирует SPI; для урона используй переданный коэффициент: добавь в Combatant
     поле rageOnHitFactor (число = 0.15*(1+SPI*0.02)), считает B3. Применяй resource += final*rageOnHitFactor, clamp.
  6. Регекн маны (игрок MAGE): resource += manaRegenPerSec * dtMs/1000, clamp 0..maxResource.
  7. Намерение игрока (intent.skillCode или state.pendingSkill): если скилл валиден
     (есть в skills, cooldowns[code]<=now, resource>=resourceCost, игрок не застанен, cast===null):
       resource -= resourceCost; pendingSkill=null;
       если castTimeSec>0 → cast={code, endsAtMs: now+castTimeSec*1000} (применение в п.3 следующих тиков)
       иначе (инстант) → применить сразу (resolveHit+effect), cooldown=now+cd, событие 'skill'.
     если невалиден — намерение игнор (НЕ кидать исключение в ядре).
  8. Скиллы моба: по первому monster.skills, у которого cooldowns[code]<=now → начать так же.
  9. Побег: intent.flee==='start' → flee={startedAtMs:now}; ==='stop' → flee=null.
     если flee и (now - startedAtMs) >= FLEE_CHANNEL_MS → result='ESCAPE', status='ended'.
     ВАЖНО: если в этом тике игрок получил урон (final>0) или застанен — flee=null (срыв).
  10. Прерывание каста станом: если на стороне в этом тике наложился STUN во время её cast → cast=null,
      cooldown на сорванный скилл = now + cooldownSec*0.5*1000 (ресурс НЕ возвращаем).
  11. Конец: monster.hp<=0 → result='VICTORY'; player.hp<=0 → result='DEFEAT'; status='ended'.

КОНСТАНТЫ (экспорт): FLEE_CHANNEL_MS = 3000.

### Тесты (engine.spec.ts, formulas.spec.ts) — детерминированные, rng = () => 0 (или массив).

Обязательные кейсы с ТОЧНЫМИ числами:
- defenseReduction(100) === 0.5; defenseReduction(0) === 0; defenseReduction(300) === 0.75.
- resolveHit: armor=100, raw=40, crit=0%, dodge=0% → damage=20 (40*0.5). 
- resolveHit с rng=()=>0 и critChance=100 → crit=true, damage=40 (raw 40→80→*0.5=40).
- resolveHit с dodge=100, rng=()=>0 → miss=true, damage=0.
- skillRawDamage({baseDamage:30, scalingStat:'STR', scalingRatio:1.2},{STR:50,INT:0}) === 90.
- tick: автоатака срабатывает ровно когда elapsedMs пересекает nextAutoAtMs.
- tick: STUN блокирует автоатаку цели на duration.
- tick: воин копит rage от своей автоатаки (resource растёт на ragePerAuto).
- tick: маг регенит ману со временем (manaRegenPerSec).
- tick: скилл на кулдауне / нехватка ресурса → намерение игнорируется, ресурс не списан.
- tick: HP моба <=0 → result VICTORY, status ended.
- tick: HP игрока <=0 → result DEFEAT.
- tick: flee 3 сек без урона → ESCAPE; урон во время flee → flee сброшен.

НЕ делай: НИКАКИХ импортов prisma/redis/nats/nestjs в engine/. Никакого Math.random/Date.
Только чистые функции. Тесты не должны мокать — данные строятся инлайн.

DoD: `npx nx test game-core` зелёный; новые спеки engine/formulas проходят; ядро
не импортирует инфраструктуру (проверь импорты). 100% перечисленных кейсов покрыто.
```

> **Заметка по балансу:** `autoRawDamage`, рост статов, XP-формулы здесь НЕ трогаем — берём из существующих computedStats и `applyProgression`. Тонкая настройка чисел — Шаг 5.

---

## Фаза B2 — BattleSessionStore (Redis)

```
Работаем в /Users/fost/Projects/troy/troy-backend.

Создай apps/game-core/src/app/battle/battle-session.store.ts — тонкий адаптер
над Redis для хранения BattleState по персонажу. Без боевой логики.

@Injectable() class BattleSessionStore {
  constructor(private readonly redis: RedisService) {}   // RedisService из ../common/redis.service
  private key(characterId) { return `battle:${characterId}`; }
  private lockKey(characterId) { return `battle:lock:${characterId}`; }

  async load(characterId): Promise<StoredSession | null>   // get + JSON.parse, null если нет
  async save(characterId, session: StoredSession, ttlSec): Promise<void>  // set ... EX ttlSec, JSON.stringify
  async clear(characterId): Promise<void>                  // del key
  async acquireLock(characterId, ttlSec): Promise<boolean>  // SET lockKey 1 NX EX ttlSec → true если поставили
  async releaseLock(characterId): Promise<void>             // del lockKey
}

StoredSession (тип в этом же файле): { battleId, characterId, monsterId, spawnId,
  monsterName, monsterLevel, state: BattleState, rageOnHitFactor, startedAtIso }.
BattleState импортируй из engine/types.

Образец работы с Redis — apps/game-core/src/app/map/map.service.ts (redis.getClient().get/set ... 'EX').

Тест battle-session.store.spec.ts: замокай RedisService.getClient() заглушкой ioredis
(простой объект с jest.fn для get/set/del/'set' с NX). Проверь сериализацию round-trip,
acquireLock true/false, clear.

НЕ делай: никакой боевой логики, никаких тиков. Только CRUD + lock.

DoD: `npx nx test game-core` зелёный; стора покрыта.
```

---

## Фаза B3 — BattleService + TickEngine + финализация (ВЫСОКИЙ РИСК → Opus)

> Эту фазу пишет Opus или делегат под плотным ревью: тут транзакция, гонки, переиспользование прогрессии/лута и стрим. Промт ниже — каркас; логику тика брать из B1, не переизобретать.

```
Работаем в /Users/fost/Projects/troy/troy-backend. Перепиши battle.service.ts
с one-shot симуляции на управление real-time сессией. Движок (tick) — из engine/, НЕ дублировать.

Зависимости (constructor): PrismaService, CharacterService, BattleSessionStore,
RedisService (для publish стрима), и текущие переиспользуемые приватные методы
(applyProgression, levelGrowth, generateLoot) — ПЕРЕНЕСТИ как есть.

Методы:

async start(req: BattleStartRequest): валидация по battle-session.md → 
  1. character = characterService.getMe(req.userId); проверить battleLockUntil > now → BadRequest('incapacitated').
  2. acquireLock(characterId, 10); если false → загрузить и вернуть текущий snapshot (resume).
  3. monster = prisma.monster.findUnique(+monsterSkills); спавн жив (raw как сейчас).
  4. CharacterKill за неделю: prisma.characterKill.findFirst({characterId, spawnId, killedAt >= weekStart()}) → если есть, BadRequest('already killed this week').
  5. дистанция: серверная позиция (character.lat/lng) vs спавн, <= INTERACTION_RADIUS_M (env, дефолт 50). (Сейчас 100 — заменить на 50.)
  6. собрать engine Combatant'ы из computedStats (игрок) и Monster (моб):
     player.autoRawDamage = class==='WARRIOR' ? physAtk : magicAtk; critMultiplier=2.0;
     ragePerAuto/manaRegenPerSec/maxResource/resourceType из class; resource init: WARRIOR 0 / MAGE maxMana;
     rageOnHitFactor = class==='WARRIOR' ? 0.15*(1+SPI*0.02) : 0;
     monster.autoRawDamage = 8 + str*0.8 + int*0.2 (как в текущем коде); critMultiplier=0; dodge=monster.dodge.
     SkillDef из ClassSkill (по class, unlockLevel<=level, isActive) и monsterSkills.
  7. initBattleState → save(ttl=BATTLE_MAX_DURATION_S+30) → releaseLock → стартовать TickEngine → вернуть snapshot DTO.

async action(req: BattleActionRequest): load; если нет/ended → {accepted:false, reason:'not_active'};
  валидировать скилл по правилам combat.md (на кд? хватает ресурса? в стане?) — если нельзя,
  вернуть {accepted:false, reason}; иначе session.state.pendingSkill = skillCode; save; {accepted:true}.
  (Применение — на ближайшем тике, не здесь.)

async flee(req): аналогично, выставить intent flee start/stop в сессию (через поле, читается тиком).
async resume(req): load → snapshot DTO или {accepted:false}.

TickEngine — это setInterval(BATTLE_TICK_MS) на бой (Map<characterId, NodeJS.Timeout> в сервисе):
  каждый тик: load; собрать intent из session (pendingSkill/flee-flag); 
  result = tick(state, {dtMs: BATTLE_TICK_MS, rng: Math.random, intent});  // <-- ЕДИНСТВЕННОЕ место Math.random
  записать state; если события/keyframe → publishState(); 
  если result.state.status==='ended' → finalize() и остановить интервал.

publishState(dto): redis.getClient().publish(`battle:stream:${session.userId}`, JSON.stringify({type:'state'|'end', payload: dto})).
  ВАЖНО: канал по userId, а НЕ по characterId — WS-гейтвей знает только userId (из JWT), characterId он не видит.
  Поэтому StoredSession должна нести userId (добавь поле). Хранение сессии остаётся по ключу battle:{characterId}.
  Стрим: state на каждое значимое изменение + не реже BATTLE_KEYFRAME_MS; иначе пропускать.

finalize(session, result): в prisma.$transaction:
  - VICTORY: applyProgression(...) (переиспользовать!), loot=generateLoot(monsterId),
    addLootToInventory, gold += monster.goldReward, **prisma.characterKill.upsert** по
    (characterId, spawnId) с killedAt=now (НЕ create — спавн мог быть убит на прошлой неделе,
    @@unique без недели; upsert обновит killedAt) (НЕ alive=FALSE!), battleLockUntil=null.
  - DEFEAT: exp -= floor(currentLevelExp*0.05) (без понижения уровня), battleLockUntil = now+DEFEAT_LOCK_SECONDS.
  - ESCAPE: ничего не начисляем, спавн не трогаем.
  - всегда: battleLog.create(result, expDelta, goldDelta, lootJson, durationSec = round(elapsedMs/1000)).
  затем store.clear(characterId), publish 'end' c BattleEndDto, снять интервал.

КОНСТАНТЫ: BATTLE_TICK_MS=250, BATTLE_KEYFRAME_MS=1000, BATTLE_MAX_DURATION_S=300, INTERACTION_RADIUS_M=env(50).
Добавь INTERACTION_RADIUS_M в .env.example.

battle.controller.ts: добавь @MessagePattern на BATTLE_ACTION/BATTLE_FLEE/BATTLE_RESUME → методы сервиса.

Тесты: start-валидации (lock/distance/already-killed/incapacitated → нужные исключения);
finalize VICTORY пишет CharacterKill и НЕ трогает alive; DEFEAT ставит lock и штраф XP;
прогрессия/лут переиспользуются (мок prisma/characterService/store). Тик-петлю в юнитах
не гонять по таймеру — тестируй finalize и валидации; сам tick уже покрыт в B1.

НЕ делай: не дублируй формулы боя (всё в engine/tick); не оставляй alive=FALSE; не считай награды вне транзакции.

DoD: `npx nx test game-core` зелёный; `npx tsc --noEmit -p apps/game-core/tsconfig.app.json` ок; старый round-loop удалён.
```

**✅ Реализовано.** Отличия от черновика выше: дистанция = `INTERACTION_RADIUS_M` (50); `CharacterKill` через **upsert** (killedAt=now); `StoredSession` несёт **userId**; стрим публикуется в **`battle:stream:{userId}`**; finalize **перечитывает** свежие character + monster-награды (start и finalize разнесены во времени); `getActiveCharacterId(userId)` резолвит characterId в action/flee/resume; есть rehydrate сессии из Redis после рестарта и safety-timeout.

---

## Фаза B4 — WS + Redis Pub/Sub стрим (ВЫСОКИЙ РИСК → Opus) — ✅ Реализовано

```
Работаем в /Users/fost/Projects/troy/troy-backend, apps/api-gateway.

Цель — клиент по WS управляет боем и получает стрим состояния. Бой идёт по тому же
аутентифицированному сокету /game, что и движение (НЕ заводить второй namespace).

Расширь apps/api-gateway/src/app/ws/game.gateway.ts (образец — там уже есть
@SubscribeMessage('character:move'), this.rpc.send(...) через NATS, this.redisService, JWT-сокет).
Гейтвей знает userId (client.data.user.sub), characterId он НЕ видит.

Добавь @SubscribeMessage (везде userId = client.data.user.sub):
- 'battle:start'  {monsterId, spawnId} → rpc.send(BATTLE_START,{userId,monsterId,spawnId}) → BattleStateDto;
    ensureBattleSubscription(client, userId) + client.emit('battle:state', state); вернуть state.
- 'battle:action' {battleId, skillCode} → rpc.send(BATTLE_ACTION,{userId,battleId,skillCode}) → вернуть ack.
- 'battle:flee'   {battleId, phase}     → rpc.send(BATTLE_FLEE,{userId,battleId,phase}) → ack.
- 'battle:resume' {battleId?}           → rpc.send(BATTLE_RESUME,{userId,battleId}); если {accepted,state} —
    ensureBattleSubscription + emit('battle:state', state); вернуть результат.

Redis Pub/Sub стрим:
- Подписка ПО userId: канал `battle:stream:${userId}` (game-core публикует туда же).
- Отдельное подписочное соединение НА СОКЕТ, хранится на client.data.battleSub
  (тип ReturnType<RedisService['getClient']>), а НЕ в Map:
  ensureBattleSubscription(client, userId): если battleSub уже есть — выйти (идемпотентно);
    sub = redisService.getClient().duplicate(); client.data.battleSub = sub;
    sub.on('message', (_ch, raw) => { const {type,payload}=JSON.parse(raw);
      client.emit(type==='end'?'battle:end':'battle:state', payload);
      if (type==='end') void closeBattleSubscription(client); });
    await sub.subscribe(`battle:stream:${userId}`);
  closeBattleSubscription(client): sub.quit() + client.data.battleSub = undefined.
- handleDisconnect → await closeBattleSubscription(client) (не оставлять висящих соединений).

НЕ делай: не считай бой в gateway (он только проксирует RPC и форвардит Redis-сообщения);
не подписывайся одним соединением на обычные команды; не забудь cleanup на disconnect и на 'end'.

DoD: `npx tsc --noEmit -p apps/api-gateway/tsconfig.app.json` ок; ручной прогон: battle:start →
приходят battle:state → battle:action меняет состояние → battle:end по победе/поражению;
disconnect не оставляет висящих Redis-подписок.
```

**✅ Реализовано.** Канал стрима — `battle:stream:{userId}`; подписчик на `client.data.battleSub` (одно соединение на сокет, идемпотентно), закрывается на `battle:end` и на disconnect; добавлен helper `requireUser`. Бэкенд Шага 3 (B0–B5) завершён; осталась клиентская часть Flutter (F1–F3).

---

## Фаза B5 — Seed скиллов

```
Работаем в /Users/fost/Projects/troy/troy-backend, prisma/seed.ts.

Добавь в сид по 2 скилла на класс (ClassSkill) и по 1 скиллу части мобов (MonsterSkill).
Значения — ПЛЕЙСХОЛДЕРЫ для проверки движка, не финальный баланс (баланс — Шаг 5).

Warrior (resourceType RAGE): 
  - heavy_strike: slot 1, unlockLevel 1, castTimeSec 0, cooldownSec 4, resourceCost 25,
    damageType PHYSICAL, baseDamage 20, scalingStat STR, scalingRatio 1.2, effectType NONE.
  - shield_slam: slot 2, unlockLevel 3, castTimeSec 0, cooldownSec 8, resourceCost 35,
    damageType PHYSICAL, baseDamage 10, scalingStat STR, scalingRatio 0.6, effectType STUN, effectValue 0, effectDurationSec 1.5.
Mage (resourceType MANA):
  - fireball: slot 1, unlockLevel 1, castTimeSec 1.5, cooldownSec 3, resourceCost 25,
    damageType MAGICAL, baseDamage 30, scalingStat INT, scalingRatio 1.2, effectType NONE.
  - frost_bolt: slot 2, unlockLevel 2, castTimeSec 1.0, cooldownSec 5, resourceCost 30,
    damageType MAGICAL, baseDamage 18, scalingStat INT, scalingRatio 0.8, effectType SLOW, effectValue 30, effectDurationSec 3.
MonsterSkill (паре мобов, по вкусу): code 'mob_smash', castTimeSec 0, cooldownSec 6,
  damageType PHYSICAL, baseDamage 12, scalingStat STR, scalingRatio 0.5, effectType NONE, sortOrder 0.

Используй upsert по уникальным ключам (ClassSkill @@unique([class,code]); MonsterSkill @@unique([monsterId,code])),
чтобы сид был идемпотентным.

DoD: `npm run prisma:seed` отрабатывает повторно без ошибок; скиллы в БД.
```

---

## Flutter F1–F3

Эталон во всём — фича `auth` (`troy-flutter/lib/features/auth/**`): слои domain/data/presentation,
`Either<Failure,T>`, `mapErrorToFailure`, DI в `lib/app/di/injection.dart`, тесты `flutter_test`+`mocktail`.
Каждый промт начинать с «прочитай эталон auth и Architecture rules в troy-flutter/CLAUDE.md».

### F1 — domain (делегат)

```
troy-flutter. Создай lib/features/battle/domain по образцу auth:
- entities (freezed): BattleState, BattleCombatant, BattleEffect, BattleCast, BattleSkill,
  BattleResultData (поля 1:1 с DTO из backend B0: hp/maxHp/resource/effects/cast/skills/flee/log;
  result VICTORY|DEFEAT|ESCAPE, expDelta, leveledUpBy, loot, ...).
- repositories/battle_repository.dart — абстрактный интерфейс, методы возвращают
  Stream/Future<Either<Failure,T>>: startBattle, useSkill, flee(start/stop), resume,
  и Stream<BattleState> battleStream (поток состояний).
НЕ: ни Dio/socket, ни DTO в domain. DoD: flutter analyze чисто.
```

### F2 — data (делегат)

```
troy-flutter. lib/features/battle/data по образцу auth:
- datasources/battle_socket_datasource.dart — обёртка над socket-клиентом (тот же, что map использует
  для player:move): emit 'battle:start'/'battle:action'/'battle:flee'/'battle:resume',
  слушать 'battle:state'/'battle:end' → отдавать как поток DTO; кидать на транспортных ошибках.
- mappers/battle_mapper.dart — DTO→entity (чистые функции, таблица кейсов в тестах).
- repositories/battle_repository_impl.dart — _guard → mapErrorToFailure, маппинг.
Тесты (mocktail): repository_impl (datasource замокан: успех→Right, ошибки→нужный Failure),
мапперы. DoD: flutter analyze чисто; flutter test зелёный.
```

### F3 — presentation (делегат + ревью)

```
troy-flutter. lib/features/battle/presentation:
- bloc/battle_bloc.dart — события: BattleStarted, SkillPressed, FleePressed(start/stop), BattleResumed;
  подписка на battleStream репозитория → эмит состояний; на result.fold (без парсинга исключений).
  Состояния: loading / active(BattleState) / ended(BattleResultData) / failure.
- pages/battle_page.dart — экран из backend-состояния: HP игрока и моба (полоски),
  Rage/Mana, кнопки скиллов (серые если !usable / на кд показывать остаток), каст-бар,
  эффекты, лог; кнопка побега (hold). По 'ended' — экран результата (XP, level up, loot),
  затем возврат на карту (router). НИКАКИХ расчётов исхода/урона на клиенте.
- DI: socketDatasource → repository(интерфейс) → BattleBloc(factory) в injection.dart.
Тесты: battle_bloc (события → последовательность стейтов, репозиторий замокан),
widget-smoke экрана боя. DoD: flutter analyze чисто; flutter test зелёный.
```

---

## Чек-лист ревью после фаз (для Opus)

- B1: ядро не импортирует prisma/redis/nats; нет `Math.random`/`Date` в engine/; порядок rng-роллов (крит→dodge) совпадает с тестами; формулы 1:1 с combat.md.
- B3: победа делает `CharacterKill.create`, а `active_spawns.alive` НЕ трогается; награды только в транзакции; прогрессия/лут переиспользованы, не переписаны; единственный `Math.random` — в драйвере тика; интервалы снимаются на финале (нет утечки таймеров).
- B4: на disconnect Redis-подписки закрываются (нет утечки соединений); gateway не содержит боевой логики.
- Сквозняк: дистанция = 50 (`INTERACTION_RADIUS_M`), согласована с `canInteract` карты; «вижу кнопку боя» = «могу начать».
- Flutter: ноль game-authoritative расчётов; экран рисует только пришедший state; структура тестов зеркалит auth.

## Definition of Done всего Шага 3

`npx nx test game-core` и `npx nx build game-core`/`api-gateway` зелёные; бой проходится
от старта до результата по WS; победа пишет CharacterKill (моб исчезает только для убившего),
поражение даёт лок 60с; XP/loot переживают рестарт; `flutter analyze` чисто, `flutter test`
зелёный; клиент без расчётов исхода. Коммит. Отметить Шаг 3 [x] в execution-plan.md.
```

---

# Корректировки боя (follow-up к Шагу 3)

Три уточнения требований сверх того, что собрано в B0–B5. Дизайн-доки уже поправлены
([combat.md](../game-design/combat.md) → «Поведение моба», [battle-session.md](../technical/battle-session.md) →
темп боя + скиллы моба). Ниже — план реализации.

| Фаза | Что | Статус | Риск / кто |
|---|---|---|---|
| **C1** | Скорость боя в `.env` (`ATTACK_SPEED_FACTOR`) | ✅ сделано | низкий |
| **C2** | Игрок использует скиллы в бою | **✅ backend готов**, остаётся Flutter F3 | — |
| **C3** | Запрограммированный алгоритм боя моба | ✅ сделано (нужна миграция 0005 + reseed) | высокий |

Порядок: **C1** (быстро) → **C3** (мясо) → **C2** (верификация после Flutter F3).

## C1 — Скорость боя в .env — ✅ Реализовано

Выбран простой подход: глобальный множитель скорости атаки, а не множитель времени.

- `battle.service.ts`: `ATTACK_SPEED_FACTOR = Number(process.env.ATTACK_SPEED_FACTOR) || 1`
  (паттерн как `INTERACTION_RADIUS_M`). Применён в `buildPlayerCombatant`/`buildMonsterCombatant`:
  `attackIntervalSec = 1 / max(attackSpeed * ATTACK_SPEED_FACTOR, 0.1)` — для обеих сторон.
- `.env.example`: добавлен `ATTACK_SPEED_FACTOR=1.0` (с комментарием).
- Эффект: <1 → автоатаки реже → бой медленнее/читаемее. Затрагивает автоатаки и
  завязанную на них генерацию ярости воина; касты/кулдауны не трогает (это и проще).
- Проверка: `tsc --noEmit` game-core 0; battle-тесты зелёные; ручной прогон с
  `ATTACK_SPEED_FACTOR=0.5` → вдвое реже удары.

> Возможное расширение (если простого фактора не хватит): полноценный множитель времени
> `dtMs = BATTLE_TICK_MS * BATTLE_SPEED` (масштабирует и касты/кд, т.к. движок параметризован `dtMs`).

## C2 — Скиллы игрока в бою (backend готов)

Бэкенд это уже умеет: `battle:action` → `BATTLE_ACTION` → `pendingSkill` → engine `applyPlayerIntent`
(валидация кд/ресурса/стана); скиллы класса грузятся в `start()` по `class` + `unlockLevel <= level`.
DTO `skills[]` (code/name/cooldownRemainingSec/usable) уже стримится.

Остаётся **только клиент** — Flutter F3: кнопки скиллов (серые при `!usable`, остаток кд) → `battle:action`.
Это уже в Flutter-промте (F3). Доп. кода на бэке не нужно (выбор «лоадаута» скиллов — пост-MVP).
Действие: сквозная верификация после F3.

## C3 — Запрограммированный алгоритм боя моба (Opus)

Сейчас движок берёт «первый скилл не на кулдауне» (`applyMonsterSkill`). Нужно: per-mob
упорядоченный алгоритм с условиями. **Полный дизайн — в [combat.md](../game-design/combat.md)
→ «Поведение моба в бою»** (эвалюатор, таблица условий, модель данных, примеры). Ниже — реализация.

- **Schema (миграция):** `MonsterSkill` += `condition String @default("always")`,
  `conditionValue Float?` (порог % для `*_hp_below`). **priority НЕ добавляем — переиспользуем
  существующий `sortOrder`** как порядок оценки (меньше = раньше).
- **Engine:** `SkillDef` += опц. `condition?: string` / `conditionValue?: number`. В
  `applyMonsterSkill` заменить «первый off-cooldown» на эвалюатор: идти по порядку (массив уже
  отсортирован сервисом по sortOrder), брать первый скилл, у которого cooldownReady И
  `conditionMet`. Условия (чисто, без рандома, по состоянию):
  - `always` → true;
  - `opener` → скилл ещё ни разу не применялся в этом бою (нет записи в `cooldowns[code]`) —
    так он срабатывает ровно один раз на старте;
  - `self_hp_below` → `monster.hp / monster.maxHp * 100 < conditionValue`;
  - `target_hp_below` → `player.hp / player.maxHp * 100 < conditionValue`.
  Дефолт при отсутствии condition — `always` (обратная совместимость).
- **Service:** маппить `condition / conditionValue` из `MonsterSkill` в `SkillDef`; порядок
  монстро-скиллов уже идёт `orderBy sortOrder asc`.
- **Seed (B5):** прописать осмысленные алгоритмы паре мобов по примерам из combat.md
  (Brute: opener-стан → self_hp_below:30 enrage → always; Shaman: target_hp_below:35 → self_hp_below:50 heal → always).
- **Доки:** combat.md ✅ детализирован, battle-session.md ✅; обновить
  [database-schema.md](../technical/database-schema.md) после миграции.
- **Тесты (engine):** выбор по приоритету (sortOrder); `self_hp_below` срабатывает ниже порога
  и НЕ срабатывает выше; `opener` применяется один раз и больше нет; `target_hp_below`;
  fallback — когда ни одно условие не выполнено, скилла нет (работает автоатака).
- DoD: миграция применяется; engine-тесты зелёные; `tsc` 0; seed идемпотентен; combat.md ↔ код согласованы.

**✅ Реализовано.** Миграция `0005_monster_skill_algorithm` (поля `condition`/`conditionValue`,
priority = `sortOrder`); эвалюатор `monsterConditionMet` в движке; маппинг в сервисе; сиды
(Brute: opener-стан → self_hp_below:30 → always; Caster: target_hp_below:35 → always);
+5 engine-тестов. Оффлайн-проверка зелёная (`tsc` 0, battle 34/34). **Применить к БД:**
`npx prisma migrate deploy` (или dev) + `npm run prisma:seed`.
Замечание: сиды используют только рабочие эффекты (STUN/урон) — `SLOW/BUFF/ABSORB` движок
пока не применяет, а `HEAL` лечит противника, а не себя (отдельная задача по effect-фреймворку).
