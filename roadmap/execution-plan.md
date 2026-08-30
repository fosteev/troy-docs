# Execution Plan — готовые промты

Рабочий плейбук для доведения Troy до playable MVP. Сделан так, чтобы **чистить контекст между шагами**: берёшь следующий невыполненный шаг, копируешь промт целиком в свежую сессию — он самодостаточен.

## Как пользоваться

1. Очистил контекст → открыл этот файл → нашёл первый невыполненный шаг в «Статусе».
2. Скопировал его промт **целиком** в новую сессию.
3. По завершении: `flutter analyze` чисто → коммит → отметил шаг `[x]` здесь.
4. Общий вектор: довести core loop по [mvp.md](./mvp.md), **весь новый код — строго по разделу «Architecture rules (MUST follow)» в `troy-flutter/CLAUDE.md`**, эталон — фича `auth` (`lib/features/auth/**`).

## Зафиксированные решения

- **Архитектура:** Clean Architecture, feature-first. Слои `domain / data / presentation`. Подробности — `troy-flutter/CLAUDE.md`.
- **Ошибки:** репозитории возвращают `Either<Failure, T>`; единый `mapErrorToFailure` (`lib/core/error/`); presentation не видит DTO и не парсит `DioException`.
- **DI:** ручной модуль на GetIt (`lib/app/di/injection.dart`). `injectable` не используем.
- **Навигация выбора персонажа (MVP-0):** успешный `select`/`create` → `router.replaceAll([HomeShellRoute])` (всегда на карту). Экран выбора не «остаётся». Нельзя тапать уже активного (`onTap = null` при `isActive`). Во время запроса — спиннер на карточке, список не пропадает.
- **Тесты:** стек `flutter_test` + `mocktail` (НЕ `bloc_test` — несовместим с Flutter 3.44). **Тесты — часть DoD КАЖДОГО шага, не откладываются в MVP-5.** Что покрывать — см. раздел «Тестирование» ниже и `troy-flutter/CLAUDE.md`.
- **Ветка работы:** `main`. Фундамент, эталон `auth` (Flutter) и backend тест-фундамент уже влиты в `main` в обоих репо. Под крупный шаг можно заводить отдельную ветку и вливать ff, либо коммитить прямо в main.

## Тестирование (для всех шагов)

Пишем по ходу, не в конце. Стек: `flutter_test` + `mocktail`. `test/` зеркалит `lib/`. Прогон — `flutter test` (часть DoD каждого шага).

Минимум на каждую фичу:
- **bloc** — на каждое событие верная цепочка стейтов (`Loading → Success/Failure`), репозиторий замокан;
- **repository_impl** — datasource замокан: успех → `Right(entity)`, разные ошибки → `Left(<нужный Failure>)` (заодно покрывает `mapErrorToFailure`);
- **mappers** — DTO→entity, чистые функции, таблица кейсов;
- **widget-smoke** — точечно для критичных экранов (бой, карта, выбор персонажа), не весь UI.

Backend (troy-backend) — стек **Jest + @nestjs/testing** (`npx nx test game-core`). Тест-фундамент (jest.config + tsconfig.spec + эталонная спека) + покрытие уже написанных сервисов ставится отдельным шагом — см. **Шаг 1Б**. Дальше каждый backend-шаг покрывает тронутую логику unit-тестами (мок Prisma/NATS/Redis); e2e — в hardening. Детали — раздел «Testing» в корневом `troy/CLAUDE.md`.

Эталон тестов — фича `auth` (создаётся в Шаге 1). Новые фичи зеркалят её структуру тестов так же, как код зеркалит код `auth`.

**Нагрузочные / перф — НЕ per-step, а фаза-гейт в MVP-5** (Шаг 6): прогон по стабильному core loop, инструмент k6/artillery/autocannon. Цель — реальные горячие пути: `GET /map/entities`, `POST /battle/start`, WS `character:move` throughput, латентность NATS-RPC. Принцип: сначала baseline, потом оптимизация. Известный кандидат на кэш — активный персонаж читается из Postgres на каждый запрос (battle/profile); вынести в Redis с инвалидацией на `select`, **только если load-тесты это подтвердят** (высокочастотные пути уже на Redis).

## Статус

