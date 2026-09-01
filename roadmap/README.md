# Troy — Roadmap

Единая точка входа в план. Здесь — цикл MVP, scope, статус фаз и общие правила; детали каждой фазы — в её папке.

MVP — минимальная версия, в которой игрок проходит полный цикл:

```
Регистрация / логин
→ создание или выбор персонажа
→ выход на карту
→ поиск моба рядом
→ бой
→ получение опыта и лута
→ усиление персонажа
→ повтор цикла
```

Все задачи оцениваются через этот цикл. Если задача не приближает playable loop — она не входит в MVP.

## Как устроена папка

```
roadmap/
├── README.md                     # этот файл: цикл, scope, статус, правила
├── mvp-0-current-flow/           # одна папка на фазу
│   ├── README.md                 # спека + баннер статуса + промт для сессии
│   └── backend-tests.md          # крупные под-шаги — отдельными файлами
├── mvp-1-playable-map/
├── mvp-2-battle-loop/
│   └── polish/                   # большая тема → своя папка с README и файлами по фазам P0–P5
├── mvp-3-inventory/
├── mvp-4-content-balance/
├── mvp-5-hardening/
├── mobs/                         # сквозная тема: доработка мобов (описания, арт, фоны арен)
├── group-battle/                 # сквозная тема: групповой бой N×N (паки → кооп), пока только дизайн
└── assets/                       # сквозная тема (конвейер ассетов), не привязана к одной фазе
```

Правила:

- **Одна папка на фазу, `README.md` внутри — обязателен.** В нём: продуктовый результат, scope по backend/Flutter, DoD, баннер статуса под заголовком и раздел «Промт для сессии» (самодостаточный, копируется целиком в свежую сессию).
- **Статус живёт в двух местах и только там:** таблица ниже и баннер `> **Статус: …**` под H1 каждого документа. Закрыл фазу — обновил оба.
- **Дочерний документ заводится, когда тема не помещается в README** (объёмный аудит, отдельный под-шаг, промт для делегата). Если и он разрастается — папка с README.
- **Файлов в корне `roadmap/` кроме этого README нет.**

## Как пользоваться

1. Очистил контекст → открыл этот файл → нашёл в таблице первую незакрытую фазу.
2. Открыл её README, скопировал раздел «Промт для сессии» **целиком** в новую сессию.
3. По завершении: `flutter analyze` чисто, тесты зелёные → коммит → обновил баннер в README фазы и таблицу здесь.
4. Весь новый код — строго по разделу «Architecture rules (MUST follow)» в `troy-flutter/CLAUDE.md`, эталон — фича `auth` (`lib/features/auth/**`). Backend — по корневому `troy/CLAUDE.md`.

## Статус фаз

Галочка у фазы — её DoD закрыт. Внутри README каждой фазы такие же чек-листы по каждому пункту scope и DoD.

### Сделано

- [x] **MVP-0 — flow auth → персонаж → карта.** `character` на Clean Architecture, backend тест-фундамент. → [mvp-0-current-flow/](./mvp-0-current-flow/README.md), [backend-tests.md](./mvp-0-current-flow/backend-tests.md)
- [x] **MVP-1 — playable map.** Реальная геопозиция, мобы с backend, персональная видимость, бой только в радиусе, вектор-тайлы. → [mvp-1-playable-map/](./mvp-1-playable-map/README.md)
- [x] **MVP-2 — battle loop.** Real-time server-authoritative бой, XP/level/loot. → [mvp-2-battle-loop/](./mvp-2-battle-loop/README.md)

### В работе

- [ ] **MVP-2 · polish — живость боя.** → [polish/](./mvp-2-battle-loop/polish/README.md)
  - [x] P0 контракт событий · [x] P1 отзывчивость и читаемость · [x] P4 «Арена» · [x] P3 старт/результат/level-up · [x] P5 лента намерений
  - [ ] P2 звук, VFX, спрайты hit/death, фоны арен — **код готов, ждёт файлов ассетов**
