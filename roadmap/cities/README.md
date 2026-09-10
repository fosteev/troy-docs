# Города, зоны, территории — новая модель мира

> **Статус: этап 4 (админка) сделан 10.09.2026 на моках контракта, бэкенд (этапы 1–3) не начат.**
> Заменяет геометрическую часть темы [zones/](../zones/README.md) (этапы 6–7: MultiPolygon на зоне и
> генератор сот). Разделы «Зоны» и «Спаун» в админке остаются, добавляется «Города». Админка собрана
> строго по разделу «Контракт и точки входа» и против живого API **не проверялась** — сценарий из
> «Готово, когда» этапа 4 прогоняется после этапов 1–3. Jira-эпик и задачи — при старте (`/troy-task`).
> Исполнитель отмечает чекбоксы по ходу.

Прототип (кликабельный: граница, разбиение на соты, раздача зон, кисть, drawer зоны):
<https://claude.ai/code/artifact/b47f545b-531b-4aee-81f4-a5a4316479f9>, исходник —
[design/prototypes/admin-cities-territories.html](../../design/prototypes/admin-cities-territories.html).
Старый прототип «Зоны» (территория на зоне) — <https://claude.ai/code/artifact/57f61faf-187b-477f-bfba-31276ad43348>,
по нему собран текущий раздел.

## Модель

Три уровня, сверху вниз:

| Сущность | Что это | Где заводится | Геометрия |
|---|---|---|---|
| **Город** (`City`) | Граница мира. Внутри неё есть мобы, снаружи — нет. Ребро соты, флаг «спаунить» | Админка → «Города»: карточка, потом граница обводится на карте (или «по радиусу» от центра) | `boundary` MultiPolygon |
| **Зона** (`SpawnZone`) | Логическая единица: имя, тип, уровни, пул мобов, фон арены, лимит спаунов на соту | `prisma/seed.ts`; правится в админке → «Зоны» | **нет** |
| **Территория** (`Territory`) | Сота гексагональной сетки города. Единственное свойство — зона (или пусто). В ней спаунятся мобы | Генератор города («Разбить на соты»), зона — раздачей или кистью | `geometry` Polygon (шестиугольник) |

```
City ──1:N── Territory ──N:1── SpawnZone
                 │
                 └──1:N── active_spawns (territory_id, spawn_zone_id)
```

Что из этого следует:

- **Зона может жить в нескольких городах** и в нескольких несвязных пятнах одного города — просто набор
  сот. Зона без сот — в резерве, ничего не ломает.
- **Территория без зоны — пустошь**: respawn её пропускает, клиент ничего в ней не видит.
- **Лимит спаунов считается на соту**, а не на зону: `SpawnZone.capacity` = «спаунов на соту в неделю»,
  `null` → env `TERRITORY_CAPACITY` (default 2). Плотность мобов задаётся ребром соты города и лимитом зоны;
  общий объём — числом сот. Это закрывает SCRUM-60 (плотность) целиком.
- **Мир по-прежнему фиксирован на неделю**: respawn в среду 00:00 UTC сносит спауны всех городов и
  раскладывает заново по сотам; `CharacterKill` и персональная видимость не меняются.

## Контекст: что есть сейчас (факты по коду на 10.09)

- `SpawnZone` несёт `geometry GEOMETRY(MULTIPOLYGON, 4326)` вне Prisma (миграции `0001`, `0022`), пишется
  из админки (`PUT /admin/spawn/zones/:id/geometry`), сида (`ST_MakeEnvelope` × 18 прямоугольников) и
  генератора `POST /admin/spawn/zones/generate` (`ST_HexagonGrid` в UTM → farthest-point centers →
  ближайший центр → анклавы → `ST_Union` по зоне). См. [zones/README.md](../zones/README.md), этапы 6–7.
- Respawn (`apps/game-core/src/app/map/spawn-cron.service.ts`): по активным зонам, `capacity ?? ZONE_CAPACITY ?? 8`
  точек через `ST_GeneratePoints(geometry, 1)` на всю территорию зоны.
- `active_spawns(id, monster_id, spawn_zone_id, location, spawned_at, alive, pack_size)` — вне Prisma.
- Клиент: `GET /map/zones` (зоны рядом, без geometry), `GET /map/entities`, WS `map:request`. Flutter
  `getZones` из bloc не вызывается.
- Админка: `troy-admin/src/pages/zones/*` — `ZonesPage`, `ZoneDrawer` (Основное / Территория / Мобы / Арена /
  Спауны), `TerritoryEditor` (geoman), `ZonesGenerateModal`, `ZonesMap`, `geo.ts`. «Спаун» — respawn и карта
  живых спаунов.

## Решения (10.09, по прототипу)

1. **Геометрия уходит с зоны.** `SpawnZone.geometry` дропается, `PUT zones/:id/geometry` и
   `POST zones/generate` удаляются вместе с `TerritoryEditor` в drawer'е зоны. Зона — чистый справочник.
2. **Город = граница + ребро соты.** `City.boundary` — MultiPolygon в тех же рамках, что была территория
   зоны (1–32 контура, ≤ 256 вершин, `ST_IsValid`); `hexSizeMeters` 100–5000; `isActive`. «По радиусу» —
   инструмент рисования в админке (центр + радиус → 32-угольник), в БД это обычный контур.