- [x] Фундамент — `core/error`, `AppScaffold`, `AppBarCloseAction`, `MainAppBar`, правила в CLAUDE.md, фикс резолва зависимостей (коммит `9e4f04c`)
- [x] `auth` → Clean Architecture, эталон (коммит `383cf02`)
- [x] **Шаг 1** — `character` → Clean Architecture + финал MVP-0
- [x] **Шаг 1Б** — Backend: тест-фундамент (Jest + 6 suites/16 тестов; влито в `main`)
- [x] **Шаг 2** — MVP-1: playable map
- [x] **Шаг 3** — MVP-2: battle loop (real-time, server-authoritative; см. [battle-loop.md](./battle-loop.md))
- [ ] **Шаг 3Б** — Battle polish — см. [battle-polish.md](./battle-polish.md), там же чек-лист остатка. P0/P1/P3/P4/P5 закрыты; в **P2** написан весь код (спрайты hit/death моба, фон арены по зоне), не хватает только файлов: SFX и пакет аудио, листы VFX и партиклы крита, сами спрайты hit/death, фоны арен, иконки мобовых скиллов
- [ ] **Шаг 4** — MVP-3: profile + inventory
- [ ] **Шаг 4Б** — Inventory redesign: мешок отдельным экраном по прототипу [design/prototypes/inventory-redesign.html](../design/prototypes/inventory-redesign.html); только клиент, бэкенд не трогаем
- [ ] **Шаг 5** — MVP-4: контент и баланс
- [ ] **Шаг 6** — MVP-5: hardening

---

## Шаг 1 — `character` → Clean Architecture + финал MVP-0

**Цель:** перевести единственную оставшуюся «грязную» фичу на стандарт и на чистой базе доделать flow выбора персонажа.

```
Работаем в /Users/fost/Projects/troy/troy-flutter (Flutter, ветка refactor/clean-arch-foundation).

Прочитай:
- раздел "Architecture rules (MUST follow)" в CLAUDE.md;
- эталонную фичу auth целиком: lib/features/auth/** (domain/data/presentation, DI в lib/app/di/injection.dart);
- troy-docs/roadmap/current-flow.md и troy-docs/roadmap/execution-plan.md (секция "Зафиксированные решения").

Задача A — мигрировать фичу character на тот же шаблон, что и auth:
- domain/entities/character.dart — freezed-модель Character (поля из CharacterSummaryDto: id, name, class, level, isActive);
- domain/repositories/character_repository.dart — абстрактный интерфейс, методы возвращают Future<Either<Failure, T>>;
- data/datasources/character_remote_datasource.dart — обёртка над ApiClient.characters, говорит DTO, кидает на транспорте;
- data/mappers/character_mapper.dart — CharacterSummaryDto → domain Character;
- data/repositories/character_repository_impl.dart — _guard → mapErrorToFailure, маппинг DTO→entity;
- presentation/bloc/character_bloc.dart — на result.fold(), без парсинга DioException;
- presentation/pages/** — bloc через GetIt.I<CharacterBloc>(), ошибки через context.showErrorSnackBar, экраны на AppScaffold + AppBarCloseAction; страницы оперируют domain Character, а не DTO;
- DI: datasource → repository(as интерфейс) → CharacterBloc(factory); удалить старый CharacterRepository и character_model.dart, если заменены.

Задача B — доделать MVP-0 (current-flow.md), с учётом зафиксированных решений:
- успешный select И create → context.router.replaceAll([const HomeShellRoute()]) (всегда на карту);
- нельзя выбрать уже активного: onTap = null при character.isActive;
- во время select — спиннер на тапнутой карточке, список персонажей не пропадает (не полноэкранный лоадер);
- удалить мёртвый стейт CharacterReady, если он больше не эмитится;
- маркер игрока на карте зависит от класса активного персонажа (player_map_marker / map_page).

Задача C — тесты (эталон + покрытие), стек flutter_test + mocktail (без bloc_test):
- создай ЭТАЛОННЫЕ тесты для уже готовой фичи auth (test/features/auth/...): auth_repository_impl (datasource замокан: успех → Right, ошибки → нужный Failure) и auth_bloc (события → последовательность стейтов). Это образец для всех будущих фич;
- по тому же образцу покрой character: character_repository_impl, character_bloc, character_mapper.

DoD: flutter analyze — без issues; flutter test — зелёный (auth + character покрыты на слоях data+bloc+mappers); вручную проходит «создание персонажа → карта» и «выбор персонажа → карта»; повторный запуск сохраняет auth + активного персонажа. Коммить на текущей ветке отдельным коммитом. Отметить Шаг 1 как [x] в execution-plan.md.
```

