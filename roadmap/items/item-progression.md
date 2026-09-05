# items — прогрессия предметов и ограничение по классу (SCRUM-62, SCRUM-17)

> **Статус: сделано (05.09).** Связка [SCRUM-62](https://fosteev.atlassian.net/browse/SCRUM-62) (itemLevel / requiredLevel / crit и dodge на шмоте, проверка уровня в equip, статы) + [SCRUM-17](https://fosteev.atlassian.net/browse/SCRUM-17) (allowedClassCodes, проверка класса в equip, личный лут по классу) — одна миграция `0020_item_progression`, одно репо `troy-backend`, одна сессия. Все 4 этапа закрыты, `npx nx run-many -t test`/`-t build` зелёные. Родитель: [README темы](./README.md) §1–2.2, эпик [SCRUM-61](https://fosteev.atlassian.net/browse/SCRUM-61).

## Зачем

Хребет прогрессии лута: у предмета появляется уровень и требование, шмот по классу перестаёт падать магу и надеваться на него, обещанные `stats-and-formulas.md` crit/dodge от шмота начинают считаться (сейчас `dodge = 0` захардкожен в `character.service.ts`). Контент MVP-4 (SCRUM-50/36) заводится уже с этими полями.

## Что нашли при разборе (05.09)

- **Единицы dodge разъезжаются.** Движок (`engine/formulas.ts`, `resolveHit`) ждёт `targetDodge` **долей** 0–1, а `critChance` — **процентами**; `Monster.dodge` в БД — доля (`AdminMonsterCreateDto`: `@Min(0) @Max(1)`), хотя `database-schema.md` пишет «(%)». `computedStats.critChance` игрока — проценты (`AGI × 0.15`), и клиент показывает его как `%`. Значит `computedStats.dodge` тоже держим в процентах, а в бой переводим `/100` — решение 3.
- **`InventoryService.equip` знает только `characterId`** (`getActiveCharacterId`), а для проверок нужны уровень и код класса — новый метод `CharacterService.getActiveCharacterBrief` (решение 4).
- **`ACTIVE_CHARACTER_SELECT` — whitelist**: новые поля предмета сами в `computeStats` не приедут, `critChanceBonus`/`dodgeBonus` надо добавить в `inventory.item.select`. `getMe` отдаёт инвентарь отдельным `include: { item: true }` — там ничего делать не надо.
- **`BattleService.finalize` читает класс персонажа** только как `class: { select: { resourceType: true } }` — для личного лута добавить `code: true`. `generateLoot` сейчас `findMany` по `dropTable` без `item` — фильтр по классу требует `include`.
- **Баг сессии 1 (SCRUM-15):** `admin-items.controller.ts` → `create()` собирает payload вручную и **не пробрасывает `description`** — предмет, созданный из админки с описанием, теряет его (update через `...dto` работает). Чиним попутно в этапе 1.
- Тесты: `battle.service.spec.ts` зовёт приватные `finalize`/`generateLoot` через `PrivateAccess`; фикстуры `dropTable` без `item` и `class` без `code` — их придётся дополнить (список в «Контракте»). `inventory.service.spec.ts` мокает `characterService.getActiveCharacterId` в тестах equip — переключить на `getActiveCharacterBrief`.
- Миграция — `0020_item_progression` (0019 занята `item_description`, см. комментарий в SCRUM-62).

## Решения (05.09)

1. **Скоуп миграции `0020_item_progression`:** только `itemLevel`, `requiredLevel`, `allowedClassCodes`, `critChanceBonus`, `dodgeBonus`. `hpRestore`/`resourceRestore` из items/README §1 — **не здесь**, они едут с зельями (SCRUM-19) своей миграцией `0021_item_consumables`.
2. **Коды ошибок equip — `LEVEL_TOO_LOW` и `CLASS_NOT_ALLOWED`** (UPPER_SNAKE, как `NOT_ENOUGH_POINTS`/`INVALID_ATTRIBUTE` в `character.service.ts`; в Jira/README написано `level_too_low` — это они). Порядок проверок: нет в инвентаре (404) → нет слота (400) → уровень → класс; всё — до транзакции. Клиент (SCRUM-64) кнопку до 400 не доводит, коды — страховка и ключ для локализации.
3. **Единицы:** `critChanceBonus`, `dodgeBonus`, `computedStats.critChance`, `computedStats.dodge` — **проценты**. В бой `buildPlayerCombatant` кладёт `dodge: stats.dodge / 100` (движок ждёт долю), `critChance` — как есть. `Monster.dodge` не трогаем (уже доля); в `database-schema.md` поправить «(%)» на «доля 0–1».
4. **`CharacterService.getActiveCharacterBrief(userId) → { id, level, classCode }`** — рядом с `getActiveCharacterId`; `equip` переходит на него, остальные методы инвентаря остаются на `getActiveCharacterId`.
5. **Личный лут — в памяти, не в SQL:** `generateLoot` подтягивает `item.allowedClassCodes` через `include` и отбрасывает строки до взвешивания; `nothingWeight` в сумме остаётся. Сигнатура — `generateLoot(monsterId, nothingWeight, rolls, classCode)`, все четыре обязательны.
6. **Валидация `allowedClassCodes` в админке — только форма:** массив строк, backend коды по таблице `CharacterClass` не проверяет (спека: FK не заводим). Форма SCRUM-63 даст select из `GET /classes`.
7. **Seed:** `requiredLevel = itemLevel`; itemLevel — минимальный уровень, при котором `budget(ilvl) × mult(rarity)` из README §3 покрывает текущую стоимость статов (статы не трогаем — это SCRUM-50). Swift Boots получают `dodgeBonus: 2` (единственный демонстрационный источник dodge, тематически «уносят из-под удара»), Knight Shield — `allowedClassCodes: ['warrior']`. Числа — в «Контракте».
8. **Swagger:** новые поля добавляются во все три DTO предмета (`InventoryItemDto`, `EquippedItemDto`, `AdminItemResponseDto`) + `AdminItemCreateDto`; классы не переименовывать (имена уезжают в Dart-клиент). `BattleLootDto` не меняется.
9. **Два коммита, по задаче:** этапы 1–2 → `items: itemLevel/requiredLevel, crit/dodge от шмота, проверка уровня в equip (SCRUM-62)`; этап 3 → `items: allowedClassCodes — проверка класса в equip, личный лут по классу (SCRUM-17)`; этап 4 (доки) — в коммит SCRUM-17 или отдельным `docs:`.

10. **Ревью сессии 1 (05.09, `/troy-plan-review`):** принято без расхождений с планом — каждый чекбокс этапов 1–4 подтверждён по дифу коммитов `c671408`, `37cdc7d`, `0d546b9` (troy-backend) и `670ba23` (troy-docs); тесты из таблиц — те же имена, проверяют заявленное (223 зелёных без кэша, `build` ок, `prisma migrate status` — 20 миграций, схема актуальна); коммиты по-русски, без подписей. Исполнитель решений по ходу не принимал. Правки ревью — только доки: в README темы §1 осталась старая `0019_item_progression` в заголовке абзаца, §5 и промт темы помечены «шаги 2–3 сделаны». Что ревью проверить не может и остаётся пользователю: gateway на :3000 — старая сборка, новые поля в Swagger/`GET /inventory` появятся после перезапуска; seed с новыми `itemLevel`/`allowedClassCodes` в базу не накатывался — `npm run prisma:seed` **сносит** `characterInventory` и предметы (`deleteMany` в начале seed), поэтому либо seed на пустой базе, либо проставить поля в админке (PUT `/admin/items/:id` уже принимает их — `allowedClassCodes: ['warrior']` у Knight Shield). Статусы Jira: SCRUM-62 и SCRUM-17 — «В процессе проверки», `Готово` ставит пользователь по чеклисту из ответа ревью.

## Этапы

### Этап 1 — SCRUM-62, схема, миграция, контракты, DTO, seed

- [x] `libs/shared/prisma/schema.prisma`, `model Item`: пять полей между `magicDmgBonus` и `description` (текст в «Контракте»).
- [x] `libs/shared/prisma/migrations/0020_item_progression/migration.sql` (текст в «Контракте»); накат `npm run prisma:migrate` (deploy), затем `npm run prisma:generate`.
- [x] `libs/shared/contracts/src/lib/contracts.ts`: `AdminItemDto` + 5 полей, `AdminItemCreatePayload` + 5 опциональных.
- [x] `apps/game-core/src/app/admin/item-admin.service.ts`: `ITEM_SELECT` + 5 полей; `toCreateData` + 5 дефолтов.
- [x] `apps/api-gateway/src/app/dto/admin/item.dto.ts`: `AdminItemResponseDto` + 5 полей, `AdminItemCreateDto` + 5 полей с валидацией (импорт `IsArray`, `IsNumber`, `Min`, `Max`).
- [x] `apps/api-gateway/src/app/admin/admin-items.controller.ts`, `create()`: пробросить `description` (баг) и 5 новых полей.
- [x] `apps/api-gateway/src/app/dto/response/inventory-response.dto.ts` → `InventoryItemDto` и `dto/response/character-response.dto.ts` → `EquippedItemDto`: 5 полей; `CharacterComputedStatsDto.critChance`/`dodge` — описания единиц.
- [x] `prisma/seed.ts`: `itemLevel`, `requiredLevel`, `allowedClassCodes`, `dodgeBonus` по таблице из «Контракта».
- [x] `apps/game-core/src/app/admin/item-admin.service.spec.ts`: в `maps weapon create payload to Prisma item.create with defaults` ожидаемый `data` + 5 дефолтов; новый кейс `create stores progression fields and class codes`.

Готово, когда: `npm run prisma:migrate` применил 0020, `npx nx run-many -t test` зелёный, `npx nx run-many -t build` собирается. **Проверено 05.09: миграция накатилась, 212 тестов game-core / 21 api-gateway зелёные, build всех трёх сервисов проходит.**

### Этап 2 — SCRUM-62, equip по уровню, crit/dodge в статах и в бою

- [x] `apps/game-core/src/app/character/character.service.ts`: `ACTIVE_CHARACTER_SELECT.inventory.select.item.select` + `critChanceBonus`, `dodgeBonus`; `EquipmentBonuses` + `critChance`, `dodge`; `getEquipmentBonuses` суммирует; `computeStats`: `critChance = totalAgility * 0.15 + bonus.critChance`, `dodge = bonus.dodge`; новый `getActiveCharacterBrief` (решение 4).
- [x] `apps/game-core/src/app/inventory/inventory.service.ts`, `equip`: `getActiveCharacterBrief`, проверка `LEVEL_TOO_LOW` (код в «Контракте»; проверку класса — этап 3).
- [x] `apps/game-core/src/app/battle/battle.service.ts`, `buildPlayerCombatant`: `dodge: stats.dodge / 100` с комментарием (решение 3).
- [x] Тесты `character.service.spec.ts`: `computeStats adds crit and dodge from equipped items`, `computeStats keeps dodge at 0 without equipment`, `getActiveCharacterBrief returns id, level and class code`, `getActiveCharacterBrief throws NotFoundException without an active character`.
- [x] Тесты `inventory.service.spec.ts`: мок `getActiveCharacterBrief` в `createService`, два существующих кейса equip переведены на него; новый `rejects equip below the required level with LEVEL_TOO_LOW`.
- [x] Тест `battle.service.spec.ts`: `buildPlayerCombatant converts profile dodge from percent to the engine fraction`.
- [x] Коммит SCRUM-62 (решение 9).

Готово, когда: `npx nx run-many -t test` зелёный; в `GET /character/me` `computedStats.dodge` = Σ `dodgeBonus` надетого (проверяется тестом, живой прогон — пользователь). **Проверено 05.09: 218 тестов game-core зелёные, build проходит.**

### Этап 3 — SCRUM-17, класс в equip и личный лут

- [x] `inventory.service.ts`, `equip`: проверка `CLASS_NOT_ALLOWED` после уровня.
- [x] `battle.service.ts`: `finalize` — `class: { select: { resourceType: true, code: true } }`, вызов `generateLoot(monsterId, monster.nothingWeight, packSize, character.class.code)`; `generateLoot` — `include` + фильтр (код в «Контракте»).
- [x] Тесты `inventory.service.spec.ts`: `rejects equip for a class outside allowedClassCodes with CLASS_NOT_ALLOWED`, `equips when allowedClassCodes contains the class`.
- [x] Тесты `battle.service.spec.ts`: фикстуры дополнены (`item: { allowedClassCodes: [] }` у каждой строки `dropTable`, `code: 'warrior'` у каждого `class`, четвёртый аргумент `'warrior'` у прямых вызовов `generateLoot`, `PrivateAccess` обновлён); новые `personal loot: a mage never rolls warrior-only rows`, `personal loot keeps the nothing bucket at the same weight`, `personal loot: a warrior still rolls the shield`.
- [x] Коммит SCRUM-17 (решение 9).

Готово, когда: `npx nx run-many -t test` зелёный, `npx nx run-many -t build` собирается. **Проверено 05.09: 223 теста game-core зелёные, build проходит.**

### Этап 4 — доки

- [x] `troy-docs/technical/database-schema.md`: 5 строк в таблице `Item` (после `magicDmgBonus`), формулы `critChance`/`dodge` в блоке производных, `Monster.dodge` — «доля 0–1 (0.05 = 5 %)».
- [x] `troy-docs/roadmap/items/README.md`: баннер статуса — «шаги 2–3 (SCRUM-62/17) сделаны 05.09, план — item-progression.md»; §1 — пометка, что `hpRestore`/`resourceRestore` едут с SCRUM-19 миграцией `0021_item_consumables`; DoD — галочки у «equip отказывает по уровню и классу» (бэкенд), «Лут не выдаёт шмот чужого класса», «crit/dodge от шмота видны в computed stats».
- [x] `troy-docs/roadmap/README.md`: строка items в «В работе» — «бэкенд ilvl/класс сделан (SCRUM-62/17), дальше зелья SCRUM-19».
- [x] `troy-backend/README.md`, таблица эндпоинтов: у `POST /inventory/equip/:itemId` — «400 `LEVEL_TOO_LOW` / `CLASS_NOT_ALLOWED`».
- [x] `troy/CLAUDE.md`, Key design decisions — пункт 12 (текст в «Контракте»).
- [x] Баннер этого файла → «сделано», галочки по факту. Затем `/troy-continue`.

Готово, когда: доки согласованы с кодом; статус в Jira — «В процессе проверки» (закрывает пользователь, увидев поля в `GET /inventory` и отказ equip на живом персонаже).

## Контракт и точки входа

### Миграция и схема

`libs/shared/prisma/migrations/0020_item_progression/migration.sql`:

```sql
-- Прогрессия предметов (roadmap/items, SCRUM-62) и ограничение по классу (SCRUM-17).
ALTER TABLE "Item"
  ADD COLUMN "itemLevel" INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN "requiredLevel" INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN "allowedClassCodes" TEXT[] DEFAULT ARRAY[]::TEXT[],
  ADD COLUMN "critChanceBonus" DOUBLE PRECISION NOT NULL DEFAULT 0,
  ADD COLUMN "dodgeBonus" DOUBLE PRECISION NOT NULL DEFAULT 0;
```

`schema.prisma`, `model Item`, между `magicDmgBonus` и `description`:

```prisma
  itemLevel         Int                  @default(1)
  requiredLevel     Int                  @default(1)
  allowedClassCodes String[]             @default([])
  critChanceBonus   Float                @default(0)
  dodgeBonus        Float                @default(0)
```

Накат **только** `npm run prisma:migrate` (deploy), затем `npm run prisma:generate`. `migrate dev` дропает `active_spawns` и `SpawnZone.geometry`.

### Контракты (`libs/shared/contracts/src/lib/contracts.ts`)

`AdminItemDto`, после `magicDmgBonus`:

```ts
  /** Уровень предмета: бюджет статов и «▲ апгрейд» на клиенте. */
  itemLevel: number;
  /** Ниже этого уровня персонажа equip отвечает 400 LEVEL_TOO_LOW. */
  requiredLevel: number;
  /** CharacterClass.code; пусто — всем классам. Чужой класс: 400 CLASS_NOT_ALLOWED, в личный лут не попадает. */
  allowedClassCodes: string[];
  /** Проценты; суммируется в computedStats.critChance. */
  critChanceBonus: number;
  /** Проценты; суммируется в computedStats.dodge. */
  dodgeBonus: number;
```

`AdminItemCreatePayload` — те же пять как `?:` (`allowedClassCodes?: string[]`).

### game-core — admin

`apps/game-core/src/app/admin/item-admin.service.ts`: в `ITEM_SELECT` после `magicDmgBonus: true,` — `itemLevel: true, requiredLevel: true, allowedClassCodes: true, critChanceBonus: true, dodgeBonus: true,`. В `toCreateData` после `magicDmgBonus`:

```ts
      itemLevel: payload.itemLevel ?? 1,
      requiredLevel: payload.requiredLevel ?? 1,
      allowedClassCodes: payload.allowedClassCodes ?? [],
      critChanceBonus: payload.critChanceBonus ?? 0,
      dodgeBonus: payload.dodgeBonus ?? 0,
```

`update` шлёт `data` как есть — не менять.

### game-core — character

`apps/game-core/src/app/character/character.service.ts`:

- `ACTIVE_CHARACTER_SELECT.inventory.select.item.select`: после `magicDmgBonus: true,` — `critChanceBonus: true, dodgeBonus: true,`.
- `interface EquipmentBonuses`: `+ critChance: number; dodge: number;`; в `getEquipmentBonuses` — `acc.critChance += entry.item.critChanceBonus; acc.dodge += entry.item.dodgeBonus;` и нули в начальном значении.
- `computeStats`:

```ts
    // Проценты: клиент показывает critChance/dodge как «%»; в бой
    // battle.service переводит dodge в долю (/100), critChance — как есть.
    const critChance = totalAgility * 0.15 + bonus.critChance;
    const dodge = bonus.dodge;
```

- Новый метод сразу после `getActiveCharacterId`:

```ts
  /**
   * Level and class code of the active character — what `InventoryService.equip`
   * checks `Item.requiredLevel` / `Item.allowedClassCodes` against.
   */
  async getActiveCharacterBrief(
    userId: string,
  ): Promise<{ id: string; level: number; classCode: string }> {
    const character = await this.prisma.character.findFirst({
      where: { userId, isActive: true },
      select: { id: true, level: true, class: { select: { code: true } } },
    });

    if (!character) {
      throw new NotFoundException('Active character not found');
    }

    return {
      id: character.id,
      level: character.level,
      classCode: character.class.code,
    };
  }
```

### game-core — inventory

`apps/game-core/src/app/inventory/inventory.service.ts`, `equip` (транзакция и `return this.getInventory(userId)` — без изменений):

```ts
  async equip(userId: string, itemId: string) {
    const character = await this.characterService.getActiveCharacterBrief(userId);
    const characterId = character.id;
    const entry = await this.prisma.characterInventory.findFirst({
      where: { characterId, itemId },
      include: { item: true },
    });

    if (!entry) {
      throw new NotFoundException('Item is not in inventory');
    }

    if (!entry.item.slot) {
      throw new BadRequestException('Item is not equippable');
    }

    if (character.level < entry.item.requiredLevel) {
      throw new BadRequestException('LEVEL_TOO_LOW');
    }

    // Пустой список — предмет для всех классов (roadmap/items §2.1).
    const allowed = entry.item.allowedClassCodes;
    if (allowed.length > 0 && !allowed.includes(character.classCode)) {
      throw new BadRequestException('CLASS_NOT_ALLOWED');
    }

    await this.prisma.$transaction(async (tx) => { /* как было */ });
    return this.getInventory(userId);
  }
```

### game-core — battle

`apps/game-core/src/app/battle/battle.service.ts`:

- `finalize`, `character.findUnique` → `class: { select: { resourceType: true, code: true } }`; вызов лута → `this.generateLoot(monsterId, monster.nothingWeight, packSize, character.class.code)`.
- `buildPlayerCombatant`: `dodge: stats.dodge / 100,` с комментарием `// computedStats.dodge — проценты (клиент показывает «%»), resolveHit ждёт долю 0–1`.
- `generateLoot` — сигнатура и начало (остальное тело как было, только переменная `dropTable` теперь — отфильтрованный список):

```ts
  /**
   * One roll of the drop table per mob of the pack ([rolls]), merged into a
   * single list — the result screen shows «Зелье ×2», not the same item twice.
   * Personal loot (WoW): rows whose item the character's class can never equip
   * are dropped before weighing; `nothingWeight` stays — only the mix changes.
   */
  private async generateLoot(
    monsterId: string,
    nothingWeight: number,
    rolls: number,
    classCode: string,
  ): Promise<InventoryAddItemEntry[]> {
    const rows = await this.prisma.dropTable.findMany({
      where: { monsterId },
      include: { item: { select: { allowedClassCodes: true } } },
    });
    const dropTable = rows.filter(
      (row) =>
        row.item.allowedClassCodes.length === 0 ||
        row.item.allowedClassCodes.includes(classCode),
    );
    if (dropTable.length === 0) {
      return [];
    }
    // … дальше без изменений (totalWeight, циклы по rolls, quantities)
```

### api-gateway — Swagger DTO

`dto/response/inventory-response.dto.ts` → `InventoryItemDto` и `dto/response/character-response.dto.ts` → `EquippedItemDto`, после `magicDmgBonus` (одинаково в обоих):

```ts
  @ApiProperty({ minimum: 1, description: 'Уровень предмета' })
  itemLevel!: number;

  @ApiProperty({ minimum: 1, description: 'Минимальный уровень персонажа; ниже — 400 LEVEL_TOO_LOW' })
  requiredLevel!: number;

  @ApiProperty({ type: [String], description: 'CharacterClass.code; пусто — всем классам' })
  allowedClassCodes!: string[];

  @ApiProperty({ description: '% к critChance' })
  critChanceBonus!: number;

  @ApiProperty({ description: '% к dodge' })
  dodgeBonus!: number;
```

`CharacterComputedStatsDto`: `critChance` → `@ApiProperty({ description: 'Проценты: AGI × 0.15 + Σ critChanceBonus надетого' })`, `dodge` → `@ApiProperty({ description: 'Проценты: Σ dodgeBonus надетого (в бою — доля /100)' })`.

`dto/admin/item.dto.ts` → `AdminItemResponseDto`: те же пять полей, что выше. `AdminItemCreateDto` (добавить `IsArray`, `IsNumber`, `Max`, `Min` в импорт `class-validator`), после `magicDmgBonus`:

```ts
  @ApiPropertyOptional({ default: 1, minimum: 1 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  itemLevel?: number;

  @ApiPropertyOptional({ default: 1, minimum: 1 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  requiredLevel?: number;

  @ApiPropertyOptional({ type: [String], default: [], description: 'CharacterClass.code; пусто — всем' })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  allowedClassCodes?: string[];

  @ApiPropertyOptional({ default: 0, minimum: 0, maximum: 100, description: '%' })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  @Max(100)
  critChanceBonus?: number;

  @ApiPropertyOptional({ default: 0, minimum: 0, maximum: 100, description: '%' })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  @Max(100)
  dodgeBonus?: number;
```

`AdminItemUpdateDto` наследует через `PartialType` — не трогать.

`apps/api-gateway/src/app/admin/admin-items.controller.ts`, `create()`, в объект `payload` после `magicDmgBonus: dto.magicDmgBonus,`:

```ts
      itemLevel: dto.itemLevel,
      requiredLevel: dto.requiredLevel,
      allowedClassCodes: dto.allowedClassCodes,
      critChanceBonus: dto.critChanceBonus,
      dodgeBonus: dto.dodgeBonus,
      description: dto.description,
```

(`description` там сейчас потерян — баг SCRUM-15, чинится этой строкой.)

### Seed (`prisma/seed.ts`, `itemsData`)

| Предмет | itemLevel | requiredLevel | allowedClassCodes | dodgeBonus | Откуда |
|---|---|---|---|---|---|
| Iron Sword | 3 | 3 | `[]` | 0 | стоимость 6 = budget(3) × 1.0 |
| Leather Armor | 1 | 1 | `[]` | 0 | 3.5 ≤ budget(1) × 1.0 = 4 |
| Knight Shield | 2 | 2 | `['warrior']` | 0 | 5 ≤ budget(2) × 1.2 = 6 |
| Swift Boots | 3 | 3 | `[]` | 2 | 3.5 + 2 % × 2 = 7.5 ≤ budget(3) × 1.45 = 8.7 |
| Health Potion | 1 | 1 | `[]` | 0 | — |

`critChanceBonus` у всех 0 (не писать). Поля ставить сразу после `rarity`.

### Тесты

`apps/game-core/src/app/admin/item-admin.service.spec.ts`:

| it | что |
|---|---|
| `maps weapon create payload to Prisma item.create with defaults` (существующий) | в ожидаемом `data` добавить `itemLevel: 1, requiredLevel: 1, allowedClassCodes: [], critChanceBonus: 0, dodgeBonus: 0` |
| `create stores progression fields and class codes` (новый) | payload с `itemLevel: 4, requiredLevel: 3, allowedClassCodes: ['mage'], critChanceBonus: 1.5, dodgeBonus: 2` → `data: expect.objectContaining({...те же})` |

`apps/game-core/src/app/character/character.service.spec.ts` — хелпер рядом с `activeCharacterRow`:

```ts
const itemRow = (overrides: Record<string, unknown> = {}) => ({
  strBonus: 0, intBonus: 0, staBonus: 0, agiBonus: 0, spiBonus: 0,
  armorBonus: 0, magicResistBonus: 0, physDmgBonus: 0, magicDmgBonus: 0,
  critChanceBonus: 0, dodgeBonus: 0,
  ...overrides,
});
```

| it | входные | ожидание |
|---|---|---|
| `computeStats adds crit and dodge from equipped items` | `activeCharacterRow({ inventory: [{ item: itemRow({ critChanceBonus: 2.5, dodgeBonus: 4 }) }, { item: itemRow({ dodgeBonus: 1 }) }] })`, agility 3 | `critChance` `toBeCloseTo(2.95)`, `dodge` `toBe(5)` |
| `computeStats keeps dodge at 0 without equipment` | `activeCharacterRow()` | `dodge` 0, `critChance` `toBeCloseTo(0.45)` |
| `getActiveCharacterBrief returns id, level and class code` | `prisma.character.findFirst → { id: 'char-1', level: 4, class: { code: 'mage' } }` | `{ id: 'char-1', level: 4, classCode: 'mage' }`; `findFirst` вызван с `where: { userId: 'user-1', isActive: true }` |
| `getActiveCharacterBrief throws NotFoundException without an active character` | `findFirst → null` | `rejects.toBeInstanceOf(NotFoundException)` |

`apps/game-core/src/app/inventory/inventory.service.spec.ts` — в `createService` рядом с `getActiveCharacterId` добавить `getActiveCharacterBrief: jest.fn()`; хелпер `const brief = (overrides = {}) => ({ id: 'char-1', level: 1, classCode: 'warrior', ...overrides })`. Два существующих кейса equip: `characterService.getActiveCharacterBrief.mockResolvedValue(brief())`, у `item` в фикстуре добавить `requiredLevel: 1, allowedClassCodes: []`.

| it | входные | ожидание |
|---|---|---|
| `rejects equip below the required level with LEVEL_TOO_LOW` | `brief({ level: 2 })`, item `{ slot: 'WEAPON', requiredLevel: 5, allowedClassCodes: [] }` | `rejects.toThrow('LEVEL_TOO_LOW')`, `$transaction` не вызван |
| `rejects equip for a class outside allowedClassCodes with CLASS_NOT_ALLOWED` | `brief({ classCode: 'mage' })`, item `{ slot: 'SHIELD', requiredLevel: 1, allowedClassCodes: ['warrior'] }` | `rejects.toThrow('CLASS_NOT_ALLOWED')`, `$transaction` не вызван |
| `equips when allowedClassCodes contains the class` | `brief()`, item `allowedClassCodes: ['warrior']`, `findMany → []` | resolves, `tx.characterInventory.update` вызван |

`apps/game-core/src/app/battle/battle.service.spec.ts`:

- `PrivateAccess`: `generateLoot(monsterId: string, nothingWeight: number, rolls: number, classCode: string)`; добавить `buildPlayerCombatant(character: unknown, classSkills: unknown[]): { dodge: number; critChance: number }`.
- Во всех фикстурах `prisma.character.findUnique.mockResolvedValue({... class: { resourceType: 'RAGE' } })` → `class: { resourceType: 'RAGE', code: 'warrior' }` (`finalize`-тесты и `victoryWithPack`).
- Во всех фикстурах `prisma.dropTable.findMany.mockResolvedValue([...])` каждой строке добавить `item: { allowedClassCodes: [] }`.
- Три прямых вызова `generateLoot('monster-1', 0)` / `(…, 9)` / `(…, 90)` → четыре аргумента: `(…, 0, 1, 'warrior')`, `(…, 9, 1, 'warrior')`, `(…, 90, 1, 'warrior')`.
- Ассерт `expect(prisma.dropTable.findMany).toHaveBeenCalledWith({ where: { monsterId: 'monster-1' } })` → `expect.objectContaining({ where: { monsterId: 'monster-1' } })`.

| it | входные | ожидание |
|---|---|---|
| `buildPlayerCombatant converts profile dodge from percent to the engine fraction` | `character = { resourceType: 'RAGE', computedStats: { maxHp: 100, maxMana: 0, physAtk: 10, magicAtk: 0, armor: 0, magicResist: 0, attackSpeed: 0.8, critChance: 1, dodge: 5, ragePerAuto: 5, manaRegen: 0, totalAttributes: { strength: 8, intelligence: 2, stamina: 6, agility: 3, spirit: 3 } } }`, `buildPlayerCombatant(character, [])` | `dodge` `toBeCloseTo(0.05)`, `critChance` `toBe(1)` |
| `personal loot: a mage never rolls warrior-only rows` | rows `[{ itemId: 'shield', weight: 9, minQty: 1, maxQty: 1, item: { allowedClassCodes: ['warrior'] } }, { itemId: 'wand', weight: 1, minQty: 1, maxQty: 1, item: { allowedClassCodes: [] } }]`, `Math.random` → `0.5`, затем `0`; `generateLoot('monster-1', 0, 1, 'mage')` | `[{ itemId: 'wand', quantity: 1 }]` (без фильтра 0.5 × 10 = 5 упало бы в щит) |
| `personal loot keeps the nothing bucket at the same weight` | те же rows, `nothingWeight` 1, `Math.random` → `0.75`; `generateLoot('monster-1', 1, 1, 'mage')` | `[]` (total = 1 + 1, ролл 1.5 уходит в «ничего») |
| `personal loot: a warrior still rolls the shield` | те же rows, `nothingWeight` 1, `Math.random` → `0.5`, затем `0`; `generateLoot('monster-1', 1, 1, 'warrior')` | `[{ itemId: 'shield', quantity: 1 }]` (total = 11, ролл 5.5 попадает в щит) |

### Доки — тексты

`troy-docs/technical/database-schema.md`, таблица `Item`, после `magicDmgBonus`:

```
| **Прогрессия и ограничения** | | |
| itemLevel | Int, default 1 | Уровень предмета — бюджет статов (roadmap/items §3), «▲ апгрейд» на клиенте |
| requiredLevel | Int, default 1 | Минимальный уровень персонажа; ниже — equip отвечает 400 `LEVEL_TOO_LOW` |
| allowedClassCodes | String[], default [] | `CharacterClass.code`; пусто — всем. Чужой класс: equip 400 `CLASS_NOT_ALLOWED`, в личный лут не попадает |
| critChanceBonus | Float, default 0 | +% к critChance |
| dodgeBonus | Float, default 0 | +% к dodge |
```

Блок производных: `critChance   = base_crit + total_agi * 0.15 + equipment_crit   // %`, `dodge        = equipment_dodge   // %, в бою /100`. Строка `Monster.dodge`: «Уклонение, доля 0–1 (0.05 = 5 %)».

`troy/CLAUDE.md`, Key design decisions, пункт 12:

```
12. **Item progression is on the `Item` row** — `itemLevel`/`requiredLevel` (equip → 400 `LEVEL_TOO_LOW`),
    `allowedClassCodes` (empty = everyone; equip → 400 `CLASS_NOT_ALLOWED`, and `generateLoot` drops such
    rows before weighing — personal loot, `nothingWeight` untouched), `critChanceBonus`/`dodgeBonus` in
    percent summed into `computedStats`. The engine's `dodge` is a fraction: `buildPlayerCombatant`
    divides by 100, `Monster.dodge` is stored as a fraction already. See `troy-docs/roadmap/items/`.
```

### Запреты

- Prisma — только `npm run prisma:migrate` (deploy) + `npm run prisma:generate`. **Никогда** `migrate dev`.
- Дев-процессы (`start:*`, docker) не запускать — только `nx test` / `nx build`; живую проверку делает пользователь.
- Без подписей ассистента в коммитах; ключ задачи — в сообщении; сообщения — как в решении 9, по-русски.
- Чужие незакоммиченные файлы не трогать. `troy-admin` и `troy-flutter` в этой связке не трогать (SCRUM-63/64 — отдельные задачи).
- Не переименовывать Swagger-классы, не менять сигнатуры существующих эндпоинтов.
- `hpRestore`/`resourceRestore`, зелья, лимит мешка — не здесь.

## Промт

### Сессия 1 — SCRUM-62 + SCRUM-17 (troy-backend) · Sonnet · acceptEdits

Код, миграция и тесты даны дословно; решений по ходу не остаётся. Годится и делегату (GLM/codex) с ревью Opus — без строк про Jira и `/troy-continue`.

```
Работаем в /Users/fost/Projects/troy (troy-backend).

Задачи: SCRUM-62 — Item progression: itemLevel, requiredLevel, crit/dodge на шмоте —
миграция, equip, статы; SCRUM-17 — Class restrictions: allowedClassCodes, проверка в
equip, личный лут по классу. Инвентарь, equip/unequip, computed stats, лут и админка
предметов уже работают — это доработка одной миграцией, не стройка.

Начни с `bash ~/.claude/skills/troy-jira/jira.sh view SCRUM-62` и `... view SCRUM-17`,
переведи обе в «В работе» (`bash ~/.claude/skills/troy-jira/jira.sh transition SCRUM-62 "В работе"`,
то же для SCRUM-17). Токен: `export $(grep -oE 'JIRA_CLOUD_[A-Z]+=[^ ]+' ~/.zshrc | tr -d '"'"'" | xargs)`.

План — troy-docs/roadmap/items/item-progression.md: этапы 1–4, чекбоксы, раздел
«Контракт и точки входа» с готовым кодом, SQL миграции, таблицей seed и таблицами
тестов. Иди строго по нему, галочки ставь по факту проверки.

Прочитай ещё:
- troy-docs/roadmap/items/README.md (§1–2.2 и §3 — откуда числа seed);
- troy-docs/technical/database-schema.md (таблица Item, блок производных статов);
- troy/CLAUDE.md (Testing, Key design decisions);
- эталоны: apps/game-core/src/app/inventory/inventory.service.spec.ts,
  apps/game-core/src/app/battle/battle.service.spec.ts (PrivateAccess, фикстуры),
  libs/shared/prisma/migrations/0019_item_description/migration.sql.

Уже решено (05.09, не переспрашивать): миграция 0020_item_progression — только пять
полей (hpRestore/resourceRestore — с зельями, SCRUM-19); коды ошибок equip —
LEVEL_TOO_LOW и CLASS_NOT_ALLOWED, проверки до транзакции в порядке 404 → нет слота →
уровень → класс; critChance/dodge в computedStats — проценты, в buildPlayerCombatant
dodge делится на 100 (движок ждёт долю); новый CharacterService.getActiveCharacterBrief
→ { id, level, classCode }, только для equip; личный лут — фильтр строк DropTable в
памяти после include item.allowedClassCodes, nothingWeight не меняется, сигнатура
generateLoot(monsterId, nothingWeight, rolls, classCode); seed — таблица в «Контракте»
(Knight Shield → ['warrior'], Swift Boots dodgeBonus 2); в admin-items.controller create()
попутно пробросить потерянный description.

Порядок:
1. Этап 1 — schema.prisma, миграция 0020 (`npm run prisma:migrate`, `npm run prisma:generate`),
   контракты, ITEM_SELECT/toCreateData, Swagger DTO (inventory/character/admin),
   admin-items.controller, seed, тест item-admin.
2. Этап 2 — character.service (select, EquipmentBonuses, computeStats, getActiveCharacterBrief),
   inventory.service equip LEVEL_TOO_LOW, battle.service dodge/100, тесты; коммит SCRUM-62.
3. Этап 3 — equip CLASS_NOT_ALLOWED, finalize class.code, generateLoot с фильтром,
   правка фикстур battle.service.spec и новые тесты; коммит SCRUM-17.
4. Этап 4 — database-schema.md, items/README.md, roadmap/README.md, troy-backend/README.md,
   troy/CLAUDE.md, баннер и галочки в item-progression.md.

DoD: unit — equip отказывает по уровню и классу; computed stats считают crit/dodge от
шмота; roll лута при фиксированном RNG не выдаёт чужой шмот; `npx nx run-many -t test`
и `npx nx run-many -t build` зелёные в troy-backend. Поля видны в Swagger-DTO
GET /inventory и GET /character/me. database-schema.md обновлён.

Ветка main, коммиты без подписей ассистента, ключ задачи в сообщении, по-русски, в
стиле истории репо — например:
`items: itemLevel/requiredLevel, crit/dodge от шмота, проверка уровня в equip (SCRUM-62)`.
Prisma — только `migrate deploy` (`npm run prisma:migrate`), НИКОГДА `migrate dev`.
Дев-процессы не запускать. Чужие незакоммиченные файлы не трогать. troy-admin и
troy-flutter не трогать.

По завершении: /troy-continue.
```
