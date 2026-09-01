# Этап 1 — Паки: 1 игрок × N мобов

> **Статус: в работе (взят 01.09).** Решение: этап взят раньше исходного порядка
> (до закрытия MVP-3) — осознанно. Прототип UI:
> [battle-screen-pack.html](../../design/prototypes/battle-screen-pack.html).

Первый этап [группового боя](./README.md): бой против нескольких мобов одновременно.
Социального слоя нет — весь рефакторинг модели сессии делается здесь и сразу в общем
виде (списки участников, цели), чтобы этап 2 (кооп) не переделывал боёвку ещё раз.

## Продуктовый результат

- На карте встречаются паки: маркер моба с бейджем «×3»; тап — обычный старт боя.
- В бою — 2–4 моба на арене, каждый живёт своей жизнью: свои HP, каст, эффекты, интенты.
- Игрок выбирает цель тапом по мобу; убил — цель автоматически переключается на следующего.
- У игрока — окошко «цель» (кого бью я), у каждого моба — «кого бьёт он»
  (в этапе 1 всегда игрока, но UI-место закладывается под кооп).
- Победа — когда мертв весь пак; XP/лут — за всех.

## Ограничения этапа (осознанные)

- **Пак гомогенный**: N инстансов одного `Monster`. Смешанные составы и «вожак» — позже
  (упрощает спавн, визуалы грузятся один раз, баланс-формулы проще).
- **Скиллы игрока — single-target** (все 4 текущих скилла обоих классов и так бьют одну
  цель). AoE/cleave — задел контракта, не этап 1.
- **Цель моба фиксирована** — единственный игрок. Аггро-логика — этап 2.

---

## 1. БД и спавн

### `active_spawns.pack_size`

Таблица вне Prisma (PostGIS), правится raw SQL миграцией (только ADD COLUMN,
накатывать `migrate deploy` — **не** `migrate dev`, см. память/CLAUDE.md):

```sql
ALTER TABLE active_spawns ADD COLUMN pack_size SMALLINT NOT NULL DEFAULT 1;
```

Также добавить колонку в `docker/postgres/init.sql` (свежие установки).

### `Monster.packMin` / `Monster.packMax` (Prisma)

```prisma
packMin Int @default(1)
packMax Int @default(1)
```

Обычная Prisma-миграция (ADD COLUMN). Админка: два числовых поля в форме моба
(валидация `1 ≤ packMin ≤ packMax ≤ 4`). Seed: `dire_wolf` 2–3, `forest_rat` 2–3,
остальные 1–1. Карточки мобов ([mobs/](../../mobs/README.md)) — добавить строку
«Пак» в статблок волка и крысы.

### Spawn-cron и карта

- `spawn-cron.service`: при генерации спавна `pack_size = randInt(packMin, packMax)`.
- `/map/entities` (+ WS-пуш карты): в DTO моба добавить `packSize: number`.
  Клиент рисует бейдж «×N» на маркере при `packSize > 1` — чисто UI, без новых ассетов.

`CharacterKill`, недельный сброс, персональная видимость — **без изменений**: пак — это
один спавн (одна строка `active_spawns`), килл пака = один `INSERT CharacterKill`.

---

## 2. Сессия в Redis (v2)

`battle:{characterId}` — поле `monster` заменяется списком `monsters`, у игрока появляется цель:

```json
{
  "battleId": "uuid", "characterId": "uuid", "spawnId": "uuid",
  "monsterId": "uuid", "packSize": 3,
  "status": "active", "startedAt": "...", "tick": 42,
  "player": {
    "hp": 180, "maxHp": 240, "resourceType": "RAGE", "resource": 35, "maxResource": 100,
    "attackIntervalSec": 1.05, "nextAutoAtMs": 1380, "effects": [], "cast": null,
    "targetInstanceId": "m2"
  },
  "monsters": [
    { "instanceId": "m1", "hp": 0,  "maxHp": 64, "alive": false,
      "attackIntervalSec": 1.4, "nextAutoAtMs": 900,
      "effects": [], "cast": null, "cooldowns": { "mob_bite": 2.1 },
      "targetId": "player" },
    { "instanceId": "m2", "hp": 41, "maxHp": 64, "alive": true, "...": "..." },
    { "instanceId": "m3", "hp": 64, "maxHp": 64, "alive": true, "...": "..." }
  ],
  "cooldowns": { "heavy_strike": 2.1 },
  "flee": null
}
```

