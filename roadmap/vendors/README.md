# Торговцы на карте — покупка и продажа за золото

> **Статус: спека (05.09), код не начат.** Сквозная тема после MVP (торговля в scope MVP не входит —
> [roadmap/README.md](../README.md), «Не входит»). Эпик [SCRUM-67](https://fosteev.atlassian.net/browse/SCRUM-67).
> Решения: торговец — данные (`Vendor`), как моб; экземпляр на карте — `active_vendors` (PostGIS) с
> `expires_at`; видимость **общая**, сток **общий и конечный**; цикл — cron каждые 6 ч сносит всех и ставит
> новых с шансом на зону; цена — `Item.vendorPrice` или формула от бюджета статов; продажа — 25 % цены, без
> buyback; торговля — **REST**, дистанция проверяется на сервере тем же радиусом, что и бой. Цифры (6 ч, 0.5,
> стоянка 2–5 ч, K = 10, 0.25) — стартовые, калибруются в фазе 7.

Первый sink золота: сейчас `Character.gold` растёт с каждого боя (`goldReward`, 7–80 за моба) и не тратится
([items/README.md](../items/README.md), аудит: «золото без sink»). Торговец — редкое событие на карте: не в каждой
зоне и не всегда, стоит ограниченное время, ассортимент случайный. Это даёт повод ходить и повод копить.

## Аудит (05.09) — на что опираемся

| Слой | Как есть | Что берём |
|---|---|---|
| Золото | `Character.gold`, начисляется в `BattleService` при победе (`goldDelta` в `battle:end`) | Списание/начисление — те же поля, транзакцией |
| Предметы | `Item` без цены; ilvl/редкость-как-бюджет — спека [items §1, §3](../items/README.md), миграция `0020_item_progression` (SCRUM-62) в коде | Формула цены от бюджета; до ilvl — `vendorPrice` руками |
| Спавн мобов | `active_spawns` raw SQL (PostGIS), `SpawnCronService` (среда 00:00 UTC, `capacity` на соту активного города, `ST_GeneratePoints` по `Territory.geometry` — модель [cities](../cities/README.md)), admin-триггер, `scripts/spawn-run.ts` | Тот же паттерн: своя таблица, свой cron, свой скрипт; цикл **не** привязан к недельному |
| Карта | WS `map:request` → `map:entities` (30 с Redis-кэш на персонажа), сейчас только мобы (`type: 'monster'`) | Добавляем `type: 'vendor'` в тот же поток |
| Дистанция | `battle:start` считает `haversine` до спавна против `INTERACTION_RADIUS_M` (50 м), escape hatch `IGNORE_BATTLE_DISTANCE` | Тот же чек в buy/sell |
| Инвентарь | `InventoryService.addItems(userId, entries)` — общий вход лута; discard (SCRUM-16) и лимит мешка (SCRUM-65) не сделаны | Покупка идёт через `addItems`; продажа частично закрывает потребность в discard |
| Визуалы | `Monster.spriteIdle/…` (`ClassSpriteSheet` JSON), `GET /monsters/:id/visuals`, спрайты не таскаются в карте | Те же поля и тот же отдельный эндпоинт визуалов |
| Админка | `MonstersPage` + `MonsterFormModal` (спрайты через `components/sprites`), `MonsterDropsPanel` + `ItemPickerModal`, `SpawnPage` (зоны, активные спавны, «Запустить respawn», `SpawnMapModal`) | Раздел «Торговцы» копирует мобов; активные торговцы — рядом со спавнами |
| Flutter | `MapEntity` — только моб; `MonsterMapMarker` (idle-спрайт / диск), `MonsterInfoCard`; фичи по эталону `auth` | Ветвление по `type`, новая фича `vendors/` |
| Ассеты | `troy-assets` — `styles/{class,mob,boss}.yaml`, `publish.mjs`, Retro Diffusion | `styles/vendor.yaml`, `kind: vendor` |

## Продуктовый результат

- На карте изредка стоит торговец: маркер отличается от моба (не угроза), на ярлыке — сколько ему осталось стоять.
- Подошёл (50 м) → тап → экран торговли: слева он сам (idle-анимация), золото игрока, вкладки «Купить» / «Продать».
- Купил: золото списалось, предмет в мешке, торговец сыграл анимацию сделки. Продал: золото пришло, предмет ушёл.
- Ассортимент у каждого экземпляра свой и случайный, остатки конечные: последний товар достаётся первому.
- Через несколько часов торговец уходит; в следующем цикле торговцы появляются в других местах и с другим товаром.
- Контент-мейкер заводит торговца целиком из админки: внешний вид, описание, анимации, пул товаров, где встречается.

---

## 1. Данные

Миграция `0024_vendors` (`0019`–`0023` заняты items/zones/cities). Накатывать **`migrate deploy`, не `migrate dev`** — дропнет
`active_spawns`, `City.boundary`, `Territory.geometry` (и `active_vendors` после этой миграции).

Prisma:

```prisma
model Vendor {
  id              String   @id @default(uuid()) @db.Uuid
  code            String   @unique          // 'wandering_merchant' — стабильный код для клиента и конвейера
  name            String
  description     String?                   // текст игроку (карточка, экран торговли); RU, EN — MVP-5
  iconUrl         String?                   // фолбэк маркера, если нет spriteIdle
  spriteIdle      Json?                     // ClassSpriteSheet | null — стоит (маркер + экран торговли)
  spriteDeal      Json?                     // ClassSpriteSheet | null — конец сделки, один проход → idle
  dwellMinMin     Int      @default(120)    // стоянка, минуты: expires_at = spawned_at + randInt(min, max)
  dwellMaxMin     Int      @default(300)
  priceMultiplier Float    @default(1.0)    // жадный торговец 1.2, распродажа 0.8 — множитель к цене покупки
  stockSlotsMin   Int      @default(4)      // сколько разных товаров выкладывает
  stockSlotsMax   Int      @default(6)
  spawnable       Boolean  @default(true)
  stockPool       VendorStockPool[]
}

// Аналог DropTable: из чего собирается ассортимент экземпляра.
model VendorStockPool {
  id       String @id @default(uuid()) @db.Uuid
  vendorId String @db.Uuid
  itemId   String @db.Uuid
  weight   Int    @default(1)
  qtyMin   Int    @default(1)
  qtyMax   Int    @default(1)
  vendor   Vendor @relation(fields: [vendorId], references: [id], onDelete: Cascade)
  item     Item   @relation(fields: [itemId], references: [id])
  @@unique([vendorId, itemId])
}

// Товар конкретного экземпляра на карте. Цена фиксируется при спавне.
model ActiveVendorStock {
  id             String @id @default(uuid()) @db.Uuid
  activeVendorId String @db.Uuid   // = active_vendors.id; FK ON DELETE CASCADE добавляется raw SQL в той же миграции
  itemId         String @db.Uuid
  quantity       Int
  price          Int
  item           Item   @relation(fields: [itemId], references: [id])
  @@index([activeVendorId])
}

// Для баланса: что покупают/продают, по какой цене. Аналог BattleLog.
model TradeLog {
  id             String    @id @default(uuid()) @db.Uuid
  characterId    String    @db.Uuid
  vendorId       String    @db.Uuid
  activeVendorId String    @db.Uuid
  itemId         String    @db.Uuid
  kind           TradeKind // BUY | SELL
  quantity       Int
  goldDelta      Int       // отрицательный при покупке
  createdAt      DateTime  @default(now())
  @@index([characterId, createdAt])
}

enum TradeKind { BUY SELL }
```

Плюс к существующим моделям: `SpawnZone.vendorIds String[] @default([])` (каких торговцев зона принимает — зеркало
`monsterIds`), `Item.vendorPrice Int?` (override; `null` → формула).

Raw SQL в той же миграции (по образцу `0001_init` / `0017_monster_packs`):

```sql
CREATE TABLE active_vendors (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor_id     UUID NOT NULL REFERENCES "Vendor"(id),
  spawn_zone_id UUID NOT NULL REFERENCES "SpawnZone"(id),
  location      GEOGRAPHY(POINT, 4326) NOT NULL,
  spawned_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at    TIMESTAMPTZ NOT NULL
);
CREATE INDEX active_vendors_location_idx ON active_vendors USING GIST (location);
ALTER TABLE "ActiveVendorStock"
  ADD CONSTRAINT "ActiveVendorStock_activeVendorId_fkey"
  FOREIGN KEY ("activeVendorId") REFERENCES active_vendors(id) ON DELETE CASCADE;
```

Почему так: `active_vendors` вне Prisma по той же причине, что `active_spawns` (GEOGRAPHY); сток — в Prisma, потому что
`buy` — обычная транзакция без геометрии. `expires_at` вместо `alive`: истёкший торговец просто не попадает в выборки,
физически чистится следующим циклом.

**Цена** — чистая функция в `libs/shared/utils` (`vendorPrice(item, multiplier)`), одна на бэкенд и админку-превью:

```
buyPrice  = item.vendorPrice ?? round(budget(itemLevel) × mult(rarity) × VENDOR_PRICE_K)   // items §3: budget = 3 + ilvl
buyPrice  = max(1, round(buyPrice × vendor.priceMultiplier))
sellPrice = max(1, floor(buyPrice(без multiplier) × VENDOR_SELL_RATIO))
```

`VENDOR_PRICE_K = 10` → Iron Sword (ilvl 1, common) ≈ 40 золота ≈ 5 крыс; Knight Shield (uncommon) ≈ 48; зелье 15–20.
До SCRUM-62 `itemLevel` считается 1 — цены плоские, поэтому у сида проставляем `vendorPrice` руками.
`VENDOR_SELL_RATIO = 0.25` — как у WoW-вендоров; инвариант «продать дешевле, чем купить» держится при любом
`priceMultiplier ≥ 0.25`, проверяется тестом.

- [ ] Prisma-модели, `SpawnZone.vendorIds`, `Item.vendorPrice`, raw SQL `active_vendors` + FK стока — миграция `0024_vendors`
- [ ] `libs/shared/contracts`: NATS-паттерны `vendor.get / vendor.buy / vendor.sell / vendor.visuals`, `admin.vendor.*`
      (list/get/create/update/delete/stock.list/stock.replace/active.list/respawn), интерфейсы DTO
- [ ] `libs/shared/utils`: `vendorPrice` / `vendorSellPrice` + spec (таблица кейсов, инвариант sell < buy)
- [ ] Env в `.env.example`: `VENDOR_RESPAWN_CRON`, `VENDOR_ZONE_CHANCE`, `VENDOR_PRICE_K`, `VENDOR_SELL_RATIO`
- [ ] Seed: два торговца («Странствующий торговец» — всё понемногу, `priceMultiplier 1.0`; «Скупщик» — только
      расходники и дешёвый шмот, `priceMultiplier 0.9`, стоянка короче), пулы из 5 сид-предметов, `vendorIds` у
      трёх зон, `vendorPrice` у 5 предметов
- [ ] `technical/database-schema.md`: разделы Vendor, VendorStockPool, ActiveVendorStock, TradeLog, active_vendors,
      новые поля SpawnZone/Item, enum TradeKind

**Готово, когда:** `npm run prisma:migrate` на dev проходит, `npm run prisma:generate`, `npm run prisma:seed` создаёт
двух торговцев с пулами; `npx nx run-many -t test` зелёные (включая spec цены).

## 2. Спавн-цикл и карта

Модуль `apps/game-core/src/app/vendor/` (`VendorCronService`, позже `VendorService`, `VendorAdminService`).

Цикл: `@Cron(process.env.VENDOR_RESPAWN_CRON ?? '0 */6 * * *', UTC)` → `respawn()`:

1. `DELETE FROM active_vendors` (сток уходит каскадом).
2. По каждой активной зоне с сотами в активных городах и непустым `vendorIds` (только `spawnable`):
   `Math.random() < VENDOR_ZONE_CHANCE` → один торговец случайно из списка, точка `ST_GeneratePoints(t.geometry, 1)`
   в случайной соте зоны (`Territory` JOIN `City(isActive)`; у зоны своей геометрии нет с `0023`, см. cities),
   `expires_at = now() + randInt(dwellMinMin, dwellMaxMin) minutes`.
3. Сток: `n = randInt(stockSlotsMin, stockSlotsMax)` **разных** предметов из пула по весам (без повторов; если пул
   меньше n — весь пул), `quantity = randInt(qtyMin, qtyMax)`, `price = buyPrice(item, vendor)`.
4. Сводка `{ zones, vendors, stockRows }` — как `SpawnRespawnSummary`.

Стоянка короче цикла по умолчанию (2–5 ч при цикле 6 ч), поэтому между «ушёл» и «пришли новые» есть пауза — так и
задумано: торговец не должен стоять вечно. Редкость = `VENDOR_ZONE_CHANCE × доля стоянки в цикле`; при трёх зонах и
0.5 в среднем 1–2 торговца на карте, половину времени.

Карта: `MapService.getEntities` добавляет `UNION ALL` по `active_vendors WHERE expires_at > now() AND ST_DWithin(...)`:
`type: 'vendor'`, `id` (= active_vendors.id), `vendorId`, `name`, `lat/lng`, `distance`, `canInteract`, `expiresAt`.
Без персонального фильтра — торговец виден всем. Кэш 30 с не меняем: остатки стока в карте не отдаём, они — в
`GET /vendors/:id`. Swagger: `MapEntityDto` получает `type: 'monster' | 'vendor'` и опциональные vendor-поля (или
`oneOf` двух DTO — решить при реализации, клиенту важен только `type`).

- [ ] `VendorCronService.respawn()` + `@Cron` из env; выбор без повторов из пула по весам; фиксация цены
- [ ] NATS `admin.vendor.respawn` → `respawn()`; `scripts/vendors-run.ts` + npm `vendors:run` (по образцу `spawn:run`)
- [ ] `MapService.getEntities`: UNION торговцев, `expiresAt` ISO, `canInteract` тем же радиусом
- [ ] Swagger `MapEntityDto` / `MapEntityResponseDto` — `type` union и vendor-поля
- [ ] Unit: `vendor-cron.service.spec.ts` (шанс 0 → пусто, шанс 1 → по одному на зону, пул меньше `stockSlotsMin`,
      нет дубликатов предметов, `expires_at` в диапазоне, цена = формула × multiplier); `map.service.spec.ts` — вендор в выдаче

**Готово, когда:** `npm run vendors:run` на dev → строки в `active_vendors` и `ActiveVendorStock`; WS `map:request`
возвращает сущность с `type: 'vendor'` и `expiresAt`; истёкший (руками `UPDATE expires_at = now() - 1h`) в выдачу не попадает.

## 3. Торговля — backend

`VendorService`, все три операции начинаются с одного гейта `loadLiveVendor(activeVendorId, lat, lng)`:
торговец существует и `expires_at > now()` → иначе `vendor_gone` (409); `haversine(lat, lng, vendor)` ≤
`INTERACTION_RADIUS_M` → иначе `too_far` (400); `IGNORE_BATTLE_DISTANCE` уважается, как в бою. Позицию клиент
присылает в теле запроса — так же, как в `battle:start`.

- `get(userId, activeVendorId, lat, lng)` → `{ vendor: {id, vendorId, code, name, description, expiresAt},
  canInteract, gold, sellRatio, stock: [{ id, item: ItemSummary, quantity, price }] }`. Возвращается и вне радиуса
  (карточка на карте показывает ассортимент), но `canInteract: false`.
- `buy(userId, activeVendorId, stockId, quantity, lat, lng)` — одна транзакция:
  `UPDATE "ActiveVendorStock" SET quantity = quantity - n WHERE id = $1 AND quantity >= n RETURNING` → пусто →
  `sold_out`; `UPDATE "Character" SET gold = gold - price×n WHERE id AND gold >= price×n RETURNING` → пусто →
  `not_enough_gold`; лимит мешка (после SCRUM-65) → `bag_full`; `InventoryService.addItems`; `TradeLog(BUY)`.
  Ответ `{ gold, stock, added: InventoryItem }`. Порядок «сток → золото → мешок» даёт гонке за последний товар
  один честный исход без блокировок.
- `sell(userId, activeVendorId, inventoryItemId, quantity, lat, lng)` — транзакция: строка инвентаря принадлежит
  активному персонажу; `isEquipped` → `item_equipped` (сначала снять — как в WoW); `quantity` ≤ остатка;
  `sellPrice` по формуле; декремент / удаление строки; `gold += sellPrice×n`; `TradeLog(SELL)`. Торговец предмет
  **не получает** — buyback не делаем. Ответ `{ gold, inventory }`.
- `visuals(vendorId)` → `{ id, code, name, description, iconUrl, spriteIdle, spriteDeal }` — по образцу
  `GET /monsters/:id/visuals`, по **шаблону** (`Vendor.id`), не по экземпляру.

REST в api-gateway (JWT guard, class-validator, Swagger):

| Метод | Путь | Тело |
|---|---|---|
| GET | `/vendors/:activeVendorId?lat&lng` | — |
| POST | `/vendors/:activeVendorId/buy` | `{ stockId, quantity, lat, lng }` |
| POST | `/vendors/:activeVendorId/sell` | `{ inventoryItemId, quantity, lat, lng }` |
| GET | `/vendors/templates/:vendorId/visuals` | — |

Rate limit — глобальный throttle (60/мин) достаточен; отдельного бакета не заводим.

- [ ] `VendorService.get / buy / sell / visuals`, `VendorController` (NATS), регистрация модуля в `app.module.ts`
- [ ] api-gateway `vendors.controller.ts` + DTO + Swagger; коды ошибок в общий маппинг NATS → HTTP
- [ ] `technical/vendor-trade.md`: эндпоинты, тела, коды ошибок (`vendor_gone`, `too_far`, `sold_out`,
      `not_enough_gold`, `bag_full`, `item_equipped`), цикл, инварианты (sell < buy, сток общий, buyback нет)
- [ ] Unit `vendor.service.spec.ts` (мок Prisma-транзакции): все ветки ошибок, успешный buy списывает ровно
      price×n и зовёт `addItems`, sell с частичным количеством, продажа стака целиком удаляет строку,
      `IGNORE_BATTLE_DISTANCE`

**Готово, когда:** сценарий curl на dev: `get` → `buy` → золото в `GET /character/me` меньше на цену, предмет в
`GET /inventory` → `sell` → золото больше на `floor(price × 0.25)`; повторный `buy` последнего экземпляра →
`sold_out`; `buy` с координатами в 1 км → `too_far`; тесты зелёные.

## 4. Админка

Раздел «Торговцы» (`/vendors`) — по образцу мобов; активные торговцы — рядом со спавнами.

- [ ] Бэк: `vendor-admin.service.ts` + spec, `vendor-admin.controller.ts` (game-core), `admin-vendors.controller.ts`
      (api-gateway), `AdminVendorDto`; Swagger
- [ ] `VendorsPage` + `VendorFormModal`: code, name, description, iconUrl, `spriteIdle` / `spriteDeal` через
      существующий загрузчик спрайтов (`components/sprites`, webp → S3), стоянка min/max (мин), `priceMultiplier`,
      слотов min/max, `spawnable`
- [ ] `VendorStockPanel` — пул товаров по образцу `MonsterDropsPanel` + `ItemPickerModal`: предмет, вес, qty min/max,
      колонка «цена у этого торговца» из `vendorPrice()` (превью, считается на клиенте той же функцией)
- [ ] `SpawnPage`: мультиселект «Торговцы» у зоны (`vendorIds`, рядом с мобами); вкладка/блок «Активные торговцы»
      (торговец, зона, координаты, «уйдёт через» / «ушёл», остатки стока), кнопка «Обновить торговцев»
      (`admin.vendor.respawn`), точки торговцев на `SpawnMapModal` другим цветом
- [ ] `ItemsPage` / `ItemFormModal`: поле «Цена у торговца» (`vendorPrice`; пусто = по формуле, рядом показать
      вычисленную)
- [ ] Меню и роут в `AdminLayout` / `App.tsx`; `api/vendors.ts`

**Готово, когда:** из админки заведён торговец с пулом и спрайтами, зона его принимает, «Обновить торговцев» ставит
его на карту и он виден в «Активных»; `npx tsc -b --noEmit` чисто.

## 5. Flutter

Новая фича `lib/features/vendors/` по эталону `auth` (domain / data / presentation); карта учится второму типу сущности.

- [ ] `MapEntity`: ветвление по `type` — либо sealed (`MonsterMapEntity` / `VendorMapEntity`), либо `type` + nullable
      vendor-поля; `VendorMapEntity { id, vendorId, name, lat, lng, distance, canInteract, expiresAt }`; маппер с
      тестом на оба типа
- [ ] `VendorMapMarker`: idle-спрайт из `GET /vendors/templates/:id/visuals` (кэш как у `monster_sprites.dart`),
      фолбэк — диск с `iconUrl`; золотая рамка вместо багровой (не угроза); на ярлыке таймер «1ч 20м»
- [ ] `VendorInfoCard`: имя, описание, «уйдёт через …», кнопка «Торговать» при `canInteract`, иначе дистанция
- [ ] Репозиторий `get / buy / sell` (`Either<Failure, T>`), `VendorTradeBloc` (load → buy/sell → refresh),
      маппинг кодов ошибок в `Failure`
- [ ] `VendorTradePage`: шапка — торговец (idle-спрайт, `SpriteSheetAnimator`), имя, «уйдёт через», золото игрока;
      вкладки «Купить» (иконка, имя, редкость, цена, остаток, шаг количества, «Купить») и «Продать» (мешок без
      экипированного, цена продажи, количество для стака); подтверждение суммы; кнопки disabled на время запроса
      (защита от двойного тапа)
- [ ] Анимация сделки: после успешного buy/sell `spriteDeal` один проход → назад в idle; всплывающее «−40» / «+10»
      у золота; хук под звук монет (сам звук — P2, SCRUM-9)
- [ ] Ошибки → тексты и поведение: `vendor_gone` — тост и закрыть экран (маркер убрать локально до следующего
      `map:request`), `sold_out` — обновить сток, `not_enough_gold`, `too_far`, `bag_full`, `item_equipped`
- [ ] Золото после сделки обновляется везде, где показано (HUD карты, Hero-экран) — через `ActiveCharacterCubit`
- [ ] Прототип `design/prototypes/vendor-trade.html` (карточка на карте + экран торговли) — до вёрстки, по правилам
      [prototypes/README.md](../../design/prototypes/README.md)
- [ ] Локализация RU/EN ключей (EN — черновой, финал в MVP-5)
- [ ] Тесты: маппер (оба типа), bloc (buy success / sold_out / vendor_gone), widget-smoke `VendorInfoCard` и
      `VendorTradePage`

**Готово, когда:** `flutter analyze && flutter test` чисто; на устройстве: подошёл → карточка → купил → предмет в
мешке, золото уменьшилось, анимация сыграла → продал → золото выросло; ушедший торговец пропадает с карты.

## 6. Арт и конвейер

- [ ] `troy-assets/styles/vendor.yaml` (`kind: vendor`): ключевая поза 128 `rd_pro__fantasy`, idle 8 кадров
      (спокойное дыхание, как классы), deal 6 кадров (`custom_action`: кивок и протянутый кошель / подброшенная
      монета), иконка маркера 64
- [ ] `publish.mjs` понимает vendor: upsert `Vendor` по `code`, спрайты idle/deal, description, `db:`-блок пула
- [ ] Карточки `troy-docs/vendors/<code>.md` по образцу [mobs/_template.md](../../mobs/_template.md): описание,
      пул, стоянка, промты арта
- [ ] Сгенерировать и залить на dev двух торговцев из сида (ориентир бюджета — goblin_warrior целиком $1.56)

**Готово, когда:** на устройстве маркер и экран торговли с реальными спрайтами, deal-анимация читается как сделка.

## 7. Баланс и контент

После недели данных `TradeLog` на dev.

- [ ] `game-design/economy.md`: источники золота (`goldReward`, таблица якорей из
      [content-generation.md](../../game-design/content-generation.md)), sink (торговцы), формула цены, ratio продажи,
      цикл / шанс / стоянка — с фактическими цифрами после калибровки (черновик — в фазе 1 вместе со схемой)
- [ ] Калибровка `VENDOR_PRICE_K`, `VENDOR_SELL_RATIO`, `VENDOR_RESPAWN_CRON`, `VENDOR_ZONE_CHANCE`, стоянок — по
      одному рычагу за раз
- [ ] Пулы под контент MVP-4: после ilvl (SCRUM-62) — товар в диапазоне уровня зоны (фильтр пула по
      `itemLevel ∈ [minLevel, maxLevel]` при спавне, если пулы одного торговца начнут ездить по зонам разного уровня)
- [ ] Уведомление «рядом появился торговец» через существующий WS `notification` — только если торговцев
      реально не находят

**Готово, когда:** цифры в `economy.md` совпадают с env dev, и у игрока 5–10 lvl есть на что копить (хотя бы один
предмет дороже золота с 10 боёв).

## Не тащим

Buyback и выкуп проданного, ремонт/прочность, репутация и персональные скидки, торг, аукцион и обмен между
игроками, вторая валюта, квесты и диалоги у торговцев, ограничение продажи по редкости, торговцы-мобы (напасть на
торговца), инвентарь торговца, который «пополняется» между циклами.

## Риски и открытые вопросы

- **Общий сток vs персональный** — принято общий (проще, даёт «успел первым»). При очень редких торговцах и
  активных игроках новичок может приходить к пустому прилавку — тогда переключаемся на персональный сток
  (генерировать `ActiveVendorStock` per character при первом `get`): схема это позволяет, меняется только один
  запрос. Решение пользователя, если увидим пустые прилавки.
- **Плоские цены до ilvl** — до SCRUM-62 формула даёт одно и то же всем common; на сиде спасает `vendorPrice`
  руками. Не блокирует, но фазу 7 без ilvl не начинать.
- **`bag_full`** зависит от лимита мешка (SCRUM-65); до него покупка при 40+ строках проходит — согласовано с тем,
  что лимит сейчас только на клиенте.
- **Кэш карты 30 с** — торговец, ушедший минуту назад, ещё виден; `get`/`buy` ответят `vendor_gone`, клиент убирает
  маркер локально. Приемлемо.
- **Двойной тап / гонка** — на сервере атомарные `UPDATE … WHERE quantity >= n` / `gold >= sum`, на клиенте disabled
  на время запроса. Идемпотентный `requestId` не заводим.
- **Бюджет арта** — два торговца ≈ $3–4 на Retro Diffusion; deal-анимация через `custom_action` — первый раз,
  может потребовать пары итераций промта.
- **Допущение:** цифры 6 ч / 0.5 / 2–5 ч / K = 10 / 0.25 — из головы, калибруются в фазе 7. Стоянка короче цикла —
  осознанно (паузы без торговцев).

## Порядок и задачи

| # | Что | Jira | Где |
|---|---|---|---|
| 1 | Данные: миграция `0024_vendors`, контракты, формула цены, seed, схема в доках | [SCRUM-68](https://fosteev.atlassian.net/browse/SCRUM-68) | vendors |
| 2 | Спавн-цикл торговцев, скрипт, торговцы в `map:entities` | [SCRUM-69](https://fosteev.atlassian.net/browse/SCRUM-69) | vendors |
| 3 | Торговля: get/buy/sell, REST, Swagger, `technical/vendor-trade.md` | [SCRUM-73](https://fosteev.atlassian.net/browse/SCRUM-73) | vendors |
| 4 | Админка: раздел «Торговцы», пул, активные + «Обновить», зона, цена предмета | [SCRUM-74](https://fosteev.atlassian.net/browse/SCRUM-74) | vendors |
| 5 | Flutter: маркер, карточка, экран торговли, анимация сделки, прототип | [SCRUM-70](https://fosteev.atlassian.net/browse/SCRUM-70) | vendors |
| 6 | Арт: `styles/vendor.yaml`, publish, карточки, два торговца | [SCRUM-71](https://fosteev.atlassian.net/browse/SCRUM-71) | vendors |
| 7 | Баланс: `economy.md`, калибровка по TradeLog | [SCRUM-72](https://fosteev.atlassian.net/browse/SCRUM-72) | vendors |

Фазы 1–3 — одна сессия бэкенда подряд; 4 и 5 параллелятся после 3 (контракт зафиксирован в фазе 1); 6 независима
от кода, кроме `publish.mjs` (после фазы 1). Фазу 7 — после SCRUM-62 и реальных данных. Вся тема — после
закрытия items 2–4 ([items/README.md §5](../items/README.md)), чтобы цены сразу были по ilvl.

## Definition of Done

- [ ] Торговцы появляются по cron с шансом на зону, стоят ограниченное время, исчезают из карты по `expires_at`; цикл
      сносит и ставит заново; `npm run vendors:run` и кнопка в админке делают то же.
- [ ] На карте торговец приходит как `type: 'vendor'` с `expiresAt`, виден всем, не персонален.
- [ ] Покупка списывает золото, уменьшает общий сток, кладёт предмет в мешок; продажа начисляет 25 % и убирает
      предмет; все ошибки (`vendor_gone`, `too_far`, `sold_out`, `not_enough_gold`, `bag_full`, `item_equipped`)
      различимы клиентом.
- [ ] Цена считается одной функцией на бэке и в админке; `vendorPrice` перекрывает формулу; sell < buy всегда.
- [ ] Админка: CRUD торговцев со спрайтами idle/deal и пулом, торговцы у зоны, цена у предмета, активные торговцы.
- [ ] Flutter: маркер с таймером, карточка, экран торговли с двумя вкладками, анимация сделки, золото обновляется.
- [ ] `TradeLog` пишется на каждую сделку.
- [ ] Доки: `database-schema.md`, `technical/vendor-trade.md`, `game-design/economy.md`; карточки торговцев.
- [ ] Тесты зелёные: `npx nx run-many -t test`, `flutter analyze && flutter test`, `npx tsc -b --noEmit`.

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy (backend troy-backend, клиент troy-flutter, админка troy-admin,
ассеты troy-assets). Задача: тема vendors — фазы 1–3 из troy-docs/roadmap/vendors/README.md
(данные, спавн-цикл, торговля на бэкенде). Спека и решения там же — не переспрашивать то, что уже
решено (баннер статуса и раздел «Риски»).

Прочитай:
- troy-docs/roadmap/vendors/README.md целиком;
- troy-docs/roadmap/items/README.md §1 и §3 (бюджет статов — основа формулы цены);
- troy-docs/technical/database-schema.md (active_spawns, CharacterKill — образец таблиц вне ORM);
- troy-backend: apps/game-core/src/app/map/spawn-cron.service.ts и map.service.ts (паттерн спавна и
  выдачи карты), battle.service.ts — проверка дистанции (haversine, INTERACTION_RADIUS_M,
  IGNORE_BATTLE_DISTANCE), inventory.service.ts — addItems;
- troy/CLAUDE.md (backend, раздел Testing).

Порядок:
1. Миграция 0024_vendors по §1 (Prisma-модели + raw SQL active_vendors + FK стока); накатывать
   `migrate deploy`, НЕ `migrate dev`. Контракты, env, vendorPrice в libs/shared/utils со spec, seed
   (два торговца, пулы, vendorIds зон, vendorPrice предметов), database-schema.md.
2. VendorCronService.respawn по §2 + admin.vendor.respawn + scripts/vendors-run.ts (npm vendors:run);
   торговцы в MapService.getEntities (type 'vendor', expiresAt); Swagger MapEntityDto.
3. VendorService get/buy/sell/visuals по §3, REST в api-gateway, коды ошибок, technical/vendor-trade.md.

Тесты — часть DoD: spec цены (инвариант sell < buy), cron (шанс, без дубликатов, диапазон expires,
цена), map (вендор в выдаче), VendorService (все ветки ошибок, транзакция buy/sell).

Проверка: `npx nx run-many -t test`; на dev — `npm run vendors:run`, затем сценарий curl из
«Готово, когда» фазы 3.

Ветка main, коммиты без подписей ассистента. По завершении: отметить чекбоксы и DoD здесь,
обновить баннер статуса, таблицу в troy-docs/roadmap/README.md и статусы SCRUM-68/69/73 (скилл troy-jira).
```
