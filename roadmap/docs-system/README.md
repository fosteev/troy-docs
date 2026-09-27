# Доки — карта системы и синхронизация с кодом

> **Статус: в работе (27.09).** Сессия 1 (каркас + пилот battle/world) — готова, принята ревью 27.09.
> Ждёт гейта: пользователь читает `system/battle.md`/`system/world.md`, подтверждает формат. Сессии 2–3 — после гейта.

Проект растёт быстрее, чем читается: 68 md / ~12k строк, из них roadmap — 32 файла / 5.1k строк
(как **планировали**), а «как устроено **сейчас**» — 4 файла в `technical/`. Битых ссылок и прямых
противоречий нет (аудит 27.09), беда в навигации: знание о городах, предметах, кастах, тайлах, админке,
загрузках размазано по roadmap-темам, карты «что где в коде» нет, индекс `README.md` устарел
(перечисляет `[TODO]`-файлы, не знает про cities/items/combat-casting/zones/vendors).

## Продуктовый результат

- `system/` — карта системы: страница на подсистему, ≤ 1–2 экрана, **текущее поведение, сверенное с
  кодом**, пути в код, «где потрогать руками», ссылки на technical/roadmap как «глубже» и «история».
- Свежесть проверяема: у страницы во frontmatter — дата и sha репозиториев, на которых её сверяли;
  `scripts/docs-check.py` показывает, сколько коммитов в её коде прошло с тех пор, ловит битые
  ссылки и несуществующие пути/символы кода.
- `README.md` — точка входа по назначению (сейчас / контракты / замысел / контент / планы).
- `CHANGELOG.md` — строка на закрытую тему/этап.
- Правило процесса: закрыл этап → обновил страницу подсистемы (+ `verified`/sha) и строку в CHANGELOG.

## Решения

1. **Ничего не переносим и не переименовываем.** На пути `roadmap/**`, `technical/battle-session.md`,
   `roadmap/cities|items|combat-casting/`, `design/prototypes/*` ссылаются `troy/CLAUDE.md`, скиллы
   `troy-*`, memory. roadmap остаётся историей и планами как есть.
2. **`system/` — новый слой поверх**, не замена `technical/`: system = обзор «сейчас» (что, как, где),
   technical = глубокие контракты (WS-события, схема БД). system ссылается вниз, не дублирует.
3. **Источник правды для system — код**, не roadmap. roadmap/technical — подсказка, где искать.
   Расхождение `technical/*` с кодом — исправить technical (это справочник). Расхождение
   `game-design/*` с кодом — **не править** (это замысел), записать в раздел страницы «Отличия от
   геймдизайна».
4. **Страницы (10):** `infra`, `auth`, `characters`, `battle`, `items`, `mobs`, `world` (города → соты →
   зоны + еженедельный респаун), `map` (позиция, anti-cheat, сущности, тайлы, клиентская карта),
   `admin` (разделы, admin-guard, загрузки S3/sharp), `client` (Flutter: архитектура, сеть, состояние).
   Vendors, кооп, редизайн мешка, зелья — только в планах, в system/README списком со ссылками на roadmap.
5. **Ссылки на код — строкой в бэктиках, не markdown-ссылкой** (vault Obsidian = troy-docs, код вне
   его): `` `troy-backend/apps/game-core/src/app/battle/battle.service.ts:BattleService` `` — путь от
   `/Users/fost/Projects/troy`, после `:` — имя символа (класс/функция/метод), **без номеров строк**
   (гниют). Каталог — со слэшем на конце.
6. **Ссылки между доками — markdown, относительные** (`[battle-session](../technical/battle-session.md)`),
   без `[[wikilinks]]`. Диаграммы — mermaid (рендерит и Obsidian, и GitLab), только где поток ≥ 3
   участников.
7. **Frontmatter страницы** (Obsidian покажет как свойства):
   ```yaml
   ---
   verified: 2026-09-27
   backend: 7fe8024      # git -C troy-backend rev-parse --short HEAD на момент сверки
   flutter: 8be7b47
   admin: dbb54d4
   paths:                # что читали при сверке; по ним docs-check считает коммиты «после»
     - troy-backend/apps/game-core/src/app/battle/
     - troy-flutter/lib/features/battle/
   ---
   ```
   Ключ репо — только если в `paths` есть путь этого репо.
