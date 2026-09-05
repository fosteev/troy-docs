# MVP-3 — гэпы бэкенда: описание предмета, выброс, отклик на статы

> **Статус: обе сессии сделаны; сессия 2 (Flutter, SCRUM-75/49) принята ревью 06.09 с правками, проверена пользователем на устройстве и закоммичена** (два коммита — решение 9). Сессия 1 (backend + admin, SCRUM-15/16) — 05.09, ревью без расхождений (решение 8), закрыта пользователем. SCRUM-75/49 — «Готово» (06.09): описание в карточке до ревью не маппилось (исполнитель пропустил чекбокс), починено ревью, проверено на устройстве. Модель сессии 2 — Sonnet, acceptEdits; ревью Opus сделано этим `/troy-plan-review`.

Родитель: [README фазы](./README.md) · аудит: [backend-gaps.md](./backend-gaps.md) (#1, #3, #7) · UX-решения: [redesign.md](./redesign.md).

## Зачем

Последнее, что держит MVP-3 открытым по бэкенду: у предмета нет описания (карточка на клиенте уже умеет его показывать), от предмета нельзя избавиться (мешок растёт бесконечно), а после equip клиент молча получает новый снапшот. Плюс найденный при разборе дефект: `/character/me` отдаёт только надетое, так что мешок на реальном клиенте пуст.

## Что нашли при разборе (05.09)

- **`/character/me` отдаёт только надетое.** `ACTIVE_CHARACTER_SELECT.inventory.where = { isEquipped: true }` (`character.service.ts`, строка ~56, так с первого коммита). Клиент собирает и куклу, и мешок только из `/character/me` (`HeroRemoteDataSource.getMe`; `GET /inventory` не вызывается нигде). Итог: на реальном API мешок пустой. Чиним в этой связке (решение 3).
- В описании SCRUM-15 написано «там уже `include: { item: true }`» — неверно: там `select`-whitelist, поле само не подтянется.
- Flutter ходит в бэкенд через **сгенерированный** пакет `packages/troy_backend_api` (openapi-generator, dart-dio, спека с `GET /api-json` работающего gateway). Новые поля и эндпоинт попадают в него только через `./tools/generate_openapi.sh` (docker) — это делает пользователь между сессиями; сессия 2 без этого не стартует.
- Стак (SCRUM-18) — решение уже есть (items/README §2.4), клиент уже рисует «×N» в шапке карточки. Кода нет.

## Решения (05.09)

1. **Discard.** `DELETE /inventory/:itemId?quantity=N`, `N ≥ 1`, по умолчанию 1.
   - `N > quantity` → 400 `Not enough items to discard`.
   - `N == quantity` и `isEquipped` → 400 `Unequip the item first` (надетую копию не выбрасываем).
   - `N < quantity` → декремент, даже если стак надет (остаётся ≥ 1 копия, она и считается надетой).
   - `N == quantity` и не надет → строка удаляется.
   - Ответ — полный инвентарь, как у equip/unequip (`InventoryEntryResponseDto[]`), HTTP 200.
   - Продажа за золото — не здесь ([vendors/](../vendors/README.md)).
2. **Миграция `0019_item_description` — отдельная.** В items/README было «description едет в `item_progression`» — отменено: MVP-3 закрывается независимо от items; SCRUM-62 берёт следующий свободный номер (0020).
3. **`/character/me.inventory` — все строки**, надетые и мешок, `isEquipped` различает. В `getMe` — отдельный `characterInventory.findMany` с `include: { item: true }`; `ACTIVE_CHARACTER_SELECT` (горячие пути, `computeStats`) не трогаем. Swagger-классы `EquippedInventoryEntryDto` / `EquippedItemDto` **не переименовывать** — имена уезжают в Dart-клиент и маппер.
4. **Description.** `String?`, до 500 символов. Админка — `Input.TextArea`, пустая строка → `null`. Seed — RU-тексты (ниже), в стиле описаний мобов.
5. **Flutter discard UX.** Кнопка DISCARD (`AppButtonVariant.outline`) под EQUIP в inspect sheet, для расходников — единственная кнопка. `quantity == 1` → `AlertDialog` подтверждения (Cancel / Discard); `quantity > 1` → диалог с действиями «Discard 1» / «Discard all (×N)». Успех → sheet закрыт, снапшот обновлён. Надетые в мешке не показываются, поэтому 400 «Unequip first» — страховка бэкенда, отдельного UI не надо: ошибка идёт в `errorMessage`-снекбар как у equip.
6. **SCRUM-49 — тост с дифом производных статов** после equip/unequip: сравниваем `profile.derived` старого и нового снапшота (maxHp, maxResource, armor, mResist, physAtk, magicAtk, atkSpeed, critPct), строка вида `PHYS ATK +7 · ARMOR −2` из ключей `hero.derived.*`; без изменений — тоста нет. Хранится в `HeroLoaded.statDeltas` (список, пустой = нечего показывать) по аналогии с `errorMessage`; страница показывает `context.showInfoSnackBar(...)` и вызывает `clearStatDeltas()`. Форматирование (`.tr()`) — в странице, чистая функция диффа без локализации (тестируется без EasyLocalization).
7. **Дельта в карточке** (вторая половина SCRUM-49): бонусы в sheet — строками `label | +value | Δ против надетого в этот слот` (▲ зелёный / ▼ красный / — muted), над таблицей строка «VS. EQUIPPED <имя>», когда в слоте что-то есть; пустой слот или расходник — колонка Δ не рисуется. Кнопка UNEQUIP в sheet — не здесь (redesign).

8. **Ревью сессии 1 (05.09):** принято без расхождений с планом; исполнитель решений по ходу не принимал — план зазора не оставил. Правка ревью: `InventoryService.discard` отвергает `quantity`, если оно не целое или < 1, **до** чтения инвентаря. Gateway и так валидирует `@Min(1)`, но NATS-паттерн `inventory.discard` доступен изнутри game-core, а `decrement` на отрицательное число увеличил бы стак. Осознанный долг: discard (как и equip) не атомарен — `findFirst` → `update`/`delete` без условия по `quantity`; два одновременных discard одного стака дадут строку с `quantity 0` или 500 на втором delete. Клиент сериализует мутации (`_mutationInFlight`), в MVP не чиним; если понадобится — `updateMany({ where: { id, quantity: { gte: N } } })` / `deleteMany({ where: { id, quantity: N, isEquipped: false } })` с проверкой `count`. Записано в Known issues `troy/CLAUDE.md`. Коммиты исполнителя были на английском не в стиле истории репо — переамендены (не запушены); в промты сессий добавлять пример сообщения дословно.

9. **Ревью сессии 2 (06.09, `/troy-plan-review`).** Исполнитель (Sonnet) сделал этапы 4–5 по контракту, но **не прогнал `/troy-continue`**: ни коммитов, ни галочек, ни комментов в Jira; при этом SCRUM-15/16/49/75 оказались в «Готово» (кем — по комментам не видно; SCRUM-75/49 возвращены в «В процессе проверки»). Пропущено молча: `description` в `hero_mapper.dart` — карточка описание не показывала вовсе, хотя это половина SCRUM-75; тесты `hero_mapper_test.dart` (description) и `hero_repository_impl_test.dart` (discard). Всё три добавлены ревью, `flutter analyze` чисто, 241 тест зелёный. Решения исполнителя, принятые ревью: (а) в кубите ошибка мутации эмитится поверх **текущего** стейта (`_emitFailure`), а не захваченного до `await` — страница вызывает `discard`/`equip` без `await` и тут же закрывает sheet (`clearInspect`), поэтому ошибка на захваченном стейте воскрешала бы `selectedItemId`; применено ко всем четырём мутациям, покрыто тестом «clearInspect во время discard не откатывается ошибкой». Успешный путь по-прежнему на захваченном `s` — как было до сессии, не трогали; (б) в тосте `atkSpeed`/`critPct` печатаются с одним знаком после запятой (IEEE-754 даёт `0.1499…` на разности double), остальные — как есть; (в) ▼ в дельте — `context.colors.error`, в токенах нет `error`. Побочное от перегенерации клиента: в `ClassSkillListItemDto` появились `INTERRUPT` и обязательный `channelTicks` — исполнитель добавил ветку в `class_mapper.dart` и `channelTicks: 0` в двух тестах классов; это едет в коммит `chore(api)`, не в фичу. Флак: `test/shared/widgets/sprite_sheet_animator_test.dart` («phase offsets a looping sheet…») раз упал в полном прогоне, 3/3 зелёный в изоляции — таймингозависимый, к связке не относится, при повторе — открыть отдельно. **Коммиты (06.09, после «ок» пользователя)**, два, в `troy-flutter`: `chore(api): реген клиента — description и DELETE /inventory, INTERRUPT/channelTicks в классах` (пакет + `class_mapper.dart` + два теста классов) и `feat(hero): описание и Discard в карточке, тост с дифом статов и дельты против надетого (SCRUM-75, SCRUM-49)` (остальное). Проверить на устройстве: описание под названием в карточке предмета из мешка; DISCARD под EQUIP (у зелья — единственная кнопка), диалог «Выбросить N?» с «Отмена / Выбросить» при ×1 и «Выбросить 1 / Выбросить все (×N)» при стаке, после — sheet закрыт, мешок обновлён; надеть предмет — снекбар вида «PHYS ATK +7 · ARMOR −2», без изменений статов — снекбара нет; в карточке предмета при занятом слоте — строка «ПРОТИВ НАДЕТОГО <имя>» и ▲/▼/— у каждого бонуса.
## Этапы

### Сессия 1 · Этап 1 — SCRUM-15, backend: description

- [x] `libs/shared/prisma/schema.prisma`: `description String?` в `model Item` (после `magicDmgBonus`, перед `iconUrl`).
- [x] Миграция `libs/shared/prisma/migrations/0019_item_description/migration.sql` (текст в «Контракте»); накат `npm run prisma:migrate` (deploy), затем `npm run prisma:generate`.
- [x] `character.service.ts` → `getMe`: инвентарь полным списком отдельным запросом (решение 3); `ACTIVE_CHARACTER_SELECT` не менять.
- [x] `admin/item-admin.service.ts`: `description: true` в `ITEM_SELECT`, `description: payload.description ?? null` в `toCreateData`.
- [x] Контракты: `AdminItemDto.description`, `AdminItemCreatePayload.description?`.
- [x] Swagger: `InventoryItemDto.description`, `EquippedItemDto.description`, `AdminItemResponseDto.description`, `AdminItemCreateDto.description` (+ валидация); описание поля `CharacterProfileResponseDto.inventory` — «все строки инвентаря, надетые — `isEquipped: true`».
- [x] `prisma/seed.ts`: `description` у 5 предметов (тексты в «Контракте»).
- [x] Тесты: `character.service.spec.ts` — `getMe returns the full inventory from a separate query`; `item-admin.service.spec.ts` — `create stores description and defaults it to null`.
- [x] Доки: строка `description` в таблице Item в `troy-docs/technical/database-schema.md`.

Готово, когда: `npm run prisma:migrate` применил 0019, `npx nx run-many -t test` зелёный, `npx nx run-many -t build` собирается. **Сделано** (05.09).

### Сессия 1 · Этап 2 — SCRUM-16, backend: discard

- [x] Контракты: `NATS_PATTERNS.INVENTORY_DISCARD`, `InventoryDiscardRequest`.
- [x] `inventory.service.ts`: `discard(userId, itemId, quantity)` по решению 1.
- [x] `inventory.controller.ts` (game-core): `@MessagePattern(NATS_PATTERNS.INVENTORY_DISCARD)`.
- [x] `apps/api-gateway/src/app/dto/inventory.dto.ts` (новый): `InventoryDiscardQueryDto`.
- [x] `apps/api-gateway/src/app/inventory/inventory.controller.ts`: `@Delete(':itemId')`.
- [x] Тесты `inventory.service.spec.ts` — 6 кейсов из «Контракта».
- [x] `troy-backend/README.md`: строка `DELETE /inventory/:itemId?quantity=` в таблицу эндпоинтов.

Готово, когда: `npx nx run-many -t test` зелёный; в Swagger (`/api`) виден `DELETE /inventory/{itemId}` с query `quantity`. **Сделано** (05.09).

### Сессия 1 · Этап 3 — SCRUM-15, admin: поле «Описание»

- [x] `troy-admin/src/api/items.ts`: `description: string | null` в `Item`.
- [x] `troy-admin/src/pages/items/ItemFormModal.tsx`: `Form.Item name="description" label="Описание"` с `Input.TextArea rows={3} maxLength={500} showCount` сразу после «Название»; `defaultValues.description: null`; в `normalizeInput` — `trim()`, пустое → `null`.

Готово, когда: `npx tsc -b --noEmit` и `npm run lint` в `troy-admin` чистые. **Сделано** (05.09).

### Между сессиями — пользователь

- [x] **Сделано пользователем 05–06.09** (клиент перегенерирован, обе проверки ниже проходят; пакет ещё не закоммичен — коммит `chore(api)` вместе с сессией 2, решение 9). **Перезапустить** gateway (ревью 05.09: процесс на :3000 отдавал Swagger без `DELETE /inventory/{itemId}` — старая сборка; клиент, снятый с него, будет без `inventoryControllerDiscard`) и перегенерировать клиент: `./tools/generate_openapi.sh` в `troy-flutter` (нужен docker). Проверка: `grep -c inventoryControllerDiscard packages/troy_backend_api/lib/src/api/inventory_api.dart` ≥ 1 и `grep -c description packages/troy_backend_api/lib/src/model/equipped_item_dto.dart` ≥ 1. Закоммитить пакет отдельным коммитом (`chore(api): regenerate client — item description, DELETE /inventory`).

### Сессия 2 · Этап 4 — SCRUM-75 (клиент SCRUM-15/16), Flutter: description и discard

- [x] Предусловие: обе проверки из блока выше проходят. Иначе — стоп и попросить пользователя перегенерировать клиент.
- [x] `hero_mapper.dart`: `description: item.description as String?` в `_EquippedEntryMapper.toDomain()` — **пропущено исполнителем, добавлено ревью 06.09** (DTO несёт поле как `Object?`).
- [x] `hero_repository.dart` + `hero_repository_impl.dart` + `hero_remote_datasource.dart`: `discard(itemId, {quantity})` по образцу `equip`.
- [x] `hero_cubit.dart`: `discard(itemId, {quantity})` по образцу `equip` (`_mutationInFlight`, сброс `selectedItemId`).
- [x] `item_inspect_sheet.dart`: параметр `onDiscard: ValueChanged<int>`, кнопка DISCARD, диалог по решению 5.
- [x] `hero_page.dart`: пробросить `onDiscard` в `showItemInspectSheet`.
- [x] Переводы `assets/translations/en.json` + `ru.json`: ключи из «Контракта».
- [x] Тесты: `hero_mapper_test.dart` (description) и `hero_repository_impl_test.dart` (discard: успех, 400) — **не написаны исполнителем, добавлены ревью 06.09**; `hero_cubit_test.dart` (группа `discard`: успех / ошибка / double-tap + гонка с `clearInspect`) — исполнитель.

Готово, когда: `flutter analyze` чисто, `flutter test` зелёный.

### Сессия 2 · Этап 5 — SCRUM-49, Flutter: отклик на смену статов

- [x] `lib/features/profile/domain/entities/stat_delta.dart` (freezed, `.freezed.dart` сгенерирован) + `lib/features/profile/domain/usecases/derived_stats_diff.dart`: чистая функция `List<StatDelta> derivedStatsDiff(DerivedStats before, DerivedStats after)`.
- [x] `hero_state.dart`: `statDeltas: List<StatDelta>` (по умолчанию `const []`), `copyWith`, `clearStatDeltas`.
- [x] `hero_cubit.dart`: после успешных `equip`/`unequip` — `statDeltas: derivedStatsDiff(old.profile.derived, new.profile.derived)`; `allocate` и `discard` — не трогают (пустой список).
- [x] `context_extensions.dart`: `showInfoSnackBar(String message)` рядом с `showErrorSnackBar`.
- [x] `hero_page.dart` listener: `statDeltas.isNotEmpty` → `showInfoSnackBar(format(...))` → `cubit.clearStatDeltas()`.
- [x] `item_inspect_sheet.dart`: параметр `equippedInSlot: InventoryItem?`, бонусы строками с дельтой (решение 7); `hero_page.dart` передаёт `loaded.snapshot.equippedIn(item.slot!)` при `slot != null`.
- [x] Тесты: `test/features/profile/domain/usecases/derived_stats_diff_test.dart` (таблица кейсов: нет изменений → пусто; рост/падение; порядок полей стабилен), `hero_cubit_test.dart` (equip меняет `physAtk` → `statDeltas` непустой; повторный `clearStatDeltas` → пустой), `hero_page_smoke_test.dart` остаётся зелёным.
- [x] Доки (ревью 06.09): галочка «визуальная обратная связь после изменения статов» в [README фазы](./README.md), баннер фазы и таблица в [roadmap/README.md](../README.md) (`/troy-continue`).

Готово, когда: `flutter analyze` чисто, `flutter test` зелёный.

## Контракт и точки входа

### Backend — миграция и схема

`libs/shared/prisma/migrations/0019_item_description/migration.sql`:

```sql
-- Описание предмета для карточки на клиенте (roadmap/mvp-3-inventory, SCRUM-15).
ALTER TABLE "Item" ADD COLUMN "description" TEXT;
```

`schema.prisma`, `model Item`: `description String?` — между `magicDmgBonus` и `iconUrl`. Накат **только** `npm run prisma:migrate` (deploy); `migrate dev` дропает `active_spawns` и `SpawnZone.geometry`.

### Backend — контракты (`libs/shared/contracts/src/lib/contracts.ts`)

```ts
// NATS_PATTERNS, после INVENTORY_ADD_ITEMS
INVENTORY_DISCARD: 'inventory.discard',

// после InventoryUnequipRequest
export interface InventoryDiscardRequest {
  userId: string;
  itemId: string;
  /** Сколько копий выбросить, >= 1. Равно quantity строки — строка удаляется. */
  quantity: number;
}

// AdminItemDto: description: string | null;  (после magicDmgBonus)
// AdminItemCreatePayload: description?: string | null;
```

### Backend — game-core

`apps/game-core/src/app/inventory/inventory.service.ts`:

```ts
async discard(userId: string, itemId: string, quantity: number) {
  const characterId = await this.characterService.getActiveCharacterId(userId);
  const entry = await this.prisma.characterInventory.findFirst({
    where: { characterId, itemId },
  });
  if (!entry) throw new NotFoundException('Item is not in inventory');
  if (quantity > entry.quantity) throw new BadRequestException('Not enough items to discard');

  if (quantity === entry.quantity) {
    if (entry.isEquipped) throw new BadRequestException('Unequip the item first');
    await this.prisma.characterInventory.delete({ where: { id: entry.id } });
  } else {
    await this.prisma.characterInventory.update({
      where: { id: entry.id },
      data: { quantity: { decrement: quantity } },
    });
  }
  return this.getInventory(userId);
}
```

`inventory.controller.ts` (game-core) — хендлер по образцу `unequip`:
`@MessagePattern(NATS_PATTERNS.INVENTORY_DISCARD) discard(@Payload() p: InventoryDiscardRequest) { return this.inventoryService.discard(p.userId, p.itemId, p.quantity); }`

`apps/game-core/src/app/character/character.service.ts`, `getMe`:

```ts
const character = await this.getActiveCharacter(userId);
const computedStats = this.computeStats(character); // как раньше — только надетое из ACTIVE_CHARACTER_SELECT
const inventory = await this.prisma.characterInventory.findMany({
  where: { characterId: character.id },
  include: { item: true },
  orderBy: { id: 'asc' },
});
return { ...character, inventory, class: character.class.code, resourceType: character.class.resourceType, computedStats };
```

`apps/game-core/src/app/admin/item-admin.service.ts`: `ITEM_SELECT` + `description: true`; `toCreateData` + `description: payload.description ?? null`. `update` шлёт `data` как есть — ничего не менять.

`prisma/seed.ts`, поле `description` в `itemsData`:

| Предмет | description |
|---|---|
| Iron Sword | Простой клинок из кузницы при заставе: ни гравировки, ни имени, зато точится за минуту и не подводит. Для первого похода лучше и не надо. |
| Leather Armor | Дублёная кожа с нашитыми пластинами. От стрелы не спасёт, но от когтей и зубов — вполне; главное, не стирать в кипятке. |
| Knight Shield | Тяжёлый щит с облупившимся гербом чужого ордена. Прежний владелец его уже не ищет, а вмятины держат удар не хуже новых. |
| Swift Boots | Сапоги с мягкой подошвой, прошитые по седельному шву: не скрипят, не скользят и будто сами уносят из-под удара. Носить с осторожностью — привыкаешь. |
| Health Potion | Мутный красный отвар в закупоренной склянке. Пахнет травами и жжёным сахаром, действует быстро; спрашивать о рецепте не принято. |

### Backend — api-gateway

`apps/api-gateway/src/app/dto/inventory.dto.ts` (новый, эталон — `dto/map.dto.ts`):

```ts
import { ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import { IsInt, IsOptional, Min } from 'class-validator';

export class InventoryDiscardQueryDto {
  @ApiPropertyOptional({ default: 1, minimum: 1, description: 'Сколько копий выбросить' })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  quantity?: number;
}
```

`apps/api-gateway/src/app/inventory/inventory.controller.ts` (добавить `Delete`, `Query` в импорт `@nestjs/common`):

```ts
@Delete(':itemId')
@ApiDataResponse(InventoryEntryResponseDto, { isArray: true })
discard(
  @CurrentUser() user: { sub: string },
  @Param('itemId') itemId: string,
  @Query() query: InventoryDiscardQueryDto,
) {
  return this.rpc.send(NATS_PATTERNS.INVENTORY_DISCARD, {
    userId: user.sub,
    itemId,
    quantity: query.quantity ?? 1,
  });
}
```

Ошибки 400/404 из game-core доезжают до HTTP через `NatsRpcService` — ничего добавлять не надо. Глобальный `ValidationPipe` уже `transform: true, whitelist: true`.

Swagger DTO — везде как у `iconUrl`:
- `dto/response/inventory-response.dto.ts` → `InventoryItemDto`: `@ApiProperty({ required: false, nullable: true }) description!: string | null;`
- `dto/response/character-response.dto.ts` → `EquippedItemDto`: то же; у `CharacterProfileResponseDto.inventory` — `@ApiProperty({ type: [EquippedInventoryEntryDto], description: 'Все строки инвентаря (надетые — isEquipped: true)' })`.
- `dto/admin/item.dto.ts` → `AdminItemResponseDto`: `@ApiPropertyOptional({ nullable: true }) description!: string | null;`; `AdminItemCreateDto`: `@ApiPropertyOptional({ nullable: true, maxLength: 500 }) @IsOptional() @IsString() @MaxLength(500) description?: string | null;` (`MaxLength` добавить в импорт `class-validator`). `AdminItemUpdateDto` наследует через `PartialType`.

### Backend — тесты

`apps/game-core/src/app/inventory/inventory.service.spec.ts` — в `createService` добавить моки `prisma.characterInventory.update` и `delete`; кейсы:

| it | входные | ожидание |
|---|---|---|
| `discard decrements quantity and keeps the row` | `{quantity: 3, isEquipped: false}`, discard 1 | `update({ where: { id }, data: { quantity: { decrement: 1 } } })`, `delete` не вызван, возвращает `findMany` |
| `discard deletes the row when the whole stack is thrown away` | `{quantity: 2, isEquipped: false}`, discard 2 | `delete({ where: { id } })`, `update` не вызван |
| `discard keeps the equipped copy when part of the stack goes` | `{quantity: 3, isEquipped: true}`, discard 2 | `update` с decrement 2 |
| `rejects discarding the whole stack while it is equipped` | `{quantity: 1, isEquipped: true}`, discard 1 | `BadRequestException`, ни `update`, ни `delete` |
| `rejects discarding more than owned` | `{quantity: 1}`, discard 2 | `BadRequestException` |
| `rejects discarding an item not in inventory` | `findFirst → null` | `NotFoundException` |

`apps/game-core/src/app/character/character.service.spec.ts` — `getMe returns the full inventory from a separate query`: мок `prisma.characterInventory.findMany` отдаёт две строки (одна `isEquipped: false`), `result.inventory` содержит обе; `findMany` вызван с `where: { characterId }`.

`apps/game-core/src/app/admin/item-admin.service.spec.ts` — `create stores description and defaults it to null`: с `description` в payload → в `data`; без — `description: null`. Существующие `expect.objectContaining` не ломаются.

### Admin (`troy-admin`)

- `src/api/items.ts`: `description: string | null;` в `Item` после `magicDmgBonus`.
- `src/pages/items/ItemFormModal.tsx`: `defaultValues.description: null`; после `Form.Item name="name"`:
  ```tsx
  <Form.Item name="description" label="Описание">
    <Input.TextArea rows={3} maxLength={500} showCount />
  </Form.Item>
  ```
  в `normalizeInput`: `const description = values.description?.trim(); … description: description ? description : null,`.

### Flutter (`troy-flutter`) — сессия 2

Эталон архитектуры — `lib/features/auth/**`; profile уже разложен так же. Presentation не видит DTO.

- `lib/features/profile/data/datasources/hero_remote_datasource.dart`:
  ```dart
  /// `DELETE /inventory/:itemId?quantity=`. The returned inventory array is ignored.
  Future<void> discard(String itemId, {int quantity = 1}) async {
    await _apiClient.inventory.inventoryControllerDiscard(itemId: itemId, quantity: quantity);
  }
  ```
  (точную сигнатуру сгенерированного метода посмотреть в `packages/troy_backend_api/lib/src/api/inventory_api.dart`.)
- `domain/repositories/hero_repository.dart`: `Future<Either<Failure, HeroSnapshot>> discard(String itemId, {int quantity = 1});`
- `data/repositories/hero_repository_impl.dart`: как `equip` — `_guard(() async { await _remote.discard(itemId, quantity: quantity); return _mapSnapshot(await _remote.getMe()); })`.
- `data/mappers/hero_mapper.dart`, `_EquippedEntryMapper.toDomain()`: `description: item.description,`.
- `presentation/bloc/hero_cubit.dart`: `Future<void> discard(String itemId, {int quantity = 1})` — копия `equip` с вызовом `_repository.discard`; успех → `s.copyWith(snapshot: snapshot, selectedItemId: null, errorMessage: null)`.
- `presentation/bloc/hero_state.dart`: `final List<StatDelta> statDeltas;` (default `const []`), в `copyWith`, метод `clearStatDeltas()` по образцу `clearError()`.
- `domain/entities/stat_delta.dart`: `class StatDelta { final String labelKey; /* 'hero.derived.phys_atk' */ final num delta; }` (freezed или plain — как `DerivedStats`).
- `domain/usecases/derived_stats_diff.dart`: `List<StatDelta> derivedStatsDiff(DerivedStats before, DerivedStats after)` — поля и ключи по порядку: `maxHp→hero.derived.hp`, `maxResource→hero.derived.rage|mana` (по `after.resourceType`), `armor→hero.derived.armor`, `mResist→hero.derived.m_resist`, `physAtk→hero.derived.phys_atk`, `magicAtk→hero.derived.magic_atk`, `atkSpeed→hero.derived.atk_speed`, `critPct→hero.derived.crit`; в список попадают только ненулевые дельты.
- `lib/shared/extensions/context_extensions.dart`: `void showInfoSnackBar(String message)` — копия `showErrorSnackBar` с `duration: const Duration(seconds: 3)`.
- `presentation/pages/hero_page.dart`, listener: после блока `errorMessage` — `if (loaded.statDeltas.isNotEmpty) { context.showInfoSnackBar(loaded.statDeltas.map((d) => '${d.labelKey.tr()} ${d.delta > 0 ? '+' : '−'}${d.delta.abs()}').join(' · ')); cubit.clearStatDeltas(); }`; в `showItemInspectSheet` добавить `onDiscard: (qty) { cubit.discard(item.id, quantity: qty); Navigator.of(context).pop(); }` и `equippedInSlot: item.slot == null ? null : loaded.snapshot.equippedIn(item.slot!)`.
- `presentation/widgets/item_inspect_sheet.dart`: новые параметры `required ValueChanged<int> onDiscard`, `InventoryItem? equippedInSlot`; под EQUIP (или вместо, если `slot == null`) — `AppButton(label: 'hero.discard'.tr(), variant: AppButtonVariant.outline, icon: Icons.delete_outline, onPressed: () => _confirmDiscard(context))`; `_confirmDiscard` — `showDialog<int>` с `AlertDialog` (эталон — `battle_page.dart:150`): title `hero.discard_title` (`{name}`), actions: `app.cancel` → `null`; `quantity == 1` → `hero.discard` → `1`; иначе `hero.discard_one` → `1` и `hero.discard_all` (`{n}`) → `quantity`; результат `!= null` → `onDiscard(result)`. Бонусы: вместо `Wrap` чипов — `Column` строк `_BonusRow(labelKey, value, delta)` для 9 бонусов с ненулевым `value` **или** ненулевым значением у `equippedInSlot`; `delta = value - equippedInSlot.<bonus>` (null, если `equippedInSlot == null`); над таблицей `Text('hero.vs_equipped'.tr(namedArgs: {'name': equippedInSlot.name}))`, когда `equippedInSlot != null`. Цвета: ▲ `tokens.success`, ▼ `tokens.error`, `—` `tokens.mutedForeground` (если таких токенов нет — взять ближайшие из `RealmWalkerTheme`).
- Переводы (`assets/translations/en.json` / `ru.json`, блок `hero` и `app`):

  | ключ | en | ru |
  |---|---|---|
  | `hero.discard` | Discard | Выбросить |
  | `hero.discard_title` | Discard {name}? | Выбросить {name}? |
  | `hero.discard_one` | Discard 1 | Выбросить 1 |
  | `hero.discard_all` | Discard all (×{n}) | Выбросить все (×{n}) |
  | `hero.vs_equipped` | VS. EQUIPPED {name} | ПРОТИВ НАДЕТОГО {name} |
  | `app.cancel` | Cancel | Отмена |

- Тесты (зеркалят `lib/`): `test/features/profile/data/mappers/hero_mapper_test.dart` — `description is mapped through (null when absent)`; `test/features/profile/data/repositories/hero_repository_impl_test.dart` — группа `discard`: `calls the endpoint with quantity and re-reads getMe`, `propagates a 400 from discard as Left(ValidationFailure)` (эталон — группа `equip`, `dioBadResponse` из `test/helpers/dio_error.dart`); `test/features/profile/presentation/bloc/hero_cubit_test.dart` — группа `discard` (успех без Loading и с `selectedItemId == null`; ошибка → `errorMessage`, снапшот прежний; double-tap игнорируется) и `stat deltas after equip` (`_snapshot` с другим `physAtk` → `statDeltas` содержит `hero.derived.phys_atk`; `clearStatDeltas` → пусто; `allocate` не заполняет); `test/features/profile/domain/usecases/derived_stats_diff_test.dart` — чистая таблица кейсов; `hero_page_smoke_test.dart` — остаётся зелёным (новые параметры sheet — с дефолтами или проброшены).

### Запреты

- Prisma — только `npm run prisma:migrate` (deploy). **Никогда** `migrate dev`.
- Дев-процессы (`start:*`, `flutter run`, docker) не запускать — только команды проверки; поднятие gateway и генерацию Dart-клиента делает пользователь.
- Без подписей ассистента в коммитах; ключ задачи — в сообщении коммита.
- Чужие незакоммиченные файлы не трогать; `packages/troy_backend_api` руками не править.
- Не переименовывать Swagger-классы и не менять сигнатуры существующих эндпоинтов инвентаря.

## Промты

### Сессия 1 — SCRUM-15 + SCRUM-16 (troy-backend + troy-admin) · Sonnet

Код, контракт и тесты даны дословно — свободы нет. Годится и делегату (GLM/codex) с ревью Opus. Режим — acceptEdits.

```
Работаем в /Users/fost/Projects/troy (troy-backend, в конце — troy-admin).

Задачи: SCRUM-15 — Item.description: колонка, миграция, seed, выдача в API;
SCRUM-16 — Выбросить предмет: DELETE /inventory/:itemId. Инвентарь, equip/unequip и
админка предметов уже работают — это доработка, не стройка.

Начни с `bash ~/.claude/skills/troy-jira/jira.sh view SCRUM-15` и `... view SCRUM-16`,
переведи обе в «В работе» (`bash ~/.claude/skills/troy-jira/jira.sh transition SCRUM-15 "В работе"`,
то же для SCRUM-16). Токен: `export $(grep -oE 'JIRA_CLOUD_[A-Z]+=[^ ]+' ~/.zshrc | tr -d '"'"'" | xargs)`.

План — troy-docs/roadmap/mvp-3-inventory/description-discard.md: этапы 1–3, чекбоксы,
раздел «Контракт и точки входа» с готовым кодом, текстами seed и таблицей тестов.
Иди строго по нему, галочки ставь по факту проверки.

Прочитай ещё:
- troy-docs/roadmap/mvp-3-inventory/README.md и backend-gaps.md (#1, #3, #7);
- troy/CLAUDE.md (раздел Testing и Key design decisions);
- эталоны кода: apps/game-core/src/app/inventory/inventory.service.spec.ts,
  apps/api-gateway/src/app/dto/map.dto.ts.

Уже решено (05.09, не переспрашивать): DELETE /inventory/:itemId?quantity=N, N>=1,
default 1; N > quantity → 400 "Not enough items to discard"; N == quantity и надет →
400 "Unequip the item first"; N < quantity — декремент даже у надетого; ответ — полный
инвентарь как у equip. Миграция 0019_item_description отдельная. В getMe инвентарь —
все строки отдельным findMany (include item), ACTIVE_CHARACTER_SELECT не трогать.
Swagger-классы не переименовывать. description до 500 символов, пустое → null.

Порядок:
1. Этап 1 — schema + миграция 0019 + getMe полный инвентарь + admin service + контракты
   + Swagger DTO + seed + тесты + database-schema.md.
2. Этап 2 — контракт INVENTORY_DISCARD, InventoryService.discard, хендлер, query DTO,
   @Delete в gateway, 6 unit-кейсов, строка в README бэкенда.
3. Этап 3 — troy-admin: поле description в src/api/items.ts и ItemFormModal.tsx.

DoD: миграция применяется (`npm run prisma:migrate`), `npx nx run-many -t test` и
`npx nx run-many -t build` зелёные в troy-backend; `npx tsc -b --noEmit` и `npm run lint`
чистые в troy-admin. Тесты — часть DoD: 6 кейсов discard, getMe full inventory,
create с description.

Ветка main, коммиты без подписей ассистента, ключ задачи в сообщении (отдельные коммиты
на backend и admin). Prisma — только `migrate deploy`. Дев-процессы не запускать.
Чужие незакоммиченные файлы не трогать.

По завершении: /troy-continue. В итоговом сообщении напомни пользователю перегенерировать
Dart-клиент (`./tools/generate_openapi.sh` в troy-flutter при запущенном gateway) — без
этого сессия 2 не стартует.
```

### Сессия 2 — SCRUM-75 (клиент 15/16) + SCRUM-49 (troy-flutter) · Sonnet, этап 5 на max + ревью Opus · после сессии 1

Этап 4 — механика по эталону `equip`. Этап 5 — новая вёрстка строк с дельтой, `statDeltas` в `HeroLoaded` с сентинелом `_noChange`, живой `hero_page_smoke_test` — место, где слабая модель начинает изобретать; прогнать `/review-local` на Opus до коммита. Режим — acceptEdits.

```
Работаем в /Users/fost/Projects/troy (troy-flutter).

Задачи: SCRUM-75 — клиентская часть SCRUM-15/16 (описание предмета в карточке, кнопка
Discard), плюс SCRUM-49 — визуальный отклик на смену статов после equip/unequip.
Hero-экран на реальном API уже есть (lib/features/profile) — это доработка.

Предусловие: клиент перегенерирован. Проверь:
`grep -c inventoryControllerDiscard packages/troy_backend_api/lib/src/api/inventory_api.dart`
и `grep -c description packages/troy_backend_api/lib/src/model/equipped_item_dto.dart` —
оба ≥ 1. Если нет — остановись и попроси пользователя запустить
`./tools/generate_openapi.sh` при поднятом gateway; пакет руками не править.

Начни с `bash ~/.claude/skills/troy-jira/jira.sh view SCRUM-75` и `... view SCRUM-49`
(SCRUM-15/16 закрыты — бэкенд и админка сделаны) и переведи обе в «В работе».
Токен: `export $(grep -oE 'JIRA_CLOUD_[A-Z]+=[^ ]+' ~/.zshrc | tr -d '"'"'" | xargs)`.

План — troy-docs/roadmap/mvp-3-inventory/description-discard.md: этапы 4–5, решения 5–7,
раздел «Контракт и точки входа → Flutter» с файлами, ключами переводов и списком тестов.
Иди строго по нему, галочки ставь по факту проверки.

Прочитай ещё:
- troy-docs/roadmap/mvp-3-inventory/README.md и redesign.md (раздел решений);
- раздел "Architecture rules (MUST follow)" в troy-flutter/CLAUDE.md, эталон — lib/features/auth;
- эталоны тестов: test/features/profile/** (mapper, repository_impl, cubit).

Уже решено (05.09, не переспрашивать): discard — кнопка DISCARD (outline) под EQUIP,
AlertDialog подтверждения, для стака — «Discard 1» / «Discard all (×N)»; успех закрывает
sheet; ошибки — через errorMessage-снекбар как у equip. Тост после equip/unequip — дифф
profile.derived старого и нового снапшота («PHYS ATK +7 · ARMOR −2»), пусто — тоста нет;
хранится в HeroLoaded.statDeltas, чистая функция derivedStatsDiff без локализации.
В sheet бонусы — строками с дельтой против надетого в этот слот и заголовком
«VS. EQUIPPED <имя>». UNEQUIP в sheet — не делаем (redesign). Тексты — только через
переводы, ключи в плане.

Порядок:
1. Этап 4 — description в маппере; discard через datasource → repository → cubit →
   sheet → page; переводы; тесты mapper/repository/cubit.
2. Этап 5 — StatDelta + derivedStatsDiff, statDeltas в HeroLoaded, showInfoSnackBar,
   listener в hero_page, дельты в sheet; тесты usecase/cubit; smoke остаётся зелёным.

DoD: `flutter analyze` чисто, `flutter test` зелёный; описание видно в карточке, предмет
выбрасывается, после equip виден тост. Тесты — часть DoD (список в плане).

Ветка main, коммиты без подписей ассистента, по-русски в стиле истории репо, ключ в
хвосте — например `feat(profile): описание предмета и discard в карточке (SCRUM-75)`;
SCRUM-75 — один коммит, SCRUM-49 — отдельный. `flutter run` и дев-процессы не запускать; визуально
проверяет пользователь. Чужие незакоммиченные файлы не трогать.

По завершении: /troy-continue — закрыть SCRUM-75 и SCRUM-49, отметить галочки в
README фазы, backend-gaps.md (#1, #3, #7) и roadmap/README.md.
```
