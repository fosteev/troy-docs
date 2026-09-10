# Зоны — раздел управления спаун-зонами в админке

> **Статус: этапы 1–4, 6 и 7 сделаны · 10.09.2026.** Схема, контракты, game-core и api-gateway в
> `troy-backend`, раздел «Зоны» — в `troy-admin`; территория зоны — набор контуров (этап 6), зоны
> генерируются по гексагональной сетке города (этап 7). Дальше этап 5 (доки), после того как
> пользователь пройдёт сценарии «Готово, когда» этапов 4, 6 и 7 на dev. Jira-эпик и задачи заводятся при старте (`/troy-task`, по одной на
> этап 1–4). Исполнитель отмечает чекбоксы по ходу работы.

Сквозная тема: полноценный CRUD зон в админке — территория рисуется на карте, а не в `seed.ts`
raw SQL'ом. Прототип (кликабельный, с реальными координатами сида):
<https://claude.ai/code/artifact/57f61faf-187b-477f-bfba-31276ad43348>.

## Цель

Контент-мейкер заводит зону целиком из админки: имя, тип, уровни, полигон на карте, пул мобов, фон арены,
лимит мобов на неделю — и видит, что respawn её реально заполнил. Ни одной ручной правки БД и сида.

## Контекст и ограничения

Что есть (факты по коду на 10.09):

- `SpawnZone` — `id, name, zoneType: String, monsterIds: String[], minLevel, maxLevel, arenaBackground: Json?`
  (`libs/shared/prisma/schema.prisma`); полигон `geometry GEOMETRY(POLYGON, 4326)` — вне Prisma, создан в
  `0001_init`, GIST-индекс есть. Пишется только в `prisma/seed.ts` через `$executeRaw`.
- Admin API: `GET /admin/spawn/zones` (без geometry), `PUT …/zones/:id/monsters`, `PUT …/zones/:id/arena`,
  `GET /admin/spawn/active` (без `pack_size`, `spawned_at`), `POST /admin/spawn/run`
  (`apps/api-gateway/src/app/admin/admin-spawn.controller.ts`, `apps/game-core/src/app/admin/spawn-admin.*`).
  Создания, удаления, правки имени/уровней/территории нет.
- Respawn (`apps/game-core/src/app/map/spawn-cron.service.ts`): `ZONE_CAPACITY = 8` захардкожен, точки —
  `ST_GeneratePoints(geometry, 1)`; зона без geometry или с пустым spawnable-пулом **молча пропускается**.
- `minLevel/maxLevel` нигде не проверяются — описание для клиента. В сиде два расхождения (Wild Boar 2 ур. в
  Green Forest 3–7, Orc Raider 6 ур. в Ash Ridge 7–10).
- Клиент: `GET /map/zones` отдаёт зоны без geometry; Flutter-репозиторий `getZones` есть, но из bloc не
  вызывается — контракт клиента в этой теме **не меняем**, regen `troy_backend_api` не нужен.
- Админка: `troy-admin/src/pages/spawn/SpawnPage.tsx` — блок «Состав зон» (`ZoneEditor`, `ZoneArenaEditor`)
  и `SpawnMapModal.tsx` (react-leaflet 5, leaflet 1.9.4, только точки спаунов). Тестов в админке нет —
  DoD там `npm run build` + `npm run lint`.
- Смежное в Jira: SCRUM-60 (плотность, `ZONE_CAPACITY` в env), SCRUM-24 (фоны арен трёх зон),
  SCRUM-68 (vendors добавит `SpawnZone.vendorIds`).

Решения (приняты 10.09, обсуждались на прототипе):

1. **Тип зоны — справочник в коде, не enum в БД.** `ZONE_TYPES = ['PLAINS','FOREST','MOUNTAIN','SWAMP','CITY','RUINS']`
   в контрактах, `@IsIn` на входе; колонка остаётся `String`, сид валиден без миграции. Подписи и цвета — в админке.
2. **Два новых поля** — `isActive` (выключенная зона не участвует в respawn и не отдаётся в `/map/zones`) и
   `capacity Int?` (null → env `ZONE_CAPACITY`, default 8). Это закрывает env-часть SCRUM-60; сама плотность —
   отдельно.
3. **Территория ходит как GeoJSON.** Изначально — один `Polygon` без дырок; с этапа 6 это `MultiPolygon`:
   1–32 контура на зону, у каждого один ring, 4–256 позиций, замкнут. На бэке `ST_GeomFromGeoJSON` +
   `ST_IsValid`; `null` снимает территорию целиком. Клиенту geometry по-прежнему не отдаём.
