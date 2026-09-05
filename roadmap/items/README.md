# Предметы — ilvl, редкость, класс-ограничения, зелья в бою

> **Статус: спека (05.09), код не начат.** Сквозная тема поверх [mvp-3-inventory](../mvp-3-inventory/README.md)
> (модель и эндпоинты) и [mvp-4-content-balance](../mvp-4-content-balance/README.md) (контент). Эпик
> [SCRUM-61](https://fosteev.atlassian.net/browse/SCRUM-61). Решения: itemLevel + requiredLevel — **да**;
> редкость = бюджет статов — **да**, правило для контента, не код; class restrictions — **да**, массив кодов
> + личный лут; зелья — **в бою, одно за бой**, персистентный HP не заводим; стак экипировки — **без миграции**;
> вторичные статы на шмоте — **только crit и dodge**; лимит мешка — **на бэкенде**; торговля, сеты, апгрейд
> за золото — **потом**.

Что докрутить в предметах «по образцу WoW», не превращая мобилку в таблицу: уровень предмета как хребет
прогрессии, редкость, которая что-то значит, шмот по классу, зелье как боевое действие. Аудит текущего
состояния — ниже, чтобы не перечитывать код.

## Аудит (05.09)

| Слой | Как есть |
|---|---|
| `Item` | name, type (WEAPON / ARMOR / CONSUMABLE), 6 слотов (HEAD, BODY, WEAPON, SHIELD, BOOTS, ACCESSORY), 5 редкостей, 9 плоских бонусов (STR/INT/STA/AGI/SPI, armor, MR, physDmg, magicDmg), iconUrl |
| Инвентарь | строка на (персонаж, предмет): quantity + isEquipped; equip авто-снимает слот |
| Лут | `DropTable` per монстр (weight / minQty / maxQty + `nothingWeight`), ролл на каждого моба пака |
| Статы | бонусы → `totalAttributes` → производные; physDmg/magicDmg — прямо в physAtk/magicAtk (сырой урон автоатаки) |
| Контент | 5 предметов, одна drop-таблица на все 10 мобов, HEAD и ACCESSORY пустые |
| API | `GET /inventory`, `POST /inventory/equip/:itemId`, `POST /inventory/unequip/:slot`. Нет use / discard / sell |

Что хромает:

- **Редкость косметическая** — не влияет ни на статы, ни на шанс дропа. Swift Boots «RARE» (+3 AGI, +1 armor) слабее «UNCOMMON» щита.
- **Нет уровня предмета и требований** — голем 10 lvl дропает тот же Iron Sword, что крыса; прогрессии лута нет по определению.
- **Consumable без механики** — тип есть, полей эффекта и эндпоинта нет; HP между боями не персистится.
- **Доки обещают dodge и crit от шмота** ([stats-and-formulas.md](../../game-design/stats-and-formulas.md)), в коде dodge = 0 захардкожен (`character.service.ts`), полей у `Item` нет.
- **Золото без sink** — копится, потратить негде (торговля вырезана из MVP).
- **Стак экипировки двусмысленный** — «Iron Sword ×3 (equipped)», бонус один раз.
- **Лимит мешка только на клиенте** (40), бэкенд бесконечный.

Гэпы MVP-3 ([backend-gaps.md](../mvp-3-inventory/backend-gaps.md)) #1–#6 на момент аудита открыты; #2, #4, #5 решены здесь.

## Продуктовый результат

- Лут растёт с мобом: у мобов 8–10 lvl падают предметы itemLevel 8–10, а не Iron Sword.
- Редкость значит: epic того же ilvl заметно жирнее common и падает реже.
- Маг не таскает щиты: чужой шмот не падает, а если попал в мешок — не надевается.
- Зелье — кнопка в бою: одно за бой, лечит или восстанавливает ресурс.
- Карточка предмета: ilvl, требование уровня, класс, crit/dodge; ▲ апгрейд — по ilvl.
- Мешок конечен: 40 слотов, при полном мешке лут теряется с уведомлением.

---

## 1. Данные

`Item`, миграция `0019_item_progression` (накатывать `migrate deploy`, **не** `migrate dev` — дропнет
`active_spawns`):

```prisma
itemLevel         Int      @default(1)   // уровень предмета: бюджет статов и «▲ апгрейд»
requiredLevel     Int      @default(1)   // ниже — equip отказывает
allowedClassCodes String[] @default([])  // CharacterClass.code; пусто = всем
critChanceBonus   Float    @default(0)   // %, суммируется в critChance
dodgeBonus        Float    @default(0)   // %, суммируется в dodge (сейчас захардкожен 0)
hpRestore         Int      @default(0)   // CONSUMABLE: лечение в бою
resourceRestore   Int      @default(0)   // CONSUMABLE: мана/ярость по resourceType
description       String?                // гэп #1 MVP-3 (SCRUM-15) — можно той же миграцией
```

Классы — данные (`CharacterClass`), поэтому ограничение — массив кодов, а не FK-таблица: два класса,
третий не планируется до поднятия капа. Колонки бонусов остаются колонками, не JSON: суммируются
в одном месте (`getEquipmentBonuses`), а рефакторинг на JSON тронул бы контракты, админку и клиент
ради двух новых полей.

Контракты (`libs/shared/contracts`), Swagger DTO, `AdminItemDto`, `InventoryItem` на клиенте — новые поля
транзитом. `technical/database-schema.md` обновить.

## 2. Механики

### 2.1 Проверки в equip: уровень и класс

`InventoryService.equip`: `character.level < requiredLevel` → 400 `level_too_low`; код класса не в
непустом `allowedClassCodes` → 400 `class_not_allowed`. Клиент: «Требуется уровень N» красным, тег
класса, Equip disabled — кнопка не должна доводить до 400.

### 2.2 Личный лут по классу

Как WoW personal loot: `BattleService.generateLoot` перед взвешиванием отбрасывает строки `DropTable`,
чей предмет персонаж не может надеть по классу. `nothingWeight` не меняется — шанс «ничего» тот же,
меняется только состав. Иначе при двух классах маг половину мешка забьёт щитами.

### 2.3 Зелья в бою

Правило WoW «одно зелье за бой» ложится на реалтайм-бой напрямую и снимает вопрос персистентного HP:
вне боя HP всегда полный, там зелье бессмысленно.

- WS `battle:use_item { itemId }`: CONSUMABLE и quantity > 0; heal / restore к Combatant игрока с clamp
  по max; декремент quantity (удаление строки при 0) в той же транзакции; событие `kind: 'item'` в ленту.
- Один раз за бой: `potionUsed` в сессии, повтор → ack `potion_used`. Во время каста — ack `casting`,
  как у инстантов.
- HUD: кнопка зелья рядом со скиллами, иконка + количество, disabled после использования.
- Seed: Health Potion `hpRestore` ≈ 40 % HP воина 1 lvl (≈ 60).

### 2.4 Стак экипировки

Без миграции. `quantity` — число копий, `isEquipped` — «одна копия надета», бонус считается один раз;
это и есть контракт. Клиент показывает «×3, 1 надета». Лишние копии — discard (SCRUM-16). Дубликаты
экипировки в дропе допустимы; пересмотреть, когда появится sink за золото (см. «Потом»).

### 2.5 Лимит мешка

`INVENTORY_MAX_SLOTS` (env, default 40), слот = строка `CharacterInventory` (стак — один слот).
В `addLootToInventory` новые строки сверх лимита не создаются, инкремент стаков — разрешён;
потерянное — списком `lostLoot` в `battle:end`, экран результата показывает «мешок полон».
`GET /inventory` отдаёт `capacity`, клиент перестаёт хранить константу. Зависит от discard (SCRUM-16).

### 2.6 Вторичные статы

`critChance = AGI × 0.15 + Σ critChanceBonus`, `dodge = Σ dodgeBonus` — как в
[stats-and-formulas.md](../../game-design/stats-and-formulas.md), только теперь с источником.
Больше двух вторичных не заводим (haste — если понадобится, в MVP-4 отдельным решением).

## 3. Правило контента: бюджет статов

В WoW редкость при равном ilvl — просто больший бюджет. У нас редкость станет значить то же самое,
но правилом для контента (и линтером сида потом), не кодом. Стартовые цифры — калибровать в
`game-design/loot-and-items.md` (SCRUM-34) против таблиц классов:

```
budget(itemLevel) = 3 + itemLevel          // очков бюджета на предмет
mult(rarity):  COMMON 1.0 · UNCOMMON 1.2 · RARE 1.45 · EPIC 1.75 · LEGENDARY 2.1
```

Цена статов в очках бюджета (стартовая):

| Стат | Очков за единицу |
|---|---|
| STR / INT / STA / AGI / SPI | 1 |
| physDmg / magicDmg | 1 |
| armor / magicResist | 0.5 |
| crit / dodge | 2 за 1 % |

Проверка на текущем сиде: Iron Sword = 6, Leather Armor = 3.5, Knight Shield (UNCOMMON) = 5,
Swift Boots (RARE) = 3.5 — бюджеты вразнобой, что и есть проблема. Слоты равноценны; коэффициенты по
слотам (оружие жирнее ботинок) — только если баланс попросит.

Веса редкости в дропе и распределение по itemLevel 1–10 — в `loot-and-items.md`; набор 20–30
предметов на все 6 слотов — SCRUM-50; персональные drop tables по уровню моба — SCRUM-36.

## 4. Что не тащим

16 слотов, прочность и ремонт, сокеты, зачарование, реформинг, трансмог, BoP/BoE, скорость оружия и
1H/2H, gearscore. Шесть слотов и два вторичных стата на мобиле читаются как система, а не как таблица.

## 5. Порядок и задачи

| # | Что | Jira | Где |
|---|---|---|---|
| 1 | Гэпы MVP-3: description, discard, стак (решение записано) | [SCRUM-15](https://fosteev.atlassian.net/browse/SCRUM-15), [SCRUM-16](https://fosteev.atlassian.net/browse/SCRUM-16), [SCRUM-18](https://fosteev.atlassian.net/browse/SCRUM-18) | mvp-3 |
| 2 | Миграция `item_progression`: ilvl, requiredLevel, crit/dodge; проверка уровня в equip; статы | [SCRUM-62](https://fosteev.atlassian.net/browse/SCRUM-62) | items |
| 3 | Class restrictions + личный лут | [SCRUM-17](https://fosteev.atlassian.net/browse/SCRUM-17) | items |
| 4 | Зелья в бою | [SCRUM-19](https://fosteev.atlassian.net/browse/SCRUM-19) | items |
| 5 | Админка — поля предмета | [SCRUM-63](https://fosteev.atlassian.net/browse/SCRUM-63) | items |
| 6 | Flutter — карточка предмета, ▲ по ilvl, кнопка зелья | [SCRUM-64](https://fosteev.atlassian.net/browse/SCRUM-64) | items |
| 7 | Лимит мешка | [SCRUM-65](https://fosteev.atlassian.net/browse/SCRUM-65) | items |
| 8 | Контент: `loot-and-items.md`, набор предметов, drop tables | [SCRUM-34](https://fosteev.atlassian.net/browse/SCRUM-34), [SCRUM-50](https://fosteev.atlassian.net/browse/SCRUM-50), [SCRUM-36](https://fosteev.atlassian.net/browse/SCRUM-36) | mvp-4 |

Шаги 2–4 — одна миграция и одна сессия, если делаются подряд. Шаг 7 — после SCRUM-16.
Контент MVP-4 заводить уже с ilvl и бюджетом, поэтому items идёт до MVP-4.

## Потом (в Jira не заводим до MVP-4)

- **Апгрейд предмета за золото** (+1 ilvl за N золота) — sink вместо вырезанной торговли; скорее
  Diablo Immortal, чем WoW, но задачу решает одной таблицей стоимости.
- **Сеты** (бонус за 2/4 предмета) — `setId` + таблица бонусов, дёшево по коду, дорого по контенту.
- **Линтер бюджета в сиде** — падать, если предмет вылезает за budget × mult более чем на 15 %.
- Второй слот аксессуара — только с артом и контентом.

## Definition of Done

- [ ] У предмета есть ilvl и требование уровня; equip отказывает по уровню и классу; клиент не даёт нажать Equip на недоступном.
- [ ] Лут не выдаёт шмот чужого класса.
- [ ] Зелье используется в бою один раз, quantity уменьшается, событие в ленте.
- [ ] crit/dodge от шмота видны в computed stats, dodge не захардкожен.
- [ ] Мешок ограничен на бэкенде, переполнение видно в результате боя.
- [ ] Админка и клиент показывают новые поля; тесты зелёные (`npx nx run-many -t test`, `flutter test`, `npx tsc -b --noEmit`).
- [ ] `loot-and-items.md` содержит правило бюджета; сид переведён на ilvl (сам контент — MVP-4).

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy (backend troy-backend, клиент troy-flutter, админка troy-admin).

Задача: тема items — шаги 2–4 из troy-docs/roadmap/items/README.md (миграция item_progression,
class restrictions + личный лут, зелья в бою). Спека и решения там же — не переспрашивать то,
что уже решено (баннер статуса).

Прочитай:
- troy-docs/roadmap/items/README.md целиком;
- troy-docs/roadmap/mvp-3-inventory/backend-gaps.md (гэпы #1–#6, решения по #2/#4/#5 — ссылки на items);
- troy-docs/technical/database-schema.md, troy-docs/technical/battle-session.md;
- troy-docs/game-design/stats-and-formulas.md (crit/dodge);
- troy/CLAUDE.md (backend), раздел "Architecture rules" в troy-flutter/CLAUDE.md.

Порядок:
1. Prisma: колонки из §1 одной миграцией 0019_item_progression; накатывать `migrate deploy`,
   НЕ `migrate dev` (дропнет active_spawns). Контракты, Swagger DTO, AdminItemDto, seed.
2. InventoryService.equip — level_too_low / class_not_allowed; CharacterService — crit/dodge от шмота,
   снять хардкод dodge = 0.
3. BattleService.generateLoot — фильтр строк DropTable по классу до взвешивания.
4. Зелья: battle:use_item по §2.3 (одно за бой, ack potion_used / casting), событие kind 'item',
   дополнить battle-session.md.
5. Админка (SCRUM-63): поля в ItemFormModal/ItemsPage. Flutter (SCRUM-64): ItemInspectSheet/ItemCell,
   кнопка зелья в HUD боя — по описаниям задач.

Тесты — часть DoD: unit на equip (уровень, класс), computed stats (crit/dodge), roll лута с фиксированным
RNG, движок (heal с clamp, второй use отказывает); Flutter — маппер + эвристика ▲ + widget-smoke;
админка — tsc.

Проверка: `npx nx run-many -t test` в troy-backend; `flutter analyze && flutter test` в troy-flutter;
`npx tsc -b --noEmit` в troy-admin.

Ветка main, коммиты без подписей ассистента. По завершении: отметить DoD здесь, обновить баннер статуса,
таблицу в troy-docs/roadmap/README.md и статусы задач SCRUM-62/17/19/63/64 (скилл troy-jira).
```