---

## Шаг 1Б — Backend: тест-фундамент

**Цель:** поставить Jest и покрыть уже написанную (и непротестированную) логику game-core, пока она не обросла регрессиями. Можно делать параллельно с Шагом 1 (разные репо).

```
Работаем в /Users/fost/Projects/troy/troy-backend (NestJS + Nx, Jest).

Прочитай раздел "## Testing" и архитектуру в /Users/fost/Projects/troy/CLAUDE.md.

Задача — тест-фундамент + покрытие существующих сервисов:
1. Настроить Jest для game-core (и api-gateway): jest.config.ts + tsconfig.spec.json под @nx/jest; убедиться, что `npx nx test game-core` запускается.
2. Эталонная unit-спека auth.service (мок PrismaService, JWT, Redis/NATS): хэш пароля, JWT, верификация 6-значного кода и TTL — образец для остальных спек.
3. По образцу покрыть unit-тестами критичную логику (инфраструктуру мокать — Prisma/NATS/Redis):
   - battle.service — формула урона reduction=defense/(defense+100), loot roll, XP/level progression, in-process Player/Inventory;
   - character.service — create/select оставляют ровно одного активного (updateMany isActive=false → нужный true);
   - map.service — distance/сборка DTO (raw SQL мокать на уровне Prisma);
   - spawn-cron.service — добор зоны до threshold 8;
   - inventory.service — equip/unequip + проверка слотов.

DoD: `npx nx test game-core` зелёный; покрыты battle/auth/character/map/spawn/inventory на уровне чистой логики. Коммит в troy-backend. Отметить Шаг 1Б [x] в execution-plan.md.
```

---

## Шаг 2 — MVP-1: playable map

**Цель:** карта на реальной геопозиции, мобы с backend, бой только в радиусе. См. [playable-map.md](./playable-map.md).

```
Работаем в /Users/fost/Projects/troy (Flutter в troy-flutter, backend в troy-backend).

Прочитай:
- troy-docs/roadmap/playable-map.md (scope и DoD);
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

DoD: позиция игрока обновляется на устройстве; мобы приходят с backend; бой только в радиусе; flutter analyze чисто; flutter test зелёный; backend build+тесты зелёные. Коммит. Отметить Шаг 2 [x].
```

---

## Шаг 3 — MVP-2: battle loop

**Цель:** server-driven бой, меняющий состояние персонажа. См. [battle-loop.md](./battle-loop.md), [combat.md](../game-design/combat.md).

> Бой — **real-time, server-authoritative**. Техническая архитектура — [battle-session.md](../technical/battle-session.md). Промт ниже — высокоуровневый обзор шага.

```
Работаем в /Users/fost/Projects/troy (Flutter + backend).

Прочитай:
- troy-docs/roadmap/battle-loop.md, troy-docs/game-design/combat.md, classes.md, stats-and-formulas.md, leveling.md;
- "Architecture rules" в troy-flutter/CLAUDE.md, эталон auth;
- заглушку lib/features/battle/** (37 LOC).

Backend (troy-backend) — battle:
- POST /battle/start проверяет: активного персонажа, существование моба, дистанцию, доступность;
- battle state: HP игрока/моба, class resource (Rage/Mana), cooldowns, active effects, result;
- skill usage, autoattack timing; победа (XP, level progression, loot roll, удаление/деактивация моба); поражение (result, безопасный возврат).

Flutter — фича battle по стандарту (domain/data/presentation):
- domain: BattleState/BattleResult/BattleRound entities, repository-интерфейс (Either);
- data: datasource (POST /battle/start), repo_impl, мапперы;
- presentation: BattleBloc, экран боя из backend-состояния (HP, Rage/Mana, cooldowns, cast/progress, result); НИКАКИХ game-authoritative расчётов на клиенте; после победы — XP/level up/loot; после боя — возврат на карту.

Тесты (по эталону auth): battle repository_impl, BattleBloc, мапперы; backend — integration на battle result (XP/level/loot/деактивация моба).

DoD: бой проходится от старта до результата; результат сохраняется в backend; XP/loot не теряются после рестарта; flutter analyze чисто; flutter test зелёный; backend тесты зелёные. Коммит. Отметить Шаг 3 [x].
```