4. **Эндпойнты остаются под `/admin/spawn/zones`** — существующий контроллер и `api/spawn.ts`, меньше churn.
5. **Уровни остаются описательными.** Бэк проверяет только `1 ≤ min ≤ max ≤ 30`; «моб вне диапазона» и
   «выключен глобально» — предупреждения в админке, сохранение не блокируют.
6. **Удаление зоны — транзакция:** её `active_spawns` → их `CharacterKill` → зона. Redis-ключи `spawn:*`
   (TTL 300 с) и кэш карты (30 с) протухают сами.
7. **Рисование — `@geoman-io/leaflet-geoman-free`** поверх уже стоящего leaflet (допущение: совместим с
   react-leaflet 5 / React 19 — проверить первым шагом этапа 4; если нет — свой слой вершин, как в прототипе).
8. Миграция — **`0021_spawn_zone_admin`**. Внимание: `vendors/README.md` планирует `0020_vendors`, но
   `0020` уже занят `item_progression` — vendors берёт следующий свободный номер после этой темы.

## Продуктовый результат

В меню админки появляется «Зоны»: таблица (тип, уровни, пул, спауны недели / лимит, площадь, арена, статус)
и карта с полигонами и спаунами. Drawer зоны с вкладками Основное / Территория / Мобы / Арена / Спауны.
«Спаун» оставляет себе respawn, глобальный флаг «Спаунить» и карту живых спаунов.

## Этапы

### 1. Схема, контракты, env

Поля `isActive`/`capacity`, GeoJSON-тип и справочник типов, NATS-паттерны и payload'ы — всё, от чего зависят
game-core и gateway.

- [x] Миграция `libs/shared/prisma/migrations/0021_spawn_zone_admin/migration.sql` (только `ADD COLUMN`, см. контракт)
- [x] `schema.prisma` → `model SpawnZone`: `isActive Boolean @default(true)`, `capacity Int?`
- [x] `npm run prisma:migrate` (deploy, **не** `migrate dev` — дропнет `active_spawns` и `geometry`) → `npm run prisma:generate`
- [x] `contracts.ts`: `ZONE_TYPES`, `ZoneType`, `GeoJsonPolygon`, расширенный `AdminSpawnZoneDto`, payload'ы
      create / settings / geometry / delete, `AdminActiveSpawnDto` + `packSize`, `spawnedAt`, `kills`, фильтр `zoneId`
- [x] `NATS_PATTERNS`: `ADMIN_SPAWN_ZONE_CREATE`, `ADMIN_SPAWN_ZONE_SETTINGS_UPDATE`, `ADMIN_SPAWN_ZONE_GEOMETRY_UPDATE`,
      `ADMIN_SPAWN_ZONE_DELETE`
- [x] `.env.example`: `ZONE_CAPACITY=8` с комментарием (дефолт для зон с `capacity = null`)
- [x] `technical/database-schema.md` → SpawnZone: добавить `arenaBackground` (в таблице его нет), `isActive`, `capacity`, формат geometry

**Готово, когда:** `npm run prisma:migrate && npm run prisma:generate` на dev проходят, `npm run build` зелёный,
`SELECT "isActive", capacity FROM "SpawnZone"` отдаёт `true, null` для трёх зон сида.

### 2. game-core — CRUD зон, геометрия, спауны зоны, respawn по новым полям

Вся логика в `apps/game-core/src/app/admin/spawn-admin.service.ts` + правки cron и map.

