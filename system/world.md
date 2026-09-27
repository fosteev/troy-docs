---
verified: 2026-09-27
backend: 7fe8024
admin: dbb54d4
paths:
  - troy-backend/apps/game-core/src/app/admin/
  - troy-backend/apps/game-core/src/app/map/
  - troy-backend/libs/shared/utils/src/lib/hex-assign.ts
  - troy-admin/src/pages/cities/
  - troy-admin/src/pages/zones/
  - troy-admin/src/pages/spawn/
---
# World — город → территория → зона

> Где на карте появляются мобы: город режется на шестиугольные соты, каждая сота получает зону-каталог
> (тип/уровни/пул мобов), раз в неделю respawn заполняет соты паками.

## Как работает

- Иерархия: `City` (граница) → `Territory` (сота гекс-сетки) → `SpawnZone` (справочник, без своей
  геометрии) `troy-backend/libs/shared/prisma/schema.prisma:SpawnZone`.
- Город — имя, `hexSizeMeters` (дефолт 300 при создании), `isActive`, `assignSeed`; граница задаётся
  отдельным вызовом как GeoJSON MultiPolygon, `null` снимает её целиком
  `troy-backend/apps/game-core/src/app/admin/city-admin.service.ts:updateCityBoundary`.
- Разбиение на соты — `ST_HexagonGrid` в динамически подобранной UTM-зоне (чтобы «сота 250 м» не плыла по
  широте); сота остаётся только если её центр внутри границы города
  `troy-backend/apps/game-core/src/app/admin/city-admin.service.ts:splitInTransaction`.
- Раздача зон по сотам — детерминированный `hexAssign`: farthest-point sampling центров от `seed`, ближайший
  центр забирает соту, анклавы одной зоны внутри другой поглощаются; тот же `seed` даёт ту же раскладку, поэтому
  dryRun-превью в админке совпадает с результатом `troy-backend/libs/shared/utils/src/lib/hex-assign.ts:hexAssign`.
- Ручная кисть — batch-перекраска сот, последняя правка по соте побеждает
  `troy-backend/apps/game-core/src/app/admin/city-admin.service.ts:paintTerritories`.
- Еженедельный respawn — cron по средам 00:00 UTC (жёстко, часовой пояс города не учитывается): сносит
  **всю** таблицу `active_spawns` и все `CharacterKill`, затем обходит соты, у которых одновременно активны
  и город, и зона `troy-backend/apps/game-core/src/app/map/spawn-cron.service.ts:run`.
- Лимит спаунов на соту — приоритет `SpawnZone.capacity`, иначе env `TERRITORY_CAPACITY`, потолок 16
  `troy-backend/apps/game-core/src/app/map/spawn-cron.service.ts:territoryCapacity`.
- Размер пака фиксируется на неделю при спауне — случайное число из `packMin..packMax` монстра (потолок 4);
  мобы с `spawnable=false` исключаются даже если числятся в пуле зоны
  `troy-backend/apps/game-core/src/app/map/spawn-cron.service.ts:rollPackSize`.
- Точка спауна — случайная точка строго внутри полигона соты; это единственное место, где генерится
  геометрия точки `troy-backend/apps/game-core/src/app/map/spawn-cron.service.ts:insertSpawns`.
- Живые спауны после вставки кэшируются в Redis на 5 минут
  `troy-backend/apps/game-core/src/app/map/spawn-cron.service.ts:cacheSpawns`.
- Клиентская карта не завязана на геометрию зоны — «зона рядом» определяется через `ST_DWithin` по
  территориям `troy-backend/apps/game-core/src/app/map/map.service.ts:getZones`.

## Данные

- Prisma: `City` (name, isActive, hexSizeMeters, assignSeed), `Territory` (cityId, zoneId, hexI, hexJ,
  `@@unique([cityId,hexI,hexJ])`), `SpawnZone` (name, zoneType, monsterIds[], minLevel/maxLevel, isActive,
  capacity?, arenaBackground — без геометрии), `Monster.packMin`/`packMax`/`spawnable`
  `troy-backend/libs/shared/prisma/schema.prisma:City`.
- Raw SQL (миграция `0023_cities_territories`): `City.boundary geometry(MultiPolygon,4326)`,
  `Territory.geometry geometry(Polygon,4326)`, `active_spawns.territory_id` — FK на `Territory`
  `troy-backend/libs/shared/prisma/migrations/0023_cities_territories/`.