- [ ] **MVP-3 — профиль, инвентарь, экипировка.** → [mvp-3-inventory/](./mvp-3-inventory/README.md)
  - [x] Клиент: Hero-экран (профиль + кукла + мешок) на реальном API, тесты зелёные
  - [x] Бэкенд: профиль, инвентарь, equip/unequip, очки атрибутов, computed stats
  - [ ] Бэкенд-гэпы [#1–#3](./mvp-3-inventory/backend-gaps.md) (description, consumables, discard) и решение по class restrictions
  - [ ] Визуальный отклик на смену статов после equip
  - [ ] [Redesign](./mvp-3-inventory/redesign.md) — мешок отдельным экраном; прототип готов, код не начат
- [ ] **mobs — доработка мобов** (описания в БД/админке, фон арены на моба, карточки, арт-пилот). → [mobs/](./mobs/README.md)
- [ ] **group-battle · этап 1 — паки (1 игрок × N мобов).** Взят 01.09 (осознанно раньше закрытия MVP-3). Спека — [stage-1-packs.md](./group-battle/stage-1-packs.md), прототип — battle-screen-pack.html; этап 2 (кооп) — после MVP. → [group-battle/](./group-battle/README.md)
- [ ] **assets — конвейер ассетов.** → [assets/](./assets/README.md)
  - [x] Шаг 0 проба стиля · [x] Шаг 1 инструментарий
  - [ ] Шаг 2 классы — `knight` перегенерирован, ждёт проверки на устройстве; остальные классы дальше
  - [ ] Шаги 3–6: мобы, предметы, hi-res, замена старых ассетов

### Не начато

- [ ] **MVP-4 — контент и баланс.** Инфраструктура есть (seed одной командой, админка контента, рендер спрайтов/rarity/level), сам контент 1–10 lvl и баланс — нет. → [mvp-4-content-balance/](./mvp-4-content-balance/README.md)
- [ ] **MVP-5 — hardening.** Последний шаг фазы — **локализация** (описания классов/скиллов на EN, см. ниже). Из списка уже закрыто: health endpoints, refresh access-токена, docker compose, seed, Swagger-тоггл. Остальное открыто. → [mvp-5-hardening/](./mvp-5-hardening/README.md)

**Следующее по порядку:** закрыть MVP-3 (гэпы бэкенда → redesign), параллельно гнать assets (классы → мобы), чтобы разблокировать P2 боя, затем MVP-4.

Старая нумерация (встречается в коммитах и заметках): Шаг 1 → MVP-0, Шаг 1Б → `mvp-0/backend-tests.md`, Шаг 2 → MVP-1, Шаг 3 → MVP-2, Шаг 3Б → `mvp-2/polish/`, Шаг 4 → MVP-3, Шаг 4Б → `mvp-3/redesign.md`, Шаг 5 → MVP-4, Шаг 6 → MVP-5. Файлы `mvp.md` и `execution-plan.md` слиты в этот README, `asset-pipeline.md` → `assets/`.

## Scope MVP

Входит:

- Email auth: регистрация, логин, refresh token.
- До 8 персонажей на аккаунт.
- Warrior и Mage.
- Активный персонаж.
- Карта с реальной геопозицией игрока.
- Отображение ближайших мобов.
- Проверка дистанции до моба перед боем.
- Реальный бой с backend state.
- XP, level progression, loot.
- Инвентарь и экипировка.
- Базовый профиль персонажа.
- Seed-контент для одной тестовой зоны.

Не входит:

- Rogue.
- PvP.
- Торговля (в том числе продажа предметов из инвентаря).
- Гильдии.
- Квесты.
- Социальные механики.
- Продвинутый procedural spawning.
- Production-grade moderation/admin panel.
- Групповой бой (паки мобов, кооп) — отдельная тема [group-battle/](./group-battle/README.md), после MVP.

## Definition of Done для MVP

- Новый пользователь может зарегистрироваться и войти.
- Если персонажей нет, пользователь обязан создать персонажа.
- Если персонажи есть, пользователь может выбрать активного.
- На карте используется реальная позиция устройства.
- Мобы приходят с backend, а не захардкожены на клиенте.
- Бой нельзя начать вне допустимого радиуса.
- Победа в бою меняет состояние персонажа: XP, level при необходимости, loot.
- Игрок видит полученный лут и может экипировать предмет.
- Экипировка меняет computed stats.
- App restart не ломает auth и active character state.
- Backend и Flutter проходят статическую проверку и тесты.

## Зафиксированные решения

- **Архитектура (Flutter):** Clean Architecture, feature-first. Слои `domain / data / presentation`. Подробности — `troy-flutter/CLAUDE.md`.
- **Ошибки:** репозитории возвращают `Either<Failure, T>`; единый `mapErrorToFailure` (`lib/core/error/`); presentation не видит DTO и не парсит `DioException`.
- **DI:** ручной модуль на GetIt (`lib/app/di/injection.dart`). `injectable` не используем.
- **Навигация выбора персонажа:** успешный `select`/`create` → `router.replaceAll([HomeShellRoute])` (всегда на карту). Экран выбора не «остаётся». Нельзя тапать уже активного (`onTap = null` при `isActive`). Во время запроса — спиннер на карточке, список не пропадает.
- **Бой:** real-time, server-authoritative, WS-only. Никаких game-authoritative расчётов на клиенте. Контракт — [battle-session.md](../technical/battle-session.md).
- **Мобы:** персональная видимость — убитый моб исчезает только для убившего персонажа (`CharacterKill`), недельный сброс в среду 00:00 UTC.
- **Тесты:** стек `flutter_test` + `mocktail` (НЕ `bloc_test` — несовместим с Flutter 3.44). **Тесты — часть DoD каждой фазы, не откладываются в MVP-5.**
- **Ветка работы:** `main`. Под крупную фазу можно заводить отдельную ветку и вливать ff, либо коммитить прямо в main.

## Тестирование (для всех фаз)

Пишем по ходу, не в конце. Стек: `flutter_test` + `mocktail`. `test/` зеркалит `lib/`. Прогон — `flutter test`.

Минимум на каждую фичу:

- **bloc** — на каждое событие верная цепочка стейтов (`Loading → Success/Failure`), репозиторий замокан;
- **repository_impl** — datasource замокан: успех → `Right(entity)`, разные ошибки → `Left(<нужный Failure>)` (заодно покрывает `mapErrorToFailure`);
- **mappers** — DTO→entity, чистые функции, таблица кейсов;
- **widget-smoke** — точечно для критичных экранов (бой, карта, выбор персонажа), не весь UI.

Backend (troy-backend) — **Jest + @nestjs/testing** (`npx nx test game-core`). Фундамент поставлен в [mvp-0/backend-tests.md](./mvp-0-current-flow/backend-tests.md); каждая backend-фаза покрывает тронутую логику unit-тестами (мок Prisma/NATS/Redis); e2e — в MVP-5. Детали — раздел «Testing» в корневом `troy/CLAUDE.md`.

Эталон тестов — фича `auth`. Новые фичи зеркалят её структуру тестов так же, как код зеркалит код `auth`.

**Нагрузочные / перф — не per-phase, а гейт в MVP-5:** прогон по стабильному core loop (k6/artillery/autocannon), горячие пути `GET /map/entities`, `POST /battle/start`, WS `character:move`, латентность NATS-RPC. Сначала baseline, потом оптимизация. Кандидат на кэш — активный персонаж читается из Postgres на каждый запрос; выносить в Redis **только если load-тесты подтвердят**.

## Делегирование

Механическую часть (раскладка слоёв строго по эталону `auth`, вёрстка по прототипу) — делегату (codex/GLM) с DoD из промта фазы; Opus — на ревью и нетривиальную логику (бой, навигационные решения, баланс). Мелкие правки — самому.

## Источники требований

- Game loop: [overview.md](../game-design/overview.md)
- Классы: [classes.md](../game-design/classes.md), карточки — [classes/](../classes/README.md)
- Статы и формулы: [stats-and-formulas.md](../game-design/stats-and-formulas.md)
- Leveling: [leveling.md](../game-design/leveling.md)
- Бой: [combat.md](../game-design/combat.md), [battle-session.md](../technical/battle-session.md)
- Выбор персонажа: [character-selection.md](../game-design/character-selection.md)
- Auth: [auth.md](../technical/auth.md)
- Геолокация: [geolocation.md](../technical/geolocation.md)
- База данных: [database-schema.md](../technical/database-schema.md)
- Визуал: [pixel-art-design.md](../game-design/pixel-art-design.md), [content-generation.md](../game-design/content-generation.md), прототипы — [design/prototypes/](../design/prototypes/README.md)
- Генерация контента (сквозные гайды): [generation/](../generation/README.md) — новый класс от карточки до устройства