- [x] `listZones` → `$queryRaw`: все поля + `ST_AsGeoJSON(geometry)::json AS geometry` + `spawnsAlive` (подзапрос по `active_spawns`, `::int`)
- [x] `createZone(payload)`: валидация типа (`ZONE_TYPES`), уровней, `capacity ≥ 0`; `monsterIds` по умолчанию `[]`, geometry `NULL`
- [x] `updateZoneSettings(payload)`: name / zoneType / minLevel / maxLevel / capacity / isActive; P2025 → 404 как в `updateZone`
- [x] `updateZoneGeometry(payload)`: структурная проверка GeoJSON в TS → `ST_IsValid` в SQL → `UPDATE … ST_SetSRID(ST_GeomFromGeoJSON(...), 4326)`; `null` → `geometry = NULL`; невалидно → 400 `GEOMETRY_INVALID`
- [x] `deleteZone(id)`: `$transaction` — `DELETE FROM active_spawns WHERE spawn_zone_id = $1 RETURNING id` → `characterKill.deleteMany({ spawnId: { in } })` → `spawnZone.delete`; ответ `{ id, spawnsRemoved }`
- [x] `listActiveSpawns(filter)`: `WHERE ($zoneId IS NULL OR spawn_zone_id = $zoneId)`, поля `pack_size AS "packSize"`, `spawned_at AS "spawnedAt"`, `kills` — count `CharacterKill` по `spawnId` с `killedAt >= currentWeekStart()`
- [x] `spawn-cron.service.ts`: `findMany({ where: { isActive: true } })`, лимит `zone.capacity ?? Number(process.env.ZONE_CAPACITY) || 8`
- [x] `map.service.ts` `getZones`: `AND z."isActive" = TRUE`
- [x] `spawn-admin.controller.ts`: четыре новых `@MessagePattern`, `ADMIN_SPAWN_ACTIVE_LIST` принимает payload с `zoneId?`
- [x] Спеки: `spawn-admin.service.spec.ts` (create-валидация, geometry: незамкнутый ring / 3 точки / 257 точек / `ST_IsValid=false` → 400, `null` снимает, delete — порядок трёх операций, list маппит geometry и `spawnsAlive`), `spawn-cron.service.spec.ts` (неактивная зона пропущена; `capacity` зоны важнее env; env важнее 8), `map.service.spec.ts` (`isActive` в SQL)

**Готово, когда:** `npx nx test game-core` зелёный; на dev `scripts/spawn-run.ts` после создания зоны с полигоном
и пулом кладёт в неё ровно `capacity` спаунов внутри полигона (проверка:
`SELECT count(*) FROM active_spawns s JOIN "SpawnZone" z ON z.id = s.spawn_zone_id WHERE z.name = '…' AND ST_Contains(z.geometry, s.location::geometry)`).

### 3. api-gateway — REST и Swagger

Проброс в NATS по образцу `admin-spawn.controller.ts`, валидация — class-validator в `dto/admin/spawn.dto.ts`.

- [x] `CreateZoneDto`, `UpdateZoneSettingsDto` (все поля опциональны, `@IsIn(ZONE_TYPES)`, `@Min(1) @Max(30)`, `capacity @Min(0) @Max(64)`), `UpdateZoneGeometryDto` (`geometry: GeoJsonPolygonDto | null`, `@ValidateNested`), `AdminSpawnZoneResponseDto` + новые поля, `ZoneDeleteResultDto`, `ActiveSpawnsQueryDto` (`zoneId?: uuid`)
- [x] `AdminSpawnController`: `POST zones`, `PUT zones/:id`, `PUT zones/:id/geometry`, `DELETE zones/:id`, `GET active?zoneId=`
- [x] Swagger: `@ApiDataResponse` на всех, пример GeoJSON в `@ApiProperty({ example })`

**Готово, когда:** `npx nx test api-gateway` и `npm run build` зелёные; через Swagger `/api` под admin-токеном
проходит цепочка create → geometry → monsters → `POST /admin/spawn/run` → `GET active?zoneId=` отдаёт спауны
только этой зоны; `PUT geometry` с незамкнутым ring → 400 `GEOMETRY_INVALID`; `DELETE` → 200 и
`GET active?zoneId=` пуст.

### 4. Админка — раздел «Зоны»

`troy-admin`, по образцу `pages/monsters/*` (страница + панели), карта — react-leaflet как в `SpawnMapModal`.