- `active_spawns` целиком вне Prisma (создана `0001_init`, `pack_size` добавлен `0017_monster_packs`):
  `id, monster_id, spawn_zone_id, territory_id, location GEOGRAPHY(POINT), spawned_at, alive, pack_size`.
- `CharacterKill.spawnId` — UUID без FK на `active_spawns` (та таблица вне ORM), поэтому снос города/зоны
  удаляет вручную в порядке `CharacterKill` → `active_spawns` → сама сущность.

## Контракт

- REST `/admin/cities` — CRUD, `/boundary`, `/territories`, `/territories/split`, `/territories/assign`,
  `/territories` (кисть) `troy-backend/apps/api-gateway/src/app/admin/admin-cities.controller.ts`.
- REST `/admin/spawn` — `run`, `zones` CRUD, `active` (фильтр по zoneId/cityId), `zones/:id/monsters`,
  `zones/:id/arena` `troy-backend/apps/api-gateway/src/app/admin/admin-spawn.controller.ts`.
- NATS `admin.city.*` / `admin.spawn.*` `troy-backend/libs/shared/contracts/src/lib/contracts.ts`.
- Клиентский контракт карты не меняется этой темой: `GET /map/zones`, `GET /map/entities`, WS `map:request`.

## Где в коде

| Слой | Путь |
|---|---|
| backend — города | `troy-backend/apps/game-core/src/app/admin/city-admin.service.ts`, `troy-backend/apps/game-core/src/app/admin/city-admin.controller.ts` |
| backend — зоны/спаун | `troy-backend/apps/game-core/src/app/admin/spawn-admin.service.ts`, `troy-backend/apps/game-core/src/app/map/spawn-cron.service.ts` |
| backend — раздача по сотам | `troy-backend/libs/shared/utils/src/lib/hex-assign.ts` |
| backend — REST | `troy-backend/apps/api-gateway/src/app/admin/admin-cities.controller.ts`, `troy-backend/apps/api-gateway/src/app/admin/admin-spawn.controller.ts` |
| admin | `troy-admin/src/pages/cities/`, `troy-admin/src/pages/zones/`, `troy-admin/src/pages/spawn/` |

## Где потрогать

- Админка → «Города»: создать город, задать границу, «Разбить на соты», «Раздать зоны» (с dryRun), кисть по сотам.
- Админка → «Зоны»: справочник тип/уровни/пул мобов/арена/лимит на соту.
- Админка → «Спаун»: ручной respawn (кнопка = `POST /admin/spawn/run`), карта живых спаунов, фильтр по городу/зоне.
- `npm run spawn:run` — тот же код, что и cron, без ожидания среды.

## Конфиг и ручки баланса

- `TERRITORY_CAPACITY` — спаунов на соту в неделю, если у зоны `capacity` не задан (дефолт `TERRITORY_CAPACITY_DEFAULT=2`, потолок `TERRITORY_CAPACITY_MAX=16`).
- `CITY_HEX_MIN_METERS=100` / `CITY_HEX_MAX_METERS=5000` / `CITY_HEX_MAX_CELLS=20000` — лимиты гекс-сетки.
- `CITY_BOUNDARY_MAX_POLYGONS=32` / `CITY_BOUNDARY_MAX_VERTICES=256` — лимиты границы города.
- `MONSTER_PACK_MAX=4` — потолок размера пака.
- `hexSizeMeters` по умолчанию — литерал 300 в коде (не env); dev-сид использует 250.

## Известные дыры

- Respawn жёстко привязан к UTC для всех городов — часовой пояс города (`City.timezone`) не реализован.
- Пересечение границ разных городов не проверяется — валидируется только геометрия одного города (`ST_IsValid`).
- Полигоны сот и границы города клиенту не отдаются — осознанно, отдельного `GET /map/cities` нет.
- Комментарий в `troy-backend/scripts/spawn-run.ts` устарел («генерация 8 мобов на зону») — рудимент
  прежней модели `ZONE_CAPACITY`, реальный код считает `capacity` на соту.

## Глубже и история

- [roadmap/cities](../roadmap/cities/README.md) — модель, решения, этапы 1–5 (тема закрыта 27.09)
- [roadmap/zones](../roadmap/zones/README.md) — предыдущая модель (территория на зоне), заменена cities
- [technical/database-schema.md](../technical/database-schema.md) — поля/типы/индексы моделей