---

## Шаг 4 — MVP-3: profile + inventory

**Цель:** игрок видит прогресс и усиливает персонажа предметами. См. [inventory-profile.md](./inventory-profile.md).

```
Работаем в /Users/fost/Projects/troy (Flutter + backend).

Прочитай:
- troy-docs/roadmap/inventory-profile.md, troy-docs/game-design/stats-and-formulas.md, leveling.md;
- "Architecture rules" в troy-flutter/CLAUDE.md, эталон auth;
- заглушки lib/features/profile/** и lib/features/inventory/**.

Backend (troy-backend) — проверить/добить:
- профиль активного персонажа; инвентарь; equip/unequip; проверка слотов и class restrictions;
- computed stats = base + level growth + free attribute points + equipment bonuses.

Flutter — две фичи profile и inventory по стандарту (domain/data/presentation):
- profile: entity Player + computed stats, repo (Either), ProfileBloc, экран (имя, класс, уровень, XP progress, статы, computed);
- inventory: entity InventoryItem, repo (Either), InventoryBloc, экраны (список с rarity/slot/equipped, equip/unequip, визуальный отклик на смену статов).

Тесты (по эталону auth): profile + inventory repository_impl, блоки, мапперы; backend — тест на equip/unequip и пересчёт computed stats.

DoD: полученный в бою предмет появляется в инвентаре; equip/unequip работает; экипировка меняет computed stats; UI обновляется без рестарта; flutter analyze чисто; flutter test зелёный; backend тесты зелёные. Коммит. Отметить Шаг 4 [x].
```

---

## Шаг 4Б — Inventory redesign

**Цель:** мешок — отдельный экран, а не хвост Hero-скролла; экипировка из слота, сравнение с надетым, фидбэк по статам. Прототип (интерактивный, открыть в браузере): [design/prototypes/inventory-redesign.html](../design/prototypes/inventory-redesign.html). Контекст и решения — раздел «Редизайн (Шаг 4Б)» в [inventory-profile.md](./inventory-profile.md). Делается после Шага 4, **только Flutter** — новых эндпоинтов не требует.