- [x] Проверить `@geoman-io/leaflet-geoman-free` с leaflet 1.9.4 / react-leaflet 5 / React 19 (`npm i --save-exact`, `import '…/dist/leaflet-geoman.css'`, `map.pm.addControls` внутри `useMap()`); при конфликте — свой слой вершин
- [x] `src/api/spawn.ts`: `SpawnZone` + `geometry | null`, `isActive`, `capacity | null`, `spawnsAlive`; `createZone`, `updateZoneSettings`, `updateZoneGeometry`, `deleteZone`, `listActiveSpawns({ zoneId? })` с `packSize/spawnedAt/kills`
- [x] `src/pages/zones/zoneTypes.ts` — подпись и цвет на `ZoneType` (PLAINS янтарь, FOREST зелёный, MOUNTAIN фиолетовый, SWAMP бирюза, CITY бордо, RUINS охра)
- [x] `ZonesPage.tsx`: шапка (заголовок, «Перезапустить спаун» с `Popconfirm`, «Новая зона»), четыре `Statistic` (зон спаунится / спауны недели из лимита / площадь / следующая среда 00:00 UTC), таблица (тип, уровни, мобы + бейдж предупреждений, спауны/лимит с `Progress`, площадь км², арена, статус, «Открыть»), клик по строке подсвечивает полигон
- [x] `ZonesMap.tsx`: `MapContainer` + `<Polygon>` на зону (цвет типа, выключенная — пунктир) + `CircleMarker` спаунов с бейджем `×N` при `packSize > 1`, тултип (моб, уровень, зона, координаты, убит N)
- [x] `ZoneDrawer.tsx` (`Drawer` 780px, `Tabs`): **Основное** — форма name / type `Select` / min / max / capacity (плейсхолдер «по умолчанию 8») / `Switch` isActive, блок удаления с `Popconfirm` (текст: сколько спаунов исчезнет); **Территория** — карта с geoman (draw / edit / clear), площадь и периметр (формула из прототипа), `TextArea` с GeoJSON read-only, пустое состояние «Территории нет — respawn пропускает зону»; **Мобы** — перенесённый `ZoneEditor` (чекбоксы + уровень + `пак a–b`, предупреждения «N ур. вне min–max», «выключен глобально»); **Арена** — перенесённый `ZoneArenaEditor` без изменений; **Спауны** — таблица `listActiveSpawns({ zoneId })`: моб, пак, координаты, убит
- [x] Создание: drawer в режиме «Новая зона», вкладки кроме «Основное» disabled до первого сохранения; после `createZone` — переключить на «Территория»
- [x] `App.tsx` роут `zones`, `AdminLayout.tsx` пункт меню «Зоны» (`BorderOuterOutlined`) и `selectedKey`
- [x] `SpawnPage.tsx`: убрать блок «Состав зон» и импорты `listZones/updateZoneMonsters/updateZoneArena`; вместо него строка-подсказка со ссылкой на `/zones`
- [x] `README.md` админки: структура `pages/zones/`, новая зависимость

**Готово, когда:** `npm run build` и `npm run lint` чистые; на dev: нарисовал полигон → сохранил → «Перезапустить
спаун» → на вкладке «Спауны» и на карте ровно `capacity` точек внутри полигона; выключил зону → после respawn
её спаунов нет; удалил зону → пропала из таблицы и с карты, `GET /map/zones` рядом с ней пуст.

### 5. Доки и закрытие

- [ ] `troy/CLAUDE.md`: пункты 3–4 «Key design decisions» (geometry теперь пишется и через admin API), описание `spawn` в архитектуре (`capacity` на зону, `isActive`), env `ZONE_CAPACITY`
- [ ] `roadmap/README.md`: галочка/баннер темы, SCRUM-60 — отметить env-часть закрытой в `mvp-4-content-balance/README.md`
- [ ] `vendors/README.md`: номер миграции → следующий свободный после `0021`
- [ ] Коммиты в стиле репозиториев: `zones: …` (backend, admin), `zones: …` (docs); Jira — статусы и worklog через `/troy-continue`

**Готово, когда:** чекбоксы этапов 1–4 закрыты, баннер темы обновлён, пользователь прошёл сценарий из
этапа 4 на dev.

### 6. Много контуров на одну зону

Доработка после этапа 4: настройки зоны (имя, тип, уровни, пул мобов, лимит) остаются одни, а территория
становится набором независимых контуров. Причина — «одна зона = один полигон» вынуждало плодить зоны-клоны
ради нескольких пятен на карте.

- [x] Миграция `0022_zone_multipolygon`: `ALTER COLUMN geometry TYPE geometry(MultiPolygon, 4326) USING ST_Multi(geometry)`
      (GIST-индекс Postgres перестраивает сам, NULL остаётся NULL)
- [x] `contracts.ts`: `GeoJsonPolygon` → `GeoJsonMultiPolygon`, константа `ZONE_GEOMETRY_MAX_POLYGONS = 32`
- [x] `spawn-admin.service.ts`: `serializeMultiPolygon` (1–32 контура, у каждого один ring 4–256 позиций),
      запись через `ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(...), 4326))`