8. **Язык — русский**, стиль существующих доков. Длина страницы — цель 60–90 строк, потолок 120.
9. Правило процесса в скиллах `troy-plan-review`/`troy-continue`, правка `troy/CLAUDE.md`
   (`admin/` → `troy-admin/`, указатель на system) — делает приёмка (Opus), не исполнитель.

## Шаблон страницы

```markdown
---
(frontmatter, см. решение 7)
---
# <Подсистема>

> Одной фразой — что это для игрока / для админа.

## Как работает
5–10 пунктов о текущем поведении. Неочевидное утверждение — с путём в код `repo/path:Symbol`.
Опционально mermaid.

## Данные
Модели/таблицы и важные поля; что живёт в raw SQL вне Prisma.

## Контракт
REST / NATS / WS — имена одной строкой каждое; детали — ссылкой на technical/*.

## Где в коде
| Слой | Путь |  (backend / flutter / admin — только существующие слои)

## Где потрогать
Экран приложения, раздел админки, curl, npm-скрипт — как увидеть руками.

## Конфиг и ручки баланса
env, константы. Нет — раздел опустить.

## Известные дыры
Из «Known issues» `troy/CLAUDE.md`, TODO/FIXME в коде подсистемы. Нет — опустить.

## Отличия от геймдизайна
Где `game-design/*` описывает иначе, чем код. Нет — опустить.

## Глубже и история
technical/…, game-design/…, roadmap-темы в порядке, как подсистема строилась.
```

## Этапы

- [x] **Сессия 1 — каркас + пилот** (sonnet, high).
  - [x] `system/_template.md` — шаблон выше
  - [x] `scripts/docs-check.py` — stale по frontmatter, битые относительные md-ссылки, несуществующие пути/символы кода
  - [x] `system/battle.md`, `system/world.md` — пилотные страницы, сверены с кодом
  - [x] `system/README.md` — карта: сервисы (mermaid), core loop → страницы, таблица подсистем, «только в планах», как читать доки
  - [x] `README.md` — разделы «Структура репозитория», «Документация», «Статус» заменены индексом по назначению
  - [x] `roadmap/README.md` — тема `docs-system/` в дереве и в «В работе»
  - [x] `python3 scripts/docs-check.py` — exit 0
- [ ] **Гейт: пользователь читает `system/battle.md` и `system/world.md` в Obsidian** — формат помогает
  разобраться? Правки формата → в шаблон и в «Решения» до сессии 2.
- [ ] **Сессия 2 — auth, characters, items, mobs** (sonnet, high) + правки `technical/*` по найденным расхождениям.
- [ ] **Сессия 3 — map, admin, client, infra** (sonnet, high) + `CHANGELOG.md` (бэкфилл по закрытым темам
  roadmap) + сверка фактов `troy/AGENTS.md` с system (указатель на `system/README.md`, без перестройки файла)
  + раздел боя в `troy-flutter/CLAUDE.md` (описывает пораундовый REST — устарел) → коротко + указатель на
  `troy-docs/system/battle.md`.
- [ ] **Приёмка (opus):** правило «закрыл этап → system + CHANGELOG + docs-check» в `troy-plan-review`,
  `troy-continue` и в правилах `roadmap/README.md`; `troy/CLAUDE.md` — `admin/` → `troy-admin/`, указатель на
  `troy-docs/system/README.md`; коммит troy-docs.

### Ревью сессии 1 (27.09)

Принято. Исполнитель собирал факты двумя research-субагентами и перепроверял grep'ом — ок, выборочная
сверка ревью (kills, крит мобов, формула урона моба, TTL кэша спаунов, `getZones`, канал `battle:stream:{userId}`,
namespace `/game`, `startedAtIso`/`elapsedMs`) — всё совпало с кодом. `technical/battle-session.md` поправлен
верно. Негативный тест `docs-check.py` (битая ссылка + несуществующий символ) — exit 1.

Исправлено ревью:
- Противоречие между пилотами: battle.md — «недельный сброс kills фильтром по дате, не сносом», world.md —
  «cron сносит все kills». В коде верно оба: cron `deleteMany`, а чтения ещё и фильтруют `killedAt >= currentWeekStart()`.
- Путь `libs/shared/...` без префикса репо — docs-check его не проверял; хроника «поправлено в этой сессии»
  на странице system; mermaid: загрузки в S3 идут через api-gateway, gateway тоже ходит в Redis (pub/sub боя);
  невнятный абзац «Свежесть» в system/README.md; в «Где потрогать» боя не было пути через приложение.

Уроки в промты сессий 2–3:
1. Факт, который встречается на двух страницах, — сверить формулировки между ними (а не только с кодом).
2. Каждый путь в бэктиках — с префиксом репо (`troy-backend/…`), иначе docs-check его не видит.
3. На странице system — только факт о системе, без хроники правок («в этой сессии поправлено»).
4. «Где потрогать» — первой строкой, как увидеть руками в приложении/админке, потом dev-способы (curl, WS, скрипты).

Вне скоупа, записано: `game-design/combat.md` — формулы автоатаки устарели (решение 3 — замысел не правим,
расхождения в battle.md); комментарий в `troy-backend/scripts/spawn-run.ts` («8 мобов на зону») — в «Известных
дырах» world.md.

## DoD темы

- 10 страниц в `system/` + README + шаблон; каждая ≤ 120 строк (`wc -l troy-docs/system/*.md`).
- `python3 troy-docs/scripts/docs-check.py` — exit 0: битых ссылок 0, несуществующих путей/символов кода 0,
  у всех страниц stale = 0 коммитов на момент закрытия.
- `README.md` не содержит `[TODO]`-файлов в дереве и ведёт в `system/README.md` первой ссылкой.
- Пользователь прочитал пилот и хотя бы одну страницу сессии 2–3 и подтвердил, что понятно.

## Промты

### Сессия 1 — каркас + пилот

```
Сессия 1 — доки Troy: каркас system/ + пилот battle/world · Модель: sonnet, effort: high

Работаем в /Users/fost/Projects/troy/troy-docs (git-репо доков; код — соседние репо
/Users/fost/Projects/troy/{troy-backend,troy-flutter,troy-admin}, их только читаем). Задача: завести
слой system/ — «как устроено сейчас», сверенный с кодом, — скрипт проверки свежести и две пилотные
страницы. Стройка с нуля, существующие доки не переносим.

Читай: troy-docs/roadmap/docs-system/README.md (весь — там решения, шаблон страницы, этапы);
/Users/fost/Projects/troy/CLAUDE.md (архитектура бэкенда, Known issues — источник для «Известных дыр»).
Для пилотов как подсказку, где искать (не как источник правды): technical/battle-session.md,
game-design/combat.md, roadmap/group-battle/stage-1-packs.md, roadmap/combat-casting/README.md,
roadmap/cities/README.md. Файлы длиннее 300 строк — сначала `grep -n '^#'`, потом нужный раздел.

Точки входа в код (проверены):
- бой: troy-backend/apps/game-core/src/app/battle/{battle.service.ts, battle-session.store.ts,
  battle.controller.ts, engine/engine.ts, engine/formulas.ts, engine/types.ts};
  WS — troy-backend/apps/api-gateway/src/app/ws/game.gateway.ts (battle:start/action/target/flee/resume);
  клиент — troy-flutter/lib/features/battle/{data,domain,presentation}.
- мир: troy-backend/apps/game-core/src/app/admin/{city-admin.service.ts, city-admin.controller.ts,
  spawn-admin.service.ts}; respawn — troy-backend/apps/game-core/src/app/map/spawn-cron.service.ts;
  хекс-раздача — troy-backend/libs/shared/utils/src/lib/hex-assign.ts; сид — troy-backend/prisma/seed.ts;
  миграция — troy-backend/libs/shared/prisma/migrations/0023_cities_territories/; админка —
  troy-admin/src/pages/{cities,zones,spawn}/.
- схема: troy-backend/libs/shared/prisma/schema.prisma (City, Territory, SpawnZone, Monster, ...).
- sha для frontmatter: backend 7fe8024, flutter 8be7b47, admin dbb54d4 (перепроверь
  `git -C ../troy-backend rev-parse --short HEAD` и т.д. в начале — если HEAD сдвинулся, бери текущий).

Уже решено, не переспрашивать: всё из раздела «Решения» roadmap-файла — ничего не переносить и не
переименовывать; system/ поверх technical/; источник правды — код; technical/* при расхождении
исправлять, game-design/* не трогать (→ «Отличия от геймдизайна»); ссылки на код — бэктиками
`путь:Символ` от /Users/fost/Projects/troy без номеров строк; ссылки между доками — относительный
markdown, без [[wikilinks]]; frontmatter по решению 7; русский; страница 60–90 строк, потолок 120.

Порядок:
1. system/_template.md — шаблон из roadmap-файла (раздел «Шаблон страницы») с frontmatter-заглушкой.
2. scripts/docs-check.py — python3, только stdlib, запуск из любой папки (корень доков — по __file__):
   a) для каждого system/*.md кроме README.md и _template.md: разобрать frontmatter (verified, backend,
      flutter, admin, paths); для каждого path: репо = первый сегмент (troy-backend→backend,
      troy-flutter→flutter, troy-admin→admin), `git -C <troy>/<репо> rev-list --count <sha>..HEAD -- <остаток>`;
      вывести строку `battle.md  verified 2026-09-27  backend +0  flutter +0`; с `-v` — ещё
      `git log --oneline <sha>..HEAD -- <пути>`. Stale — информация, на exit code не влияет;
   b) по всем *.md troy-docs (кроме .git, .obsidian, node_modules): относительные ссылки `](x.md)`,
      `](x.md#якорь)`, `](dir/)` — цель должна существовать; http(s) и mailto пропускать; ссылки внутри
      ```-блоков и `инлайн-кода` пропускать (в roadmap/docs-system/README.md такие есть — это примеры);
   c) по system/*.md: каждый бэктик-фрагмент, начинающийся с troy-backend/ | troy-flutter/ |
      troy-admin/ — путь должен существовать; если после последнего `:` не цифры — это символ, он должен
      встречаться в файле (простой поиск подстроки).
   Exit 1, если есть битые ссылки (b) или пути/символы (c); вывод — список file:line → что не так.
3. system/battle.md и system/world.md — по шаблону, каждое утверждение «Как работает» проверено по коду.
   Нашёл расхождение technical/* с кодом — исправь technical точечно и запиши в отчёт. world.md покрывает
   город → соты → зоны и еженедельный респаун (cron, capacity/TERRITORY_CAPACITY, паки, снос kills).
4. system/README.md — карта: абзац «что за проект и из каких репо»; mermaid-схема сервисов (Flutter и
   админка → api-gateway REST/WS → NATS → game-core → Postgres+PostGIS / Redis; game-core → событие NATS →
   notification-service → Resend/SES; загрузки → S3); core loop (регистрация → персонаж → карта → моб →
   бой → XP/лут → усиление) с указанием страницы на каждый шаг; таблица подсистем (страница | одной
   строкой | verified) — все 10 из решения 4, ещё не написанные помечены «(будет)» без ссылки;
   «Только в планах» — vendors, кооп (group-battle этап 2), редизайн мешка, зелья → ссылки на roadmap;
   «Как читать доки»: system (сейчас) → technical (контракты) → game-design (замысел) → roadmap (история
   и планы); «Свежесть»: команда docs-check.
5. README.md (корень доков) — заменить разделы «Структура репозитория», «Документация», «Статус» одним
   разделом-индексом по назначению: Как устроено сейчас (system/README.md — первой строкой) / Контракты
   (technical/*) / Геймдизайн (game-design/*) / Контент и арт (classes/, mobs/, generation/, design/,
   assets/) / Планы и история (roadmap/README.md). Файлов с [TODO] в индексе не перечислять. Разделы
   выше «Структуры репозитория» не трогать.
6. roadmap/README.md — `docs-system/` в дерево «Как устроена папка» и пункт в «В работе» со ссылкой.
7. Галочки сессии 1 в roadmap/docs-system/README.md — по факту проверки.

DoD: `python3 /Users/fost/Projects/troy/troy-docs/scripts/docs-check.py` — exit 0, battle.md и world.md
с +0; `wc -l system/*.md` — каждая ≤ 120; `grep -rn '\[\[' system/` — пусто. Сломай руками одну ссылку и
один путь кода во временной копии страницы — скрипт должен дать exit 1 (копию потом удалить).

Не делать: страницы кроме battle/world/README/_template; перенос/переименование любых файлов; правки
game-design/*, roadmap/* (кроме п.6–7), кода в соседних репо, ~/.claude, troy/CLAUDE.md, troy/AGENTS.md;
.obsidian/ не трогать; чужие незакоммиченные файлы (.gitignore) не трогать; dev-процессы не запускать;
«заодно улучшить» — нет. Вопрос без ответа в промте — в отчёт, не додумывать.

Не коммитить, не пушить — это сделает приёмка.
Последним сообщением — отчёт: сделано (файлы) / расхождения доков с кодом (док — что написано — что в
коде — исправил ли) / отклонения от плана / не проверено / открытые вопросы. Отчёт — единственное, что
увидит приёмка: без него работа потеряна.
```