**Зафиксировано в прототипе:**
- Нет empty-state текста — пустой мешок это просто dashed-сетка.
- Нет Sell — экономика не в инвентаре.
- Discard и Use — только когда появятся эндпоинты (gaps #2, #3 в [inventory-backend-gaps.md](./inventory-backend-gaps.md)); мёртвых кнопок в приложении не шипим.
- Скругления: прототип рисует sharp pixel-рамки по redesign-prompt, приложение живёт на `tokens.radius*`. В этом шаге **используем токены приложения** — переход на sharp-углы это отдельный шаг по всей дизайн-системе, не по одному экрану.

```
Работаем в /Users/fost/Projects/troy/troy-flutter.

Прочитай:
- troy-docs/design/prototypes/inventory-redesign.html — открой в браузере, прокликай 5 экранов; заметки под каждым телефоном и таблица «What it costs» — это ТЗ;
- troy-docs/roadmap/inventory-profile.md (раздел «Редизайн (Шаг 4Б)») и inventory-backend-gaps.md;
- lib/features/profile/** — текущий Hero-экран (HeroCubit, HeroSnapshot, InventorySection, EquipmentPanel, ItemInspectSheet, ItemGlyphIcon);
- lib/features/map/presentation/widgets/map_nav_bar.dart — текущий bottom nav (BACKPACK · MAP · MENU);
- "Architecture rules" в troy-flutter/CLAUDE.md.

Структура:
- features/inventory/ — presentation-фича (InventoryPage + виджеты). Domain (InventoryItem, HeroSnapshot, HeroSlot) остаётся в features/profile/domain, InventoryPage работает поверх того же HeroCubit — это осознанно: один снапшот на оба экрана, без цикла зависимостей между фичами. Пустые .gitkeep в inventory/domain и inventory/data удалить.
- Общие вещи (ItemGlyphIcon, RarityColors, EquipSlot, ItemCell, DashedBox) → lib/shared/widgets/ (или оставить в profile, если тянет только inventory — решить по факту использования).
- HeroCubit — один инстанс на HomeShell (провайдить выше обоих экранов), load() один раз, оба экрана слушают.

Навигация:
- BACKPACK в nav bar → InventoryPage. Hero (профиль, полная кукла со спрайтом, атрибуты, derived) — четвёртый таб HERO по прототипу. Если четыре таба ломают текущий бар с большим центральным MAP — HERO действием в app bar инвентаря. Выбрать одно, зафиксировать в inventory-profile.md.
- Из HeroPage секцию InventorySection убрать; EquipmentPanel там остаётся.

InventoryPage (экран 1 прототипа):
- App bar: заголовок + золото (справа). Футер с золотом убрать.
- Полоса куклы: 6 EquipSlot ~48px с подписями слотов. Тап по слоту → slot sheet (ниже) + подсветка в сетке предметов, подходящих в этот слот (остальные dim, не скрывать).
- Вместимость: сегментированный бар used/40 (capacity — константа HeroSnapshot.capacity), при >= 90% — tokens warning.
- Чипы фильтра как сейчас + sort-чип: rarity ↓ (default) / newest / type. Accessory фильтруем по slot == ring.
- Сетка 4 колонки, min 12 ячеек, добивка dashed (как сейчас). Бейджи ячейки: quantity (как сейчас), метка слота (3 буквы, низ-лево), NEW (верх-лево), ▲ апгрейд (низ-право, success) если slot != null и суммарный бонус > суммарного бонуса надетого в этот слот (или слот пуст).
- NEW: локальный набор «виденных» itemId (SharedPreferences); предмет перестаёт быть NEW после открытия его карточки или equip. Бэкенд acquiredAt не ждём.
- Пустой мешок — просто dashed-сетка, без текста и CTA. Loading — тот же каркас (dashed ячейки), без центрального спиннера.

Item sheet (экраны 2 и 4):
- Шапка как сейчас (glyph, имя цветом rarity, «Rarity · Type · Slot ×N»). Описание — только если item.description != null.
- Бонусы — строками: label | значение | дельта против надетого в этот слот (▲ +N success / ▼ -N error / — muted). Строка «VS. EQUIPPED <имя>» над таблицей, если в слоте что-то есть. Для уже надетого — без дельты, кнопка UNEQUIP вместо EQUIP.
- Consumable: строка эффекта и кнопка USE со степпером — ТОЛЬКО когда закрыт gap #2; до этого sheet информационный. Discard — ТОЛЬКО когда закрыт gap #3.
- Equip/Unequip → закрыть sheet → тост с дифом computedStats старого и нового снапшота (например «PHYS ATK +7 · ARMOR -2»), а не суммой бонусов предмета. Тост — shared виджет, если его ещё нет.

Slot sheet (экран 3):
- Тап по слоту куклы (и в InventoryPage, и в EquipmentPanel на Hero) → sheet: что надето (glyph, имя, чипы бонусов) + UNEQUIP; ниже «SWAP FOR» — горизонтальный список предметов мешка с подходящим slot, отсортирован по rarity, с ▲ у апгрейдов; тап = equip (бэкенд сам снимает предыдущее). Пустой слот — без блока «Equipped», сразу список. Мгновенный unequip по тапу на слот убрать.
- Во время мутации (HeroCubit._mutationInFlight) — кнопки sheet disabled, тап по ячейкам игнорируется; после ответа sheet закрывается.

Тексты — в assets/translations/en.json и ru.json (ключи hero.* / inventory.*), без хардкода.

Тесты (flutter_test + mocktail, по эталону auth):
- unit: сортировка/фильтр/подсветка по слоту, эвристика апгрейда, диф computedStats для тоста, NEW-набор;
- widget-smoke InventoryPage: сетка рендерит bag без надетых, чип фильтрует, тап по слоту открывает slot sheet со «SWAP FOR» только подходящих, тап по предмету открывает item sheet с дельтой;
- HeroCubit: существующие тесты не ломаем; если cubit поднимается на уровень shell — тест на один load для обоих экранов.

DoD: BACKPACK открывает отдельный экран инвентаря по прототипу; Hero без мешка; equip из slot sheet и из item sheet работает против реального бэкенда, после equip/unequip тост с дифом статов; NEW/▲/бейдж слота на ячейках; пустой мешок = dashed-сетка; нет кнопок без эндпоинта; flutter analyze чисто; flutter test зелёный. Коммит. Отметить Шаг 4Б [x] в execution-plan.md и обновить раздел «Редизайн (Шаг 4Б)» в inventory-profile.md (что реализовано, что отложено).
```

---

## Шаг 5 — MVP-4: контент и баланс

**Цель:** хватает контента, чтобы проверить loop и прогрессию. См. [content-balance.md](./content-balance.md).

```
Работаем в /Users/fost/Projects/troy (в основном backend troy-backend + game-design доки).

Прочитай:
- troy-docs/roadmap/content-balance.md;
- troy-docs/game-design/classes.md, combat.md, leveling.md, stats-and-formulas.md.

Game-design — дописать недостающие доки: game-design/monsters.md, loot-and-items.md, inventory-and-equipment.md.
Контент/баланс: мобы 1–10 lvl, drop tables, минимум предметов (weapon/armor/accessory), баланс XP до 10 lvl, баланс Warrior/Mage, skill set стартовых уровней.

Backend (troy-backend) — seed: zones, monsters, items, drop tables, spawn rules для тестовой зоны; повторяемый dev seed одной командой (без ручных SQL-правок).
Flutter — иконки/спрайты основных мобов, отображение rarity, level/threat, result screen с loot+XP.

Тесты: на формулы/баланс, где они есть (XP-таблица, расчёт урона/защиты, drop-роллы) — unit-тесты на детерминированную часть; smoke на воспроизводимость seed.

DoD: есть тестовая зона с мобами; loot progression; Warrior и Mage playable до 10 lvl; seed пересоздаётся одной командой; тесты формул зелёные. Коммит. Отметить Шаг 5 [x].
```

---

## Шаг 6 — MVP-5: hardening

**Цель:** закрыть технические дыры для теста на реальных устройствах. См. [hardening.md](./hardening.md).

```
Работаем в /Users/fost/Projects/troy (backend + Flutter + DevOps).

Прочитай troy-docs/roadmap/hardening.md.

Backend (troy-backend):
- logout / revocation refresh-токена; WebSocket CORS whitelist; rate limiting WS-событий;
- anti-cheat: checkSpeed() не должен разрешать teleport при timeDelta = 0;
- логировать ошибки отправки email; проверить health endpoints в Docker;
- integration/e2e на сквозной флоу: auth → character → battle result → inventory equip (unit-тесты сервисов уже есть с прошлых шагов — здесь закрыть пробелы).

Flutter (troy-flutter):
- unit-тесты блоков/репозиториев уже есть с прошлых шагов — здесь закрыть пробелы покрытия и добавить widget-smoke ключевых экранов; опционально вернуть bloc_test (совместимой с Flutter 3.44 версией) как сахар для уже написанных тестов;
- обработка истёкшего access token; recovery при refresh failure; единый error UI;
- smoke test auth → character → map; проверка iOS/Android location permissions; release config для backend base URL.

DevOps: docker compose поднимает рабочий dev backend; seed одной командой; Swagger в dev и отключаем в prod; задокументировать локальный запуск backend + Flutter.

Перформанс/нагрузочные (фаза-гейт, не per-step): инструмент k6 или artillery; сценарии по горячим путям — GET /map/entities, POST /battle/start, WS character:move (N клиентов с движением), латентность NATS-RPC валидации. Снять baseline (p50/p95/RPS). По результатам решить про кэш активного персонажа в Redis (инвалидация на select) — не оптимизировать без данных.

DoD: backend проходит build и тесты (unit+integration); flutter analyze чисто и flutter test зелёный; docker compose поднимает рабочий backend; снят перф-baseline горячих путей (p50/p95/RPS); MVP можно поставить на устройство и пройти core loop без ручных SQL/API вмешательств. Коммит. Отметить Шаг 6 [x].
```

---

## Памятка по делегированию

Механическую часть (раскладка слоёв строго по эталону `auth`) можно отдавать codex/kimi с DoD из соответствующего промта, Opus — на ревью и на нетривиальную логику (бой, navigation-решения, баланс). Мелкие правки — самому.