- [x] Гейтвей: `GeoJsonMultiPolygonDto`, пример в Swagger — два контура
- [x] `prisma/seed.ts`: три прямоугольника заворачиваются в `ST_Multi(...)`
- [x] Спеки: контуры сохраняются целиком, отбой на «ни одного контура», «33 контура», «одиночный Polygon»
- [x] Админка: `geo.ts` считает площадь/периметр/вершины по всем контурам, вкладка «Территория» — кнопка
      «Добавить контур», таблица контуров (площадь, вершины, центр, «Показать», удалить), карта зоны
      рисует все контуры одним слоем
- [x] `technical/database-schema.md` → SpawnZone: тип колонки, потолки, как respawn делит лимит

**Готово, когда:** `npm run prisma:migrate` на dev проходит, `npx nx run-many -t test` и обе сборки зелёные;
в админке к зоне добавляются два контура, после «Перезапустить спаун» точки лежат в обоих
(`SELECT ST_NumGeometries(geometry) FROM "SpawnZone"` > 1, все спауны внутри `ST_Contains`).

Чего в бэке править **не** пришлось: `ST_GeneratePoints(geometry, 1)` в respawn сам работает по
мультиполигону и распределяет точки пропорционально площади контуров, `ST_DWithin` в `/map/zones` и
`ST_Contains` в проверках — тоже.

### 7. Раскладка территорий по гексагональной сетке города

Руками обвести весь город невозможно, поэтому территории раскладываются генератором: граница города
режется сотами, каждой зоне достаётся свой центр, сота уходит ближайшему центру, соты одного центра
склеиваются в территорию. Соты — шестиугольники (правильные восьмиугольники плоскость не замащивают).

**Зоны генератор не создаёт и не удаляет.** Имена, типы, уровни, пул мобов, фон арены и лимит спаунов —
это настроенная руками сущность; переписывается только `geometry`. `seed` решает, какой зоне какой кусок
города достанется.

- [x] `POST /admin/spawn/zones/generate` (`GenerateZonesDto` — `boundary`, `hexSizeMeters`, `seed?`,
      `dryRun?`), NATS `admin.spawn.zone.generate`
- [x] Шаг 1 — соты: `ST_HexagonGrid` в UTM-проекции (в 3857 «сота 400 м» на широте Москвы вышла бы 225 м),
      наружу отдаются только центры
- [x] Шаг 2 — раздача в TS: центры зон через farthest-point sampling (случайные точки сбивались бы
      в кучки), сота уходит ближайшему центру, порядок зон тасуется seed'ом
- [x] Шаг 3 — `ST_Union` сот каждой зоны обратно в БД, `UPDATE … geometry` в транзакции
- [x] Анклавы: кусок зоны, со всех сторон окружённый одной чужой зоной, отдаётся ей ещё до объединения —
      иначе объединение соседа получало дырку, её приходилось срезать, и зоны накладывались друг на друга.
      Соту-центр не отдаём, чтобы зона не осталась вовсе без территории
- [x] Соседство сот считается по шагу сетки из самих центров, а не по `hexSizeMeters`
- [x] Ограничения: ребро соты 100–5000 м, потолок 20 000 сот (`HEX_GRID_TOO_LARGE`), сот не меньше, чем
      зон (`NOT_ENOUGH_CELLS`), хотя бы одна зона (`NO_ZONES`), сложность результата — `ZONE_TOO_COMPLEX` /
      `ZONE_TOO_FRAGMENTED`
- [x] Спеки: dryRun не пишет, состав зон не меняется, зона без сот получает `geometry: null`, срез дырок,
      поглощение анклава и защита соты-центра, отбой по каждому коду
- [x] Админка: кнопка «Разложить территории», модалка с обводкой границы (или прямоугольником по виду
      карты), ребром соты, seed'ом с «Перемешать», превью на карте и таблицей по зонам
- [x] `TerritoryEditor` вынесен из `ZoneTerritoryPanel` — общий слой рисования для территории и границы

**Готово, когда:** `npx nx run-many -t test` и обе сборки зелёные; на dev превью режет обведённый город
на столько частей, сколько заведено зон, зоны не накладываются друг на друга, применение переписывает
территории, а список зон остаётся прежним; после «Перезапустить спаун» точки лежат внутри новых территорий.

Почему не Вороной по точкам: у сот вершин единицы, а у ячейки Вороного, обрезанной по извилистой
границе, — сотни, и они упираются в потолок 256 вершин на контур. Раздача «ближайший центр» поверх сот
даёт ту же мозаику, но с дешёвой геометрией.

## Контракт и точки входа

### Миграция и схема