- `instanceId` — `"m1"…"mN"`, стабилен на весь бой.
- Кулдауны и «spent»-флаги скиллов моба — **per-инстанс** (каждый волк кастует сам).
- Мёртвый моб: `alive:false`, эффекты/каст сброшены, движок его пропускает.
- 1v1 — вырожденный случай: `monsters` из одного элемента. Отдельной «старой» ветки кода нет.

---

## 3. Контракт (WS + NATS)

Ломающее изменение `BattleStateDto`: клиент и сервер обновляются одним релизом
(соло-разработка), слой совместимости не делаем.

### WS клиент → сервер

```typescript
'battle:start'  { monsterId, spawnId }                    // без изменений
'battle:action' { battleId, skillCode }                   // бьёт по ТЕКУЩЕЙ цели
'battle:target' { battleId, targetInstanceId }            // НОВОЕ: смена цели
'battle:flee'   { battleId, phase }                       // без изменений
'battle:resume' { battleId? }                             // без изменений
```

Смена цели — отдельное намерение, а не параметр `action`: тап по мобу и тап по скиллу —
независимые жесты, и клиент не должен угадывать цель в момент каста. Ack на `battle:target`:
`{ accepted, reason?: 'invalid_target' }` (мёртвый/несуществующий инстанс). Смена цели
применяется сразу (не на тике) — она не меняет игровое состояние, только адресацию.

### `BattleStateDto` v2 (contracts.ts)

```typescript
export interface BattleMonsterDto extends BattleCombatantDto {
  instanceId: string;              // НОВОЕ
  alive: boolean;                  // НОВОЕ
  targetId: 'player';              // НОВОЕ: кого бьёт моб (под кооп — id участника)
  name: string; level: number;
  skills: BattleMonsterSkillDto[]; // интент-лента, per-инстанс (кулдауны свои)
}
export interface BattlePlayerDto extends BattleCombatantDto {
  resourceType: 'RAGE'|'MANA'; resource: number; maxResource: number;
  targetInstanceId: string | null; // НОВОЕ: null — все мобы мертвы (мгновение до end)
}
export interface BattleStateDto {
  battleId: string; status: 'active'; elapsedMs: number;
  arenaBackground: ClassSpriteSheet | null;
  player: BattlePlayerDto;
  monsters: BattleMonsterDto[];    // БЫЛО: monster: BattleMonsterDto
  skills: BattleSkillDto[]; flee: { remainingSec: number } | null;
  log: BattleLogEntryDto[];
}
```

`BattleLogEntryDto`: `source: 'player'|'monster'` остаётся, добавляется
`sourceInstanceId?: string` и `targetInstanceId?: string` (для строк «Волк №2 укусил…»
и адресных цифр урона). Новый `kind: 'death'` — смерть моба (клиент играет death-анимацию
и авторетаргет).

### NATS

- Новый RPC `battle.target` (`BattleTargetRequest { userId, battleId, targetInstanceId }`).
- Остальные паттерны и `battle.stream.{characterId}` — без изменений (payload — новый DTO).

### `BattleEndDto`

Без структурных изменений: `expDelta`/`goldDelta` — суммы по паку, `loot[]` — общий список.

---

## 4. Движок (TickEngine)

