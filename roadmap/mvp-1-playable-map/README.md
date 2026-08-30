# MVP-1 — Playable Map

> **Статус: сделано** (Шаг 2; фича `map` по стандарту, персональная видимость мобов, вектор-тайлы Protomaps через прокси api-gateway).

Цель: карта должна стать игровым экраном, а не статичной витриной.

## Продуктовый результат

Игрок видит себя на карте, видит ближайших мобов и понимает, до каких мобов можно дотянуться физически.

## Backend

- [x] Реализовать или стабилизировать map endpoints:
  - nearby entities;
  - nearby zones;
  - distance to entity;
  - interaction radius.
- [x] Использовать PostGIS для поиска мобов рядом (`ST_DWithin`, `ST_Distance`).
- [x] Кэшировать частые запросы в Redis коротким TTL (**ключ пер-персонажный** — выдача
  отфильтрована под убийства конкретного персонажа).
- [x] Не отдавать мобов, деспавненных системой (`alive = FALSE`).
- [x] Не отдавать мобов, которых **этот персонаж** уже убил на текущей неделе
  (см. персональную механику ниже). Один и тот же моб остаётся видимым для других
  игроков — общего «лока на бой» нет.
- [x] `canInteract` считается на сервере: `distance <= INTERACTION_RADIUS_M` (env, дефолт 50).
- [x] Возвращать DTO, достаточный клиенту:
  - id;
  - type;
  - name;
  - level;
  - lat/lng;
  - distance;
  - canInteract.

### Персональная видимость мобов

- [x] Любой игрок может начать бой по любому живому мобу — общей блокировки нет.
- [x] Убитый моб исчезает **только для убившего персонажа**. Факт убийства пишется на
  персонаже по `active_spawns.id` (таблица `CharacterKill`, см. database-schema.md).
- [x] Недельный сброс: **каждую среду в 00:00 UTC** — фильтр учитывает только убийства
  с `killedAt >= начала текущей недели`, после среды все мобы снова видны.
- [x] Запись убийства (write-путь) — это battle-loop (Шаг 3). На этом шаге строится
  модель `CharacterKill` + read-фильтр в `/map/entities`.

## Flutter

- [x] Запрашивать permission на геолокацию.
- [x] Получать текущую позицию устройства.
- [x] Центрировать карту на игроке.
- [x] Слать движение на backend.
- [x] Показывать mobs из backend вместо hardcoded markers.
- [x] Визуально различать mobs в радиусе и вне радиуса.
- [x] Не позволять начать бой, если `canInteract = false`.
- [x] Показывать понятное состояние при выключенной геолокации.

### Игровой вид карты (vector tiles)

Базовая карта — не OSM-раster «как в навигаторе», а тёмный кастомный стиль
поверх векторных тайлов (как в Pokémon GO / Ingress / Orna): свой style JSON
красит геометрию OSM на клиенте (`troy-flutter`), спрятаны лишние подписи/POI.

- Данные — self-hosted [Protomaps](https://protomaps.com) pmtiles-архив,
  раздаётся с `api-gateway` (`/tiles/<file>.pmtiles`, `express.static` с
  поддержкой HTTP Range — клиент качает только видимые тайлы, не весь файл).
- Сейчас забандлен один архив под Москву (игра пока московская).
- **Техническая возможность**: покрытие расширяется на любой другой регион
  без изменения кода — достаточно сделать новый экстракт по bbox из
  публичного билда Protomaps (`pmtiles extract <build> <output> --bbox=...`)
  и положить файл в `troy-backend/data/tiles/`; он сразу станет доступен по
  тому же префиксу.
- Вне покрытия архива клиент показывает обычный OSM raster как fallback —
  слои независимы, переключения bbox вручную не требуется.

## Связанные документы

- [geolocation.md](../../technical/geolocation.md)
- [database-schema.md](../../technical/database-schema.md)

## Definition of Done

- [x] На реальном устройстве позиция игрока обновляется.
- [x] Мобы на карте приходят с backend.
- [x] Бой доступен только в радиусе взаимодействия.
- [x] При выключенной геолокации пользователь не попадает в сломанный экран.

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила (архитектура, тесты, делегирование) — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy (Flutter в troy-flutter, backend в troy-backend).

Прочитай:
- troy-docs/roadmap/mvp-1-playable-map/README.md (scope и DoD);
- troy-docs/technical/geolocation.md;
- "Architecture rules" в troy-flutter/CLAUDE.md и эталон lib/features/auth/**;
- текущую заглушку lib/features/map/** (там пока только presentation-виджеты, без data-слоя).

Backend (troy-backend) — map endpoints + персональная видимость мобов:
- nearby entities (PostGIS ST_DWithin + ST_Distance), nearby zones;
- DTO клиенту: id, type('monster'), name, level, lat, lng, distance, canInteract;
- canInteract = distance <= INTERACTION_RADIUS_M (env, дефолт 50); добавить в .env.example;
- Prisma-модель CharacterKill (characterId FK, spawnId=active_spawns.id без FK, killedAt;
  @@unique([characterId, spawnId])) + миграция;
- getEntities фильтрует мобов: alive=TRUE И NOT EXISTS убийство этим активным
  персонажем с killedAt >= начала недели (среда 00:00 UTC); хелпер weekStart();
- Redis-кэш короткий TTL, ключ ПЕР-ПЕРСОНАЖНЫЙ (map:entities:{characterId}:{lat}:{lng}:{radius});
- WS map:request: верхний предел radius = 5000 (как REST);
- запись убийства (отмена глобального alive=FALSE → INSERT CharacterKill) — это Шаг 3;
- обновить Swagger-DTO и перегенерить packages/troy_backend_api для Flutter.

Flutter — построить фичу map ПО СТАНДАРТУ (domain/data/presentation):
- domain: entities (MapEntity, SpawnZone), repository-интерфейс (Either);
- data: remote datasource (REST GET /map/entities, /map/zones) + socket datasource (player:move, map:request/map:entities) + repo_impl + мапперы;
- presentation: MapBloc (позиция, загрузка мобов, debounce player:move), страница на flutter_map;
- геолокация: permission, центрирование на игроке, отправка движения; различать мобов в радиусе и вне; не давать начать бой при canInteract=false; внятный экран при выключенной геолокации.

Тесты (flutter_test + mocktail, по эталону auth): map repository_impl, MapBloc, мапперы; backend — unit/integration на map endpoints.

DoD: позиция игрока обновляется на устройстве; мобы приходят с backend; бой только в радиусе; flutter analyze чисто; flutter test зелёный; backend build+тесты зелёные. Коммит. Отметить фазу [x] в troy-docs/roadmap/README.md.
```