```sql
-- Зоны из админки (roadmap/zones). Только ADD COLUMN; накат — prisma migrate deploy.
ALTER TABLE "SpawnZone"
  ADD COLUMN "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN "capacity" INTEGER;
```

```prisma
  isActive   Boolean  @default(true)
  // null → env ZONE_CAPACITY (default 8): сколько спаунов respawn кладёт в зону на неделю.
  capacity   Int?
```

### Контракты (`libs/shared/contracts/src/lib/contracts.ts`)

```ts
export const ZONE_TYPES = ['PLAINS', 'FOREST', 'MOUNTAIN', 'SWAMP', 'CITY', 'RUINS'] as const;
export type ZoneType = (typeof ZONE_TYPES)[number];
export const ZONE_GEOMETRY_MAX_VERTICES = 256;

export const ZONE_GEOMETRY_MAX_POLYGONS = 32;

/** Территория зоны: контуры, у каждого один ring без дырок, [lng, lat], первая точка = последняя. */
export interface GeoJsonMultiPolygon { type: 'MultiPolygon'; coordinates: [number, number][][][]; }

export interface AdminSpawnZoneDto {
  id: string; name: string; zoneType: string; minLevel: number; maxLevel: number;
  monsterIds: string[]; arenaBackground: ClassSpriteSheet | null;
  isActive: boolean; capacity: number | null;
  geometry: GeoJsonMultiPolygon | null;
  /** Живых спаунов зоны сейчас (active_spawns.alive). */
  spawnsAlive: number;
}
export interface AdminSpawnZoneCreatePayload { name: string; zoneType: ZoneType; minLevel: number; maxLevel: number; capacity?: number | null; isActive?: boolean; }
export interface AdminSpawnZoneSettingsPayload { id: string; name?: string; zoneType?: ZoneType; minLevel?: number; maxLevel?: number; capacity?: number | null; isActive?: boolean; }
export interface AdminSpawnZoneGeometryPayload { id: string; geometry: GeoJsonMultiPolygon | null; }
export interface AdminSpawnZoneDeletePayload { id: string; }
export interface AdminSpawnZoneDeleteResult { id: string; spawnsRemoved: number; }
export interface AdminActiveSpawnListPayload { zoneId?: string; }
// AdminActiveSpawnDto += packSize: number; spawnedAt: string; kills: number;
```

Паттерны: `admin.spawn.zone.create`, `admin.spawn.zone.settings.update`, `admin.spawn.zone.geometry.update`,
`admin.spawn.zone.delete`. Существующие `admin.spawn.zone.update` (мобы) и `…arena.update` не трогаем.

### REST (`/admin/spawn`, `GatewayJwtGuard + AdminGuard`)

| Метод | Путь | Тело / query | Ответ |
|---|---|---|---|
| GET | `zones` | — | `AdminSpawnZoneDto[]` (теперь с `geometry`, `spawnsAlive`) |
| POST | `zones` | `CreateZoneDto` | `AdminSpawnZoneDto` |
| PUT | `zones/:id` | `UpdateZoneSettingsDto` | `AdminSpawnZoneDto` |
| PUT | `zones/:id/geometry` | `{ geometry: GeoJsonMultiPolygon \| null }` | `AdminSpawnZoneDto` · 400 `GEOMETRY_INVALID` |
| DELETE | `zones/:id` | — | `{ id, spawnsRemoved }` |
| GET | `active` | `?zoneId=uuid` | `AdminActiveSpawnDto[]` с `packSize`, `spawnedAt`, `kills` |

Ошибки 400 в стиле `LEVEL_TOO_LOW`: `ZONE_TYPE_UNKNOWN`, `LEVEL_RANGE_INVALID` (`1 ≤ min ≤ max ≤ 30`),
`CAPACITY_INVALID` (`0 ≤ capacity ≤ 64`), `GEOMETRY_INVALID`. Несуществующая зона — 404
`Spawn zone not found` (как сейчас).

Как это вышло в коде (этапы 1–3, факты для админки):

- `capacity` — целое `0..64` (`ZONE_CAPACITY_MAX` в контрактах) либо `null` («по умолчанию 8»);
  `capacity: 0` — легальная «зона без спаунов». Тот же потолок зажимает и env `ZONE_CAPACITY`.
- `PUT zones/:id/geometry` требует ключ `geometry` в теле: `null` снимает территорию, отсутствие ключа — 400.
  Порядок проверок: структура в TS → `ST_IsValid` в PostGIS. Самопересекающийся полигон отсекается вторым шагом.