3. **Территория = сота, а не произвольный полигон.** `Territory` создаётся только генератором
   («Разбить на соты»), руками не рисуется. Сота остаётся, если её центр внутри границы (не режем по краю —
   иначе краевые «соты» превращаются в осколки). Ключ — `(cityId, hexI, hexJ)` из `ST_HexagonGrid`.
4. **Раздача зон — тот же алгоритм этапа 7, но пишет `Territory.zoneId`, а не `ST_Union` в зону.**
   Состав зон города выбирается чеклистом в модалке (по умолчанию все активные), seed, dryRun-превью,
   правило анклавов остаётся. Поверх — **кисть**: клик/протяжка по сотам красит их выбранной зоной или
   «без зоны», сохраняется батчем.
5. **Перерезка стирает раздачу.** Смена ребра соты или границы удаляет территории (и их спауны) и режет
   заново; новые соты — без зоны. Это транзакция с подтверждением в админке. Ручная покраска при этом
   теряется — осознанно: соты другого размера не совпадают со старыми.
6. **`active_spawns.territory_id`** добавляется рядом с `spawn_zone_id` (денормализация: бой берёт
   арену и пул по зоне, не хочется join'а через соту). Удаление территории/города — каскадом на спауны и
   их `CharacterKill` в транзакции, как сейчас при удалении зоны.
7. **Клиентский контракт не меняется.** `GET /map/zones` отдаёт зоны, у которых есть сота в радиусе
   (`Territory JOIN SpawnZone`, без geometry); `/map/entities` как был. Полигоны сот клиенту и
   `GET /map/cities` (центр/bbox для «вы вне мира») — следующий шаг, в этой теме не делаем.
8. **Общая чистая функция раздачи** (`farthest-point` + `nearest` + анклавы) выносится в
   `libs/shared/utils/hex-assign.ts`, чтобы seed и game-core считали одинаково.
9. **Seed заводит зоны без геометрии и один dev-город** «Moscow Dev»: граница — прямоугольник старой
   сетки (`37.55–37.67, 55.70–55.736`), ребро 250 м, разбиение SQL'ом (`ST_HexagonGrid`), раздача всех
   активных зон через `hex-assign` с seed 4242. Так `spawn:run` и тесты работают из коробки.
10. **Миграция `0023_cities_territories`** — только DDL; данные территорий не мигрируются (dev), после
    наката — `npm run prisma:seed`. `vendors/README.md` берёт следующий номер после `0023`.
11. **Env:** `TERRITORY_CAPACITY=2` вместо `ZONE_CAPACITY=8`; `ZONE_GENERATE_*` константы переезжают в
    `CITY_HEX_*` (100–5000 м, потолок 20 000 сот на город).

## Продуктовый результат

В меню админки блок «Мир»: **Города** (new), **Зоны**, **Спаун**.

- **Города** — таблица (статус, площадь, ребро, территорий с зоной / всего, зон, спаунов в неделю) и
  карточка с вкладками **Основное** (имя, ребро, «спаунить», seed, центр, удаление) /
  **Граница** (обвести, по радиусу, очистить; вершины, площадь, оценка числа сот; «Разбить на соты») /
  **Территории** (карта сот; инструменты «выбор» и «кисть»; раскраска по зоне / типу / уровню;
  переключатель спаунов; легенда-кисть с «без зоны»; карточка выбранной соты с select зоны;
  «Раздать зоны» (модалка: чеклист зон, seed, «Перемешать»); «Перерезать соты»; «Сохранить раздачу») /
  **Спауны** (живые спауны города).
- **Зоны** — таблица (тип, уровни, мобы с предупреждением, лимит на соту, территорий · города, арена,
  статус), drawer **Основное / Мобы / Арена / Где на карте** (read-only список городов со ссылкой на
  карту). Вкладка «Территория» и кнопка «Разложить территории» уходят.
- **Спаун** — как сейчас, плюс таблица последнего прогона по городам с причиной пропуска
  (нет границы / не разбит / выключен / нет сот с зоной).

## Этапы

### 1. Схема, контракты, env

- [ ] Миграция `libs/shared/prisma/migrations/0023_cities_territories/migration.sql` (см. контракт):
      `City`, `Territory`, `boundary`/`geometry` raw-колонки + GIST, `active_spawns.territory_id`,
      `DROP COLUMN "SpawnZone".geometry`
- [ ] `schema.prisma`: `model City`, `model Territory` (без geo-колонок), `SpawnZone` без изменений полей
      (комментарий у `capacity` — «на соту»)
- [ ] `npm run prisma:migrate` (deploy, **не** `migrate dev`) → `npm run prisma:generate` → `npm run prisma:seed`
- [ ] `contracts.ts`: `CITY_HEX_MIN_METERS/MAX_METERS/MAX_CELLS`, `AdminCityDto`, `AdminTerritoryDto`,
      payload'ы create / settings / boundary / split / assign / paint / delete, `AdminActiveSpawnListPayload += cityId?`,
      `AdminActiveSpawnDto += territoryId`; удалить `AdminSpawnZoneGeometryPayload`, `AdminSpawnZoneGeneratePayload/Result`,
      `ZONE_GENERATE_*`, `AdminSpawnZoneDto.geometry`
- [ ] `NATS_PATTERNS`: `ADMIN_CITY_LIST/CREATE/SETTINGS_UPDATE/BOUNDARY_UPDATE/DELETE`,
      `ADMIN_CITY_TERRITORIES_LIST/SPLIT/ASSIGN/PAINT`; удалить `ADMIN_SPAWN_ZONE_GEOMETRY_UPDATE`, `…_GENERATE`
- [ ] `libs/shared/utils/hex-assign.ts` — чистая раздача (перенос из `spawn-admin.service.ts`) + спека
- [ ] `.env.example`: `TERRITORY_CAPACITY=2` вместо `ZONE_CAPACITY`
- [ ] `prisma/seed.ts`: зоны без geometry, dev-город с разбиением и раздачей (решение 9)

**Готово, когда:** миграция и сид проходят на dev, `npm run build` зелёный,
`SELECT count(*) FROM "Territory" WHERE "zoneId" IS NOT NULL` > 0, `SELECT geometry FROM "SpawnZone"` → ошибка «нет колонки».

### 2. game-core — города, территории, respawn по сотам

Новый модуль `apps/game-core/src/app/admin/city-admin.*`; правки `spawn-admin`, `spawn-cron`, `map`.

- [ ] `listCities` — `$queryRaw`: поля + `ST_AsGeoJSON(boundary)`, `territoriesTotal`, `territoriesAssigned`,
      `spawnsAlive`, `areaKm2` (`ST_Area(boundary::geography)`)
- [ ] `createCity` / `updateCitySettings` (name, hexSizeMeters, isActive) / `deleteCity` (транзакция:
      spawns города → их kills → territories → city; ответ `{ id, territoriesRemoved, spawnsRemoved }`)
- [ ] `updateCityBoundary`: структурная проверка → `ST_IsValid` → `UPDATE`; если у города есть территории —
      требует `confirmResplit: true`, иначе 409 `CITY_HAS_TERRITORIES`; с флагом — перерезка внутри той же транзакции
- [ ] `splitCity(id)`: `ST_HexagonGrid` в UTM по bbox границы, фильтр `ST_Contains(boundary, ST_Centroid(hex))`,
      потолок `CITY_HEX_MAX_CELLS` → 400 `HEX_GRID_TOO_LARGE`; транзакция: удалить старые территории (+ спауны,
      kills) → вставить новые (`hexI`, `hexJ`, `geometry`); ответ — список территорий
- [ ] `assignCity(id, { zoneIds, seed, dryRun })`: центры сот в TS → `hexAssign` из `@shared/utils` →
      `dryRun` отдаёт раскладку, иначе `UPDATE "Territory" SET "zoneId"` батчем; 400 `NO_ZONES`, `NOT_ENOUGH_CELLS`
- [ ] `paintTerritories(id, [{ territoryId, zoneId | null }])`: валидация принадлежности соты городу и
      существования зоны, один `UPDATE … FROM (VALUES …)`; при смене зоны спауны соты живут до respawn (как
      выключение зоны сейчас)
- [ ] `listTerritories(cityId)`: `hexI`, `hexJ`, `zoneId`, `ST_AsGeoJSON(geometry)`, центр, `spawnsAlive`
- [ ] `spawn-cron.service.ts`: цикл `City(isActive) → Territory(zoneId ≠ null) JOIN SpawnZone(isActive)`;
      `capacity ?? TERRITORY_CAPACITY ?? 2` точек через `ST_GeneratePoints(t.geometry, n)`; пул — зоны;
      `INSERT active_spawns (…, spawn_zone_id, territory_id)`; лог пропусков по причинам
- [ ] `map.service.ts` `getZones`: `SELECT DISTINCT z.* FROM "Territory" t JOIN "SpawnZone" z … JOIN "City" c
      WHERE c."isActive" AND z."isActive" AND ST_DWithin(t.geometry::geography, point, radius)`
- [ ] `spawn-admin.service.ts`: убрать `updateZoneGeometry`, `generateZones`, `serializeMultiPolygon`
      (переносится в `city-admin`), `listZones` без geometry + `territoriesCount`, `citiesNames[]`;
      `listActiveSpawns({ zoneId?, cityId? })`
- [ ] `scripts/spawn-run.ts` — без изменений по интерфейсу, проверить вывод
- [ ] Спеки: `city-admin.service.spec.ts` (boundary-валидация, split — фильтр по центру и потолок,
      assign dryRun не пишет, paint отбивает чужую соту, delete — порядок операций), `hex-assign.spec.ts`
      (перенос из `spawn-admin` + анклавы), `spawn-cron.service.spec.ts` (выключенный город пропущен,
      сота без зоны пропущена, `capacity` зоны важнее env, env важнее 2), `map.service.spec.ts` (SQL через Territory)

**Готово, когда:** `npx nx test game-core` зелёный; на dev после сида `scripts/spawn-run.ts` кладёт в каждую
соту с активной зоной ровно `capacity` спаунов внутри её шестиугольника:
`SELECT count(*) FROM active_spawns s JOIN "Territory" t ON t.id = s.territory_id WHERE NOT ST_Contains(t.geometry, s.location::geometry)` = 0.

### 3. api-gateway — REST и Swagger

- [ ] `AdminCityController` (`/admin/cities`, `GatewayJwtGuard + AdminGuard`), DTO в `dto/admin/city.dto.ts`
      (class-validator, `@IsIn`, `@Min/@Max` по константам, `GeoJsonMultiPolygonDto` переезжает сюда)
- [ ] `AdminSpawnController`: удалить `PUT zones/:id/geometry`, `POST zones/generate`; `GET active?cityId=`
- [ ] Swagger: `@ApiDataResponse` на всех, примеры GeoJSON границы и ответа split

**Готово, когда:** `npx nx test api-gateway` и `npm run build` зелёные; через Swagger под admin-токеном
проходит цепочка create city → boundary → split → assign → `POST /admin/spawn/run` → `GET active?cityId=`
отдаёт спауны только этого города; `PUT boundary` у разбитого города без `confirmResplit` → 409.

### 4. Админка — «Города», упрощённые «Зоны»

`troy-admin`, по прототипу; `TerritoryEditor` и `geo.ts` переиспользуются для границы.

- [x] `src/api/cities.ts`: `City`, `Territory`, `listCities`, `createCity`, `updateCitySettings`,
      `updateCityBoundary`, `deleteCity`, `listTerritories`, `splitCity`, `assignCity`, `paintTerritories`
- [x] `src/pages/cities/`: `CitiesPage` (Statistic × 4, таблица), `CityPage` (роут `cities/:id`, Tabs),
      `CityMainPanel`, `CityBoundaryPanel` (TerritoryEditor + «По радиусу» + предупреждение о перерезке),
      `CityTerritoriesPanel` (карта: `<Polygon>` на соту, кисть по `mousedown/mouseover`, режимы раскраски,
      легенда-кисть, карточка соты, «Раздать зоны» → `CityAssignModal`, «Перерезать», «Сохранить раздачу»
      с батчем изменённых сот), `CitySpawnsPanel`
- [x] Цвета зон для сот: детерминированный `hsl` по индексу зоны (`zoneColor(id)` в `zoneTypes.ts`),
      тип и уровень — существующие `ZONE_TYPE_META` и градиент (`levelColor`)
- [x] `pages/zones`: убрать `ZoneTerritoryPanel`, `ZonesGenerateModal`, `ZonesMap`; в `ZoneDrawer` вкладка
      «Где на карте» (read-only, ссылка `cities/:id`); в таблице «Территорий · города» вместо площади
- [x] `SpawnPage`: таблица последнего прогона по городам с причиной пропуска (данные — из `listCities`)
- [x] `AdminLayout`: группа «Мир» (Города / Зоны / Спаун), роут `cities`, `cities/:id`
- [x] `README.md` админки: структура `pages/cities/`

Сделано на моках контракта (этапы 1–3 в бэке ещё не смержены — `ADMIN_CITY_*` в `contracts.ts` нет),
поэтому DoD против живого API не проверялся. Что вылезло по дороге и требует решения на бэке:

- `AdminCitySettingsPayload` в контракте без `confirmResplit`, хотя REST-таблица обещает 409
  `CITY_HAS_TERRITORIES` при смене `hexSizeMeters`. Админка шлёт флаг — его нужно завести в DTO гейтвея,
  иначе `forbidNonWhitelisted` отобьёт запрос.
- Числа зон города в `AdminCityDto` нет, а в `AdminSpawnZoneDto` нет сот по городам (только `cityNames`).
  Колонка «Зон» в таблице городов считается по `cityNames` (сопоставление по имени), а вкладка «Где на
  карте» тянет `listTerritories` по каждому городу зоны — на 20 000 сот это дорого. Просим `zonesCount`
  в городе и `cities: [{ cityId, territories }]` в зоне.
- «Спаунов / нед.» в таблице городов показывает `spawnsAlive` (факт), а не план: плана
  (Σ `capacity` зон по сотам) из `AdminCityDto` не собрать.
- `TerritoryEditor` и `geo.ts` переехали из `pages/zones` в `components/map/` — их теперь использует
  граница города; `components/map/cities.ts` переименован в `mapPresets.ts` (`MapPreset`), чтобы не
  путать пресеты вида с сущностью `City`.

**Готово, когда:** `npm run build` и `npm run lint` чистые; на dev: создал город → обвёл → разбил → раздал →
покрасил пару сот кистью → сохранил → «Перезапустить спаун» → на вкладке «Спауны» и на карте точки только в
сотах с зоной, в перекрашенных — мобы новой зоны; выключил город → после respawn его спаунов нет; удалил
город → таблица и карта пусты, `GET /map/zones` в его центре пуст.

### 5. Доки и закрытие

- [ ] `troy/CLAUDE.md`: архитектура `spawn` (город → соты → зоны, `TERRITORY_CAPACITY`), пункты 3–4
      «Key design decisions» (raw-геометрия теперь у `City.boundary`, `Territory.geometry`, `active_spawns`;
      `SpawnZone` без geometry), env
- [ ] `technical/database-schema.md`: секции `City`, `Territory`, `SpawnZone` без geometry, `active_spawns.territory_id`
- [ ] `roadmap/README.md`: галочка темы; `zones/README.md` — баннер «этапы 6–7 заменены cities»;
      `mvp-4-content-balance/README.md` — SCRUM-60 закрыт; `vendors/README.md` — номер миграции
- [ ] Коммиты `cities: …` (backend, admin, docs); Jira — `/troy-continue`

## Контракт и точки входа

### Миграция `0023_cities_territories`

```sql
CREATE TABLE "City" (
  "id"            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "name"          TEXT NOT NULL,
  "isActive"      BOOLEAN NOT NULL DEFAULT FALSE,
  "hexSizeMeters" INTEGER NOT NULL DEFAULT 300,
  "assignSeed"    INTEGER,
  "createdAt"     TIMESTAMPTZ NOT NULL DEFAULT now(),
  "updatedAt"     TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Граница мира; вне Prisma (PostGIS), как раньше SpawnZone.geometry.
ALTER TABLE "City" ADD COLUMN boundary geometry(MultiPolygon, 4326);
CREATE INDEX "City_boundary_idx" ON "City" USING GIST (boundary);

CREATE TABLE "Territory" (
  "id"     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "cityId" UUID NOT NULL REFERENCES "City"("id") ON DELETE CASCADE,
  "zoneId" UUID REFERENCES "SpawnZone"("id") ON DELETE SET NULL,
  "hexI"   INTEGER NOT NULL,
  "hexJ"   INTEGER NOT NULL,
  UNIQUE ("cityId", "hexI", "hexJ")
);
ALTER TABLE "Territory" ADD COLUMN geometry geometry(Polygon, 4326) NOT NULL;
CREATE INDEX "Territory_geometry_idx" ON "Territory" USING GIST (geometry);
CREATE INDEX "Territory_zoneId_idx" ON "Territory" ("zoneId");

ALTER TABLE active_spawns ADD COLUMN territory_id UUID REFERENCES "Territory"("id") ON DELETE CASCADE;
CREATE INDEX active_spawns_territory_idx ON active_spawns (territory_id);

-- Зона больше не знает, где она на карте.
DROP INDEX IF EXISTS "SpawnZone_geometry_idx";
ALTER TABLE "SpawnZone" DROP COLUMN geometry;
```

`ON DELETE CASCADE` на `active_spawns.territory_id` — страховка; сервис всё равно удаляет спауны и их
`CharacterKill` явно в транзакции, потому что `CharacterKill.spawnId` без FK.

```prisma
model City {
  id            String      @id @default(uuid()) @db.Uuid
  name          String
  // Выключенный город не участвует в respawn и не отдаётся клиенту.
  isActive      Boolean     @default(false)
  // Ребро соты, м (CITY_HEX_MIN_METERS..MAX). Смена — перерезка территорий.
  hexSizeMeters Int         @default(300)
  // Seed последней раздачи зон; тот же seed и состав → та же раскладка.
  assignSeed    Int?
  createdAt     DateTime    @default(now())
  updatedAt     DateTime    @updatedAt
  territories   Territory[]
  // boundary geometry(MultiPolygon, 4326) — вне Prisma, raw SQL.
}

model Territory {
  id     String     @id @default(uuid()) @db.Uuid
  cityId String     @db.Uuid
  city   City       @relation(fields: [cityId], references: [id], onDelete: Cascade)
  // null — пустошь: respawn пропускает, клиент ничего не видит.
  zoneId String?    @db.Uuid
  zone   SpawnZone? @relation(fields: [zoneId], references: [id], onDelete: SetNull)
  hexI   Int
  hexJ   Int
  // geometry geometry(Polygon, 4326) NOT NULL — шестиугольник, вне Prisma.
  @@unique([cityId, hexI, hexJ])
  @@index([zoneId])
}

// SpawnZone: capacity Int? — теперь «спаунов на соту в неделю», null → env TERRITORY_CAPACITY (2).
//            + territories Territory[]
```

### Контракты (`libs/shared/contracts/src/lib/contracts.ts`)

```ts
export const CITY_HEX_MIN_METERS = 100;
export const CITY_HEX_MAX_METERS = 5000;
export const CITY_HEX_MAX_CELLS = 20000;
export const TERRITORY_CAPACITY_MAX = 16; // потолок на соту; зажимает и env

export interface AdminCityDto {
  id: string; name: string; isActive: boolean; hexSizeMeters: number; assignSeed: number | null;
  boundary: GeoJsonMultiPolygon | null;
  areaKm2: number | null;
  territoriesTotal: number; territoriesAssigned: number; spawnsAlive: number;
  updatedAt: string;
}
export interface AdminTerritoryDto {
  id: string; cityId: string; zoneId: string | null; hexI: number; hexJ: number;
  geometry: GeoJsonPolygon; center: { lat: number; lng: number }; spawnsAlive: number;
}
export interface AdminCityCreatePayload { name: string; hexSizeMeters?: number; isActive?: boolean; }
export interface AdminCitySettingsPayload { id: string; name?: string; hexSizeMeters?: number; isActive?: boolean; }
export interface AdminCityBoundaryPayload { id: string; boundary: GeoJsonMultiPolygon | null; confirmResplit?: boolean; }
export interface AdminCityDeleteResult { id: string; territoriesRemoved: number; spawnsRemoved: number; }
export interface AdminCitySplitPayload { id: string; }
export interface AdminCityAssignPayload { id: string; zoneIds: string[]; seed?: number; dryRun?: boolean; }
export interface AdminCityAssignResult { cityId: string; seed: number; applied: boolean; territories: AdminTerritoryDto[]; perZone: { zoneId: string; hexCount: number }[]; }
export interface AdminCityPaintPayload { id: string; changes: { territoryId: string; zoneId: string | null }[]; }
// AdminSpawnZoneDto: −geometry, +territoriesCount: number, +cityNames: string[]
// AdminActiveSpawnDto: +territoryId: string | null;  AdminActiveSpawnListPayload: +cityId?: string
```

Паттерны: `admin.city.list`, `admin.city.create`, `admin.city.settings.update`, `admin.city.boundary.update`,
`admin.city.delete`, `admin.city.territories.list`, `admin.city.territories.split`,
`admin.city.territories.assign`, `admin.city.territories.paint`. Удаляются `admin.spawn.zone.geometry.update`,
`admin.spawn.zone.generate`.

### REST (`/admin/cities`, `GatewayJwtGuard + AdminGuard`)

| Метод | Путь | Тело / query | Ответ |
|---|---|---|---|
| GET | `cities` | — | `AdminCityDto[]` |
| POST | `cities` | `CreateCityDto` | `AdminCityDto` |
| PUT | `cities/:id` | `UpdateCitySettingsDto` | `AdminCityDto` (смена `hexSizeMeters` у разбитого города → 409 `CITY_HAS_TERRITORIES` без `confirmResplit`) |
| PUT | `cities/:id/boundary` | `{ boundary, confirmResplit? }` | `AdminCityDto` · 400 `GEOMETRY_INVALID` · 409 `CITY_HAS_TERRITORIES` |
| DELETE | `cities/:id` | — | `AdminCityDeleteResult` |
| GET | `cities/:id/territories` | — | `AdminTerritoryDto[]` |
| POST | `cities/:id/territories/split` | — | `AdminTerritoryDto[]` · 400 `CITY_NO_BOUNDARY`, `HEX_GRID_TOO_LARGE` |
| POST | `cities/:id/territories/assign` | `{ zoneIds, seed?, dryRun? }` | `AdminCityAssignResult` · 400 `NO_ZONES`, `NOT_ENOUGH_CELLS`, `ZONE_NOT_FOUND` |
| PUT | `cities/:id/territories` | `{ changes: [{ territoryId, zoneId }] }` | `AdminTerritoryDto[]` (изменённые) · 400 `TERRITORY_NOT_IN_CITY`, `ZONE_NOT_FOUND` |
| GET | `/admin/spawn/active` | `?zoneId=&cityId=` | `AdminActiveSpawnDto[]` |

Ошибки 400 в стиле `LEVEL_TOO_LOW`; несуществующий город — 404 `City not found`.

### Соты в SQL

```sql
-- split: сетка в UTM-зоне центра границы, наружу — только соты с центром внутри
WITH b AS (SELECT boundary AS g, _ST_BestSRID(boundary) AS srid FROM "City" WHERE id = ${id}::uuid),
     grid AS (
       SELECT h.i, h.j, ST_Transform(h.geom, 4326) AS geom
       FROM b, ST_HexagonGrid(${hexSizeMeters}, ST_Transform(b.g, b.srid)) AS h
     )
INSERT INTO "Territory" ("cityId", "hexI", "hexJ", geometry)
SELECT ${id}::uuid, grid.i, grid.j, grid.geom
FROM grid, b WHERE ST_Contains(b.g, ST_Centroid(grid.geom))
RETURNING id, "hexI", "hexJ", ST_AsGeoJSON(geometry)::json AS geometry;

-- respawn: n точек в соте
SELECT ST_SetSRID((ST_Dump(ST_GeneratePoints(t.geometry, ${n}))).geom, 4326)::geography
FROM "Territory" t WHERE t.id = ${territoryId}::uuid;

-- /map/zones
SELECT DISTINCT z.id, z.name, z."zoneType", z."minLevel", z."maxLevel"
FROM "Territory" t
JOIN "City" c ON c.id = t."cityId" AND c."isActive"
JOIN "SpawnZone" z ON z.id = t."zoneId" AND z."isActive"
WHERE ST_DWithin(t.geometry::geography, ST_SetSRID(ST_MakePoint(${lng}, ${lat}), 4326)::geography, ${radius});
```

Замечание по `ST_HexagonGrid`: в 3857 «сота 400 м» на широте Москвы выходит 225 м, поэтому сетка строится в
UTM (`_ST_BestSRID`) и переводится обратно — так уже сделано в этапе 7 темы zones.

### Что не тащим

- Полигоны сот и границу города клиенту, экран «вы вне мира», `GET /map/cities` — следующая тема
  (клиентская сторона мира).
- Ручное рисование произвольной территории; территория — только сота.
- Веса мобов, боссы и фиксированные слоты — MVP-4.
- Пересечение границ городов не проверяем: два города могут перекрываться, respawn заполнит оба.
- Vendors на территории — vendors (SCRUM-68) добавит своё поле, когда дойдёт.

## Риски и открытые вопросы

- **Объём:** 20 000 сот × 2 спауна = 40 000 `active_spawns` на город. `INSERT` батчем по 1000 строк,
  а не по одной, как сейчас в cron; проверить время respawn на dev с городом ~5 000 сот.
- **Ребро соты и «жизнь» на карте:** 250 м даёт ~0,16 км² и 2 моба на соту — на глаз нормально для центра
  города, для спальных районов может быть пусто. Крутить `hexSizeMeters` и `capacity` на живых данных.
- **Кисть и конкурентность:** два админа красят один город — последний `PUT territories` побеждает по
  сотам, конфликтов не детектим.
- **Смена зоны у соты между respawn'ами:** старые спауны живут до среды (как выключение зоны сейчас). Если
  это будет мешать контент-мейкеру — кнопка «Перезапустить спаун города» уже есть в прототипе.
- **Вопрос пользователю:** нужен ли `City.timezone` для локального времени respawn, или среда 00:00 UTC
  для всех — решение «UTC для всех» до MVP-5.

## Порядок работы

1. Завести эпик «cities» и задачи по этапам 1–4 через `/troy-task` (этап 5 — хвост последней).
2. Этапы 1 → 2 → 3 последовательно, одна сессия на `troy-backend`.
3. Этап 4 можно начинать на моках `api/cities.ts` параллельно с 3; DoD — только против живого API.
4. Этап 5 — после сценария пользователя на dev.

## Промт для сессии

```
Проект Troy, воркспейс /Users/fost/Projects/troy. Прочитай troy/CLAUDE.md, затем
troy-docs/roadmap/cities/README.md целиком — это план и контракт; для контекста «как сейчас» —
troy-docs/roadmap/zones/README.md, этапы 6–7 (их код ты переносишь с зоны на город).
Делай этапы 1–3 в troy-backend по разделу «Контракт и точки входа», отмечая чекбоксы по ходу.

Правила: миграции только `npm run prisma:migrate` (deploy) — `migrate dev` дропает raw-геометрию;
после миграции `npm run prisma:seed`; зависимости пинить точно; клиентский контракт /map/zones и
/map/entities не менять. Чистую раздачу (farthest-point + nearest + анклавы) вынести в
libs/shared/utils/hex-assign.ts, чтобы её использовали и seed, и city-admin. Тесты — Jest, спеки рядом
с сервисами (эталон: apps/game-core/src/app/admin/spawn-admin.service.spec.ts).

DoD: `npx nx run-many -t test` и `npm run build` зелёные; через Swagger под admin-токеном проходит
create city → boundary → split → assign → POST /admin/spawn/run → GET active?cityId= с точками внутри
сот; PUT boundary у разбитого города без confirmResplit → 409. Коммит `cities: …`, без подписей
ассистента. В конце — открытые вопросы и что не удалось проверить без живой БД.
```

```
Проект Troy, админка troy-admin (Vite + React 19 + antd 6 + react-leaflet 5 + leaflet-geoman).
Задача: переделать раздел «Мир» админки под новую модель город → зона → территория
(troy-docs/roadmap/cities/README.md, этап 4), не потеряв ни одной уже работающей фичи раздела «Зоны».

Прочитай по порядку: troy-admin/README.md; troy-docs/roadmap/cities/README.md целиком (модель, решения,
этап 4, «Контракт и точки входа» — REST и DTO); troy-docs/roadmap/zones/README.md, блоки «Как это вышло
в коде (этап 4, админка)», этапы 6 и 7 — это правила и код, которые ты переносишь. Прототип, по которому
делать: https://claude.ai/code/artifact/b47f545b-531b-4aee-81f4-a5a4316479f9 (исходник
troy-docs/design/prototypes/admin-cities-territories.html — там же алгоритмы разбиения и раздачи для
превью). Компоненты antd, стиль как у pages/zones и pages/monsters.

Сначала проверь бэкенд: grep ADMIN_CITY_ в troy-backend/libs/shared/contracts/src/lib/contracts.ts.
Если паттернов нет — этапы 1–3 cities ещё не смержены: пиши src/api/cities.ts строго по типам и путям
из раздела «Контракт и точки входа» (AdminCityDto, AdminTerritoryDto, /admin/cities/…), ничего не
выдумывай сверх контракта, а DoD против живого API отметь как «не проверено» и опиши сценарий
пользователю. Если есть — сверь типы с contracts.ts, расхождения решай в пользу бэкенда и запиши в README.

Что уже работает и обязано остаться (инвентарь фич, куда переезжает):
1. ZonesPage: четыре Statistic, таблица зон, клик по строке подсвечивает, «Перезапустить спаун» с Popconfirm,
   «Новая зона» → остаётся в /zones. Столбец «площадь» → «Территорий · города» (territoriesCount, cityNames).
2. ZoneDrawer (780px, Tabs; создание — вкладки кроме «Основное» disabled до первого сохранения;
   у каждой вкладки своя кнопка и свой эндпойнт; ответ мутации кладётся в состояние drawer'а):
   Основное (ZoneMainPanel: name/type/min/max/capacity/isActive, удаление с Popconfirm и текстом
   «сколько спаунов исчезнет») — остаётся, capacity теперь «спаунов на соту в неделю», плейсхолдер
   «по умолчанию 2», лимит из TERRITORY_CAPACITY_MAX; Мобы (ZoneMonstersPanel: чекбоксы, уровень,
   «пак a–b», предупреждения «N ур. вне min–max» и «выключен глобально») — без изменений; Арена
   (ZoneArenaPanel) — без изменений; Спауны (ZoneSpawnsPanel: моб, пак, координаты, убит) — без
   изменений; Территория (ZoneTerritoryPanel) — удаляется, вместо неё read-only вкладка «Где на карте»
   (города зоны: сот, спаунов/нед., кнопка «На карту» → /cities/:id с вкладкой «Территории»).
3. TerritoryEditor (общий слой рисования geoman: draw/edit/clear, allowSelfIntersection: false,
   pm:edit → состояние, округление до 6 знаков, слой пересобирается только по команде, а не на каждую
   правку вершины) и geo.ts (contoursOf, multiPolygonFromLatLngs, validateGeometry, areaKm2,
   perimeterKm, vertexCount, contourCentroid) → переиспользуются для границы города один в один.
   Таблица контуров (площадь, вершины, центр, «Показать», удалить), «Добавить контур», пустое
   состояние — переезжают в CityBoundaryPanel; текст пустого состояния: «Границы нет — город нельзя
   разбить на соты, respawn его пропускает».
4. ZonesGenerateModal (ребро соты 100–5000 с константами, seed + «Перемешать», dryRun-превью на карте и
   таблицей по зонам, «Применить» с тем же seed, обводка границы или «прямоугольник по виду карты»,
   ошибки HEX_GRID_TOO_LARGE / NOT_ENOUGH_CELLS / NO_ZONES / ZONE_TOO_* в человеческий текст) →
   разделяется: обводка границы — в CityBoundaryPanel; ребро соты — поле города; «Разбить на соты» —
   кнопка (POST split); seed/«Перемешать»/dryRun-превью/таблица по зонам → CityAssignModal
   (POST assign) с новым чеклистом зон. Ни одна опция не теряется.
5. ZonesMap (Polygon на зону цветом типа, выключенная — пунктир; CircleMarker спаунов с бейджем ×N
   при packSize > 1; тултип: моб, уровень, зона, координаты, убит N; клик по строке таблицы →
   подсветка) → CityTerritoriesPanel: Polygon на соту, спауны и тултипы как были; на CitiesPage — обзорная
   карта границ городов (Polygon на город, выключенный — пунктир).
6. AdminMap + MapControl + быстрые переходы по городам (components/map/cities.ts) — остаются.
   Переименуй файл и типы в mapPresets.ts / MapPreset, чтобы не путать с сущностью City; «Новый город»
   может брать имя и центр карты из пресета.
7. SpawnPage: respawn с Popconfirm, глобальный флаг «Спаунить», SpawnMapModal живых спаунов, строка-подсказка
   со ссылкой на /zones — остаются; добавляется таблица последнего прогона по городам с причиной
   пропуска (нет границы / не разбит / выключен / нет сот с зоной) — данные из listCities.
8. zoneTypes.ts (подписи и цвета типов), zoneStatus.ts — остаются; добавь zoneColor(id) —
   детерминированный hsl по индексу зоны для раскраски сот «по зоне».
9. Перевод ошибок бэка в текст (GEOMETRY_INVALID и др.) — сохранить и дополнить кодами cities:
   CITY_HAS_TERRITORIES (409 → Modal.confirm «Перерезать соты? Раздача зон и спауны города будут
   удалены», повтор запроса с confirmResplit: true), CITY_NO_BOUNDARY, TERRITORY_NOT_IN_CITY, ZONE_NOT_FOUND.

Новое (по прототипу):
- Роуты cities и cities/:id, пункт меню «Города» в группе «Мир» (Города / Зоны / Спаун), lazy-чанки.
- CitiesPage: Statistic × 4 (городов спаунится / территорий и с зоной / спаунов на неделю / следующая
  среда), таблица (статус: черновик без границы · не разбит · активен · выключен; площадь; ребро; террит.
  с зоной / всего; зон; спаунов/нед.; изменён), «Новый город» → drawer с name / hexSizeMeters / isActive,
  после создания — переход на cities/:id, вкладка «Граница».
- CityPage с Tabs: Основное (name, hexSizeMeters с подсказкой площади соты ≈ 2,6 × ребро², isActive,
  assignSeed read-only, центр/bbox, удаление с Popconfirm и текстом про территории и спауны; смена ребра
  у разбитого города — тот же confirm о перерезке), Граница, Территории (disabled без границы), Спауны
  (disabled без сот с зоной; listActiveSpawns({ cityId })).
- CityTerritoriesPanel: Segmented «выбор / кисть», Segmented раскраски «по зоне / по типу / по уровню»,
  переключатель спаунов, легенда-кисть (все зоны + «Без зоны — мобов нет», счётчики сот, выключенная зона
  помечена), карточка выбранной соты (зона, спаунов/нед., центр, площадь, Select зоны), кнопки «Раздать
  зоны», «Перерезать соты» (Popconfirm), «Сохранить раздачу» / «Отменить». Кисть: Polygon на соту с
  eventHandlers mousedown/mouseover, нажатие держится в useRef, изменения копятся в Map<territoryId, zoneId>
  и уходят одним PUT /admin/cities/:id/territories { changes } только по реально изменённым сотам; после
  ответа локальное состояние сот обновляется ответом, без повторного listTerritories.
  Сот может быть до 20 000 — Polygon'ы рендерить одним слоем без Tooltip на каждом (тултип — один,
  по hover через состояние), pathOptions мемоизировать.

Удалить: ZoneTerritoryPanel, ZonesGenerateModal, ZonesMap (после переноса кода), updateZoneGeometry,
generateZones, ZONE_GENERATE_* и geometry из типа SpawnZone в api/spawn.ts.

Правила кода (из этапа 4 zones, не нарушать): гейтвей валидирует forbidNonWhitelisted — формы шлют ровно
поля DTO, не объекты из ответов; eslint-plugin-react-hooks 7 запрещает setState в эффекте — состояние
страницы/drawer'а (какой город, какая вкладка, режим кисти) живёт на странице и меняется в обработчиках;
зависимости пинить точно (.npmrc save-exact), новых зависимостей не добавлять без нужды (geoman и
react-leaflet уже есть); прототип — ориентир по составу и текстам, а не по вёрстке пиксель в пиксель,
компоненты antd. Отмечай чекбоксы этапа 4 в troy-docs/roadmap/cities/README.md по ходу; обнови
troy-admin/README.md (структура pages/cities/, что убрано из pages/zones).

DoD: `npm run build` и `npm run lint` чистые; ни один пункт инвентаря 1–9 не пропал (пройди по списку и
отметь в отчёте, куда переехал каждый); при живом бэке — сценарий из «Готово, когда» этапа 4 cities.
В конце — отчёт: что перенесено куда, что не удалось проверить без бэкенда, открытые вопросы.
Коммит `cities: admin — города, территории, зоны без карты`, без подписей ассистента.
```