Порядок тика (расширение текущего, [battle-session.md](../../technical/battle-session.md#тик-движок-tickengine)):

1. `elapsedMs` += tick;
2. эффекты: игрок + каждый живой моб (DOT/снятие истёкших);
3. касты: игрок (в цель `targetInstanceId`; если цель умерла до конца каста — каст
   доводится в **новую** авто-выбранную цель); каждый живой моб — в игрока;
4. автоатаки: игрок → цель; каждый живой моб → игрок (Rage воина растёт с каждого
   полученного удара — формула не меняется, источников просто несколько);
5. намерение игрока (скилл) — в текущую цель;
6. AI мобов: тот же алгоритм приоритет+условие (combat.md → «Поведение моба в бою»),
   но **на каждый инстанс отдельно** — свои кулдауны, свой `spent`, свои условия
   (`self_hp_below` — HP этого инстанса);
7. побег — без изменений;
8. смерть моба: `alive=false`, снять его каст/эффекты, лог `kind:'death'`; если это была
   цель игрока — авторетаргет: первый живой по порядку `instanceId`;
9. конец боя: все мобы мертвы → VICTORY; игрок мертв → DEFEAT; timeout → DEFEAT.

Рассинхрон автоатак пака (чтобы урон не приходил «пачкой» и читался):
на старте `nextAutoAtMs` i-го инстанса сдвигается на `i * 400ms`.

### Награды (финализация, в транзакции — как сейчас)

- XP и gold: `база_моба × PACK_REWARD_TOTAL(n)` (см. баланс), одной суммой.
- Лут: roll дроп-таблицы **на каждого моба пака** (щедро; ужмём в MVP-4, если перекос).
- `CharacterKill` — один INSERT (спавн один), `BattleLog` — одна запись.

---

## 5. Баланс (черновые числа, финальная настройка — MVP-4)

Пак из N мобов должен быть опаснее соло-моба, но не в N раз. Статы инстанса
масштабируются при сборке Combatant'ов (сам `Monster` в БД не трогаем):

| Константа (env) | Формула | n=1 | n=2 | n=3 |
|---|---|---|---|---|
| `PACK_TOTAL_DMG(n) = 1 + PACK_DMG_PER_EXTRA×(n−1)`, per-моб `/n` | урон инстанса | 1.0 | 0.575 | 0.43 |
| `PACK_TOTAL_HP(n) = 1 + PACK_HP_PER_EXTRA×(n−1)`, per-моб `/n` | HP инстанса | 1.0 | 0.625 | 0.5 |
| `PACK_REWARD_TOTAL(n) = PACK_TOTAL_HP(n)` | XP/gold за пак | ×1.0 | ×1.25 | ×1.5 |

Дефолты: `PACK_DMG_PER_EXTRA = 0.15`, `PACK_HP_PER_EXTRA = 0.25`.
Итог для пака ×3: суммарный DPS ≈ 1.3× соло, суммарное HP ≈ 1.5× соло, награда ×1.5.
Интуиция: бой дольше и опаснее, но каждый отдельный волк — заметно слабее одиночного.

---

## 6. Клиент (Flutter)

Эталон раскладки — [battle-screen-pack.html](../../design/prototypes/battle-screen-pack.html).

### Данные

- `battle_state.dart`: `monster` → `List<BattleMonster> monsters`; `BattlePlayer.targetInstanceId`.
- `battle_monster.dart`: `instanceId`, `alive`, `targetId`.
- Маппер, datasource (`battle:target` emit), repository, bloc: событие
  `BattleTargetSelected(instanceId)`; лог-энтити — `sourceInstanceId`/`targetInstanceId`.

### Экран боя

- **Сцена**: раскладка инстансов по фикс-позициям на плоскости земли
  (1 — центр; 2 — два по диагонали; 3 — треугольник, дальний меньше; 4 — ромб).
  Один спрайт-лист на всех: рассинхрон стартового кадра idle, flip части инстансов,
  scale по плану (дальний 0.85). Мёртвый — death-анимация, затем труп тускнеет.
- **Тап по мобу** = смена цели: маркер-кольцо под целью, плашка цели подсвечена.
- **Плашки врагов** (вместо одной полосы boss): компактный ряд/столбик по инстансам —
  имя+«№», мини-HP; плашка текущей цели раскрыта (крупная полоса с числами, каст-бар,
  чипы эффектов).
- **Окошко «цель» у игрока**: в блоке игрока рядом с портретом — мини-портрет/имя
  текущей цели (прототип показывает где).
- **Окошко «цель» у моба**: на плашке инстанса — «→ ВЫ» (этап 1 константа; место под кооп).
- **Лента намерений (P5)** — привязана к **текущей цели** (интенты остальных не едут);
  у нецелевого моба, начавшего каст, — «!» над спрайтом (телеграф уже есть).
- **Цифры урона / хореография**: якорятся к инстансу по `targetInstanceId`/`sourceInstanceId`.
- Авторетаргет по `kind:'death'` — клиент просто следует `player.targetInstanceId` из снапшота.

---

## 7. Тесты (DoD, стек как в фазах)

Backend (Jest, мок Prisma/Redis/NATS):

- `engine.spec`: тик с 2+ мобами (каждый бьёт/кастует независимо); авторетаргет при
  смерти цели; каст игрока доводится в новую цель; VICTORY только когда мертвы все;
  Rage растёт от ударов нескольких мобов; рассинхрон `nextAutoAtMs`.
- `formulas.spec`: pack-факторы (таблица n=1..4, n=1 — тождество).
- `battle.service.spec`: `battle.target` — валидация (мёртвый/чужой инстанс → reject);
  награды: XP/gold × `PACK_REWARD_TOTAL`, лут N roll'ов, один `CharacterKill`.
- `spawn-cron.service.spec`: `pack_size ∈ [packMin, packMax]`.

Flutter (`flutter_test` + `mocktail`): маппер `monsters[]`; bloc — смена цели
(оптимистично + откат по reject-ack), state с мёртвым мобом; widget-smoke боя с паком.

## 8. DoD этапа

- [ ] Волки/крысы спавнятся паками 2–3, маркер с бейджем «×N».
- [ ] Бой против пака: мобы действуют независимо, смена цели тапом, окошки «цель»
      у игрока и мобов, лента намерений следует за целью.
- [ ] Убийство части пака меняет картину боя (death-анимация, авторетаргет), победа —
      только когда мертвы все; награды по формулам пака; один `CharacterKill`.
- [ ] 1v1-бои работают как раньше (вырожденный случай, без отдельной ветки кода).
- [ ] `battle-session.md` обновлён до v2 (сессия, DTO, события) — этот документ
      остаётся спекой этапа, контракт живёт там.
- [ ] Тесты раздела 7 зелёные; `npx nx run-many -t test` и `flutter analyze && flutter test` чистые.

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила
> (архитектура, тесты, делегирование) — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy (backend troy-backend + клиент troy-flutter).

Задача: этап 1 группового боя — паки мобов (1 игрок × N мобов).
Спека: troy-docs/roadmap/group-battle/stage-1-packs.md — прочитай целиком и следуй ей.
Контекст: troy-docs/technical/battle-session.md (текущий контракт боя),
troy-docs/game-design/combat.md (правила боя), прототип UI —
troy-docs/design/prototypes/battle-screen-pack.html (открыть в браузере).

Порядок:
1. БД/спавн: pack_size в active_spawns (raw SQL, migrate deploy, НЕ migrate dev),
   Monster.packMin/packMax (Prisma), spawn-cron, packSize в /map/entities, seed волка/крысы.
2. Контракт: BattleStateDto v2 (monsters[], targetInstanceId), battle:target, лог
   с sourceInstanceId/targetInstanceId и kind:'death'. Обновить battle-session.md.
3. Движок: monsters[] в сессии, per-инстанс AI/кулдауны, авторетаргет, победа «все мертвы»,
   pack-факторы статов и наград (env-константы из спеки).
4. Flutter: entities/mappers/bloc/datasource, сцена с N инстансами одного спрайт-листа
   (рассинхрон idle, flip, scale), тап=цель, плашки врагов, окошки «цель», лента
   намерений по цели. Раскладка — по прототипу.
5. Тесты по разделу 7 спеки. Бэкенд: npx nx run-many -t test. Клиент: flutter analyze,
   flutter test.

Backend-код — по troy/CLAUDE.md, Flutter — строго по Architecture rules из
troy-flutter/CLAUDE.md (эталон — фича auth). Ветка main, коммиты без подписей ассистента.
По завершении: обновить баннер статуса в stage-1-packs.md и таблицу в roadmap/README.md.
```