- Все мутации зоны (`monsters`, `arena`, `settings`, `geometry`) возвращают полный `AdminSpawnZoneDto` —
  с `geometry`, `isActive`, `capacity` и `spawnsAlive`, так что после сохранения строку таблицы можно
  обновлять ответом, без повторного `listZones`.
- `GET active` без `zoneId` ведёт себя как раньше (все живые спауны), с `zoneId` — только спауны зоны.
- Выключение зоны прячет её из `/map/zones` сразу, но её спауны живут на карте до ближайшего respawn:
  `/map/entities` по `isActive` не фильтруется (так и задумано — мир фиксирован на неделю).

Как это вышло в коде (этап 4, админка):

- Гейтвей валидирует с `forbidNonWhitelisted: true` — форма зоны отправляет ровно поля DTO, а не весь
  `SpawnZone` из ответа; лишний ключ (`id`, `geometry`, `spawnsAlive`) вернул бы 400.
- Территория — набор контуров (этап 6): каждый контур на карте живёт отдельным leaflet-слоем со своим
  geoman-редактированием, а в состояние собирается один MultiPolygon по всем слоям. Удаление контура — из
  таблицы под картой, не из geoman. Пересечение контуров между собой отбивает `ST_IsValid`, и админка
  переводит `GEOMETRY_INVALID` в человеческий текст.
- Единой кнопки «Сохранить» у зоны нет: у каждой вкладки свой эндпойнт, поэтому и своя кнопка
  (Основное → `POST`/`PUT zones/:id`, Территория → `PUT …/geometry`, Мобы → `PUT …/monsters`,
  Арена → `PUT …/arena`). Ответ мутации кладётся в состояние drawer'а и оказывается свежее списка.
- Слой полигона на карте пересобирается только по команде (нарисовать / очистить / отменить / после
  сохранения), а не на каждую правку вершины — иначе `setLatLngs` из React сбивал бы маркеры geoman.
- Правки вершин уходят в состояние через `pm:edit` на слое; координаты округляются до 6 знаков (~11 см).
- Площадь и периметр считаются на клиенте равнопромежуточной проекцией вокруг центра полигона —
  бэк их не отдаёт, а для зон в километрах погрешность меньше точности рисования.
- Ограничения формы совпадают с DTO: уровни 1–30 и `max ≥ min`, `capacity` 0–64 либо пусто
  («по умолчанию 8»). Структура GeoJSON проверяется перед отправкой, самопересечение не даёт нарисовать
  сам geoman (`allowSelfIntersection: false`), `ST_IsValid` остаётся последней линией.
- `eslint-plugin-react-hooks 7` запрещает `setState` в эффекте, поэтому состояние drawer'а (какая зона,
  какая вкладка) живёт на `ZonesPage` и меняется в обработчиках, а не синхронизируется эффектом.

### Геометрия в SQL

```sql
-- чтение (listZones)
SELECT z.id, z.name, z."zoneType", z."minLevel", z."maxLevel", z."monsterIds", z."arenaBackground",
       z."isActive", z.capacity,
       ST_AsGeoJSON(z.geometry)::json AS geometry,
       (SELECT count(*)::int FROM active_spawns s WHERE s.spawn_zone_id = z.id AND s.alive) AS "spawnsAlive"
FROM "SpawnZone" z ORDER BY z.name ASC;

-- проверка перед записью (после структурной проверки в TS)
SELECT ST_IsValid(ST_GeomFromGeoJSON(${json})) AS valid;

-- запись
UPDATE "SpawnZone" SET geometry = ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(${json}), 4326)) WHERE id = ${id}::uuid;
```

Структурная проверка в TS: `type === 'MultiPolygon'`, 1–32 контура, у каждого ровно один ring,
4–256 позиций, каждая `[lng, lat]` в диапазоне, первая равна последней. Пересечение контуров между
собой ловит уже `ST_IsValid` — для MultiPolygon он требует, чтобы внутренности частей не пересекались.

### Что не тащим

- Веса мобов и фиксированные слоты («босс раз в неделю») — MVP-4, поле появится там.
- Дырки и мультиполигоны, проверка пересечения зон.
- Полигоны на клиенте, ambient и фон по типу зоны — P2/MVP-5.
- Вкладка «Торговцы» — vendors (SCRUM-68), зеркало «Мобов».

## Риски и открытые вопросы

- ~~**Бой и удалённый спаун.**~~ Проверено в этапе 2: `active_spawns` читает только `loadAliveSpawn`, и только
  из `battle.start`; дальше сессия живёт в Redis, а `CharacterKill.spawnId` — UUID без FK. Удаление зоны с идущим
  боем безопасно, `ZONE_HAS_SPAWNS` не понадобился.
- ~~**geoman и React 19.**~~ Проверено в этапе 4: `@geoman-io/leaflet-geoman-free@2.20.0` объявляет peer только
  `leaflet ^1.2.0`, React ему безразличен, а d.ts вдобавок augment'ит `LeafletEventHandlerFnMap` — `pm:*`
  типизируются и в react-leaflet. Своего слоя вершин не понадобилось. Цена — отдельный чанк 274 КБ (72 КБ gzip),
  подтягивается только на роуте `/zones`.
- ~~**`$queryRaw` и `::json`.**~~ На dev-БД `ST_AsGeoJSON(...)::json` приходит объектом; `JSON.parse`-ветка в
  маппере на случай строки всё равно оставлена и покрыта спекой.
- **Полигон за пределами тайлов админ-карты** — не риск для бэка; на карте админки OSM-тайлы онлайн, ограничений нет.
- **Вопрос пользователю:** чинить ли два расхождения уровней в сиде (Wild Boar, Orc Raider) — по плану оставляем
  как есть до MVP-4, админка их покажет предупреждением.

## Порядок работы

1. Завести эпик «zones» и задачи по этапам 1–4 через `/troy-task` (этап 5 — хвост последней).
2. Этап 1 → 2 → 3 строго последовательно (каждый зависит от контрактов и Prisma-клиента предыдущего); это одна
   сессия исполнителя на `troy-backend`.
3. Этап 4 можно начинать параллельно с 3 на моках `api/spawn.ts` (форма и карта не зависят от гейтвея), но
   DoD этапа 4 проверяется только против живого API.
4. Этап 5 — после проверки сценария пользователем на dev.

## Промт для сессии

```
Проект Troy, троевой воркспейс /Users/fost/Projects/troy. Прочитай troy/CLAUDE.md, затем
troy-docs/roadmap/zones/README.md целиком — это план и контракт. Делай этапы 1–3 в troy-backend по
разделу «Контракт и точки входа», отмечая чекбоксы в README темы по ходу.

Правила: миграции только `npm run prisma:migrate` (deploy) — `migrate dev` дропает active_spawns и
SpawnZone.geometry; зависимости пинить точно; существующие паттерны admin.spawn.zone.update /
arena.update не переименовывать; клиентский контракт /map/zones не менять. Тесты — Jest, спеки рядом
с сервисами (эталон: apps/game-core/src/app/admin/spawn-admin.service.spec.ts, map/spawn-cron.service.spec.ts).

DoD: `npx nx run-many -t test` и `npm run build` зелёные; через Swagger под admin-токеном проходит
create → geometry → monsters → POST /admin/spawn/run → GET active?zoneId= с точками внутри полигона;
невалидный GeoJSON → 400 GEOMETRY_INVALID. Коммит в стиле истории: `zones: …`, без подписей ассистента.
В конце — список открытых вопросов и что не удалось проверить без живой БД.
```

```
Проект Troy, админка troy-admin (Vite + React 19 + antd 6 + react-leaflet 5). Прочитай troy-admin/README.md
и troy-docs/roadmap/zones/README.md — этап 4 и раздел «Контракт и точки входа» (REST + блок «Как это
вышло в коде»). Бэкенд этапов 1–3 готов и смержен в troy-backend (main): миграция 0021, все эндпойнты
/admin/spawn/zones живые. Прототип раздела:
https://claude.ai/code/artifact/57f61faf-187b-477f-bfba-31276ad43348 — делать по нему, компоненты
antd, стиль как у pages/monsters. Отмечай чекбоксы этапа 4 в README темы.

Первый шаг — проверить @geoman-io/leaflet-geoman-free с текущим leaflet/react-leaflet/React 19;
если конфликт — свой слой вершин на leaflet без плагина. Зависимости пинить точно (.npmrc save-exact).
Перенести ZoneEditor/ZoneArenaEditor из SpawnPage в pages/zones, из SpawnPage блок «Состав зон» убрать.

DoD: `npm run build` и `npm run lint` чистые; описать сценарий проверки на dev из «Готово, когда» этапа 4
для пользователя. Коммит `zones: …` без подписей ассистента.
```
