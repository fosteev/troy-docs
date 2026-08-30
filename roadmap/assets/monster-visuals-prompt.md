# Промт: визуал мобов — спрайты idle/attack + спрайт на каждый скилл (backend + админка)

> **Статус: выполнено** (troy-backend `5245b56` — спрайт-листы мобов, `GET /monsters/:id/visuals`, иконки скиллов; админка — спрайты у мобов и скиллов). Сохранён как спека визуала мобов и образец промта для делегата.

> Промт для исполнителя (ИИ-агента). Выполнять строго по шагам, ничего лишнего не
> рефакторить. Все пути указаны от корня соответствующего репозитория.

## Роль

Ты — аккуратный fullstack-разработчик. Работаешь в двух репозиториях:

- **`troy-backend`** — NestJS + Nx монорепо (api-gateway + game-core + notification-service, NATS, Prisma, PostgreSQL).
- **`troy-admin`** — Vite + React + TypeScript + Ant Design 6 SPA (админка, ходит в api-gateway по REST).

## Задача одним абзацем

Для персонажей (модель `CharacterClass`) уже сделано: иконка + спрайт-листы
анимаций (idle/walk/attack/attackIdle) хранятся в БД как JSON, загружаются и
настраиваются из админки, отдаются клиенту через публичный REST. Нужно сделать
**то же самое для мобов**: у `Monster` появляются спрайт-листы **idle** (стоит)
и **attack** (автоатака), а у каждого скилла моба (`MonsterSkill`) — **свой
спрайт атаки**. Иконка у моба уже есть (`iconUrl`) — её не трогать. Всё
настраивается в админке на существующей странице мобов. Плюс новый публичный
эндпоинт, из которого мобильный клиент заберёт визуал моба.

**Эталон для копирования паттернов — реализация классов.** Прежде чем писать
код, прочитай эти файлы и делай по аналогии:

| Что | Где смотреть (troy-backend) |
|---|---|
| Схема: JSON-поля спрайтов | `libs/shared/prisma/schema.prisma` → `CharacterClass` (spriteIdle/spriteWalk/spriteAttack/spriteAttackIdle), `ClassSkill.spriteAttack` |
| Формат миграции | `libs/shared/prisma/migrations/0011_character_class_sprite_attack_idle/migration.sql` |
| Контракты | `libs/shared/contracts/src/lib/contracts.ts` → `ClassSpriteSheet`, `AdminClassDto`, `CharacterClassListItem` |
| Валидация спрайтов + маппинг в Prisma.Json | `apps/game-core/src/app/admin/class-admin.service.ts` → `validateSprite`, `toSpriteInput`, `CLASS_SELECT` |
| Админ-контроллер gateway | `apps/api-gateway/src/app/admin/admin-classes.controller.ts` + `apps/api-gateway/src/app/dto/admin/class.dto.ts` (`ClassSpriteSheetDto`) |
| Публичный REST | `apps/api-gateway/src/app/character/classes.controller.ts` + `apps/api-gateway/src/app/dto/response/class-response.dto.ts`; NATS-хендлер в `apps/game-core/src/app/character/character.controller.ts` |
| Тесты-эталон | `apps/game-core/src/app/admin/class-admin.service.spec.ts` |

| Что | Где смотреть (troy-admin) |
|---|---|
| Панель загрузки/настройки спрайта (переиспользуемая) | `src/pages/classes/ClassSpritesPanel.tsx` (+ `SpriteAnimatedPreview.tsx`, `spriteUtils.ts`, `useImageNaturalSize.ts`) |
| Спрайт в форме сущности | `src/pages/classes/ClassMainForm.tsx` (тип `SpriteFormValue`, хелперы `toSprite`/`toSpriteForm`) |
| Спрайт в модалке скилла | `src/pages/classes/ClassSkillEditModal.tsx` |
| Текущая страница мобов | `src/pages/monsters/*` (форма `MonsterMainForm.tsx`, скиллы — inline-таблица `MonsterSkillsPanel.tsx` через `Form.List`, replace всего списка) |
| API-клиенты | `src/api/monsters.ts`, `src/api/monsterSkills.ts`, `src/api/uploads.ts` (`uploadSprite` — POST `/admin/uploads/sprite`, уже готов, переиспользовать) |

Формат спрайт-листа один на весь проект (НЕ создавать новый тип):

```ts
interface ClassSpriteSheet {
  url: string;          // webp в S3 (даёт /admin/uploads/sprite)
  columns: number;
  rows: number;
  frameCount: number;   // может быть < columns*rows (неполный последний ряд)
  fps: number;
  skipFrames?: number[]; // 0-based индексы пропускаемых кадров
}
```

---

## Жёсткие правила (нарушение = работа не принята)

1. **НИКОГДА не запускать `prisma migrate dev`** — он дропает вручную созданные
   PostGIS-объекты (`active_spawns`, `SpawnZone.geometry`). Миграцию писать
   руками: папка `libs/shared/prisma/migrations/0012_monster_sprites/` с
   `migration.sql` (по образцу 0011). Применение — только `npm run prisma:migrate`
   (это `migrate deploy`).
2. После правки `schema.prisma` — `npm run prisma:generate`.
3. Не добавлять новые npm-зависимости. В backend версии пиннёные (без `^`/`~`) — не трогать package.json.
4. Комментарии в коде — на русском, в стиле окружающего кода; писать их только там, где код сам себя не объясняет.
5. Ничего не менять в battle-логике, спавне, дроп-таблицах, seed. Мобильный клиент (troy-flutter) — вне скоупа.
6. Тесты — часть DoD: расширить `monster-admin.service.spec.ts` и добавить спеку на публичный сервис визуала.
7. Существующие тесты должны остаться зелёными: `npx nx run-many -t test`.

---

## Часть 1 — troy-backend

### Шаг 1. Схема и миграция

В `libs/shared/prisma/schema.prisma`:

- `model Monster`: добавить `spriteIdle Json?` и `spriteAttack Json?` (комментарий как у CharacterClass: `// ClassSpriteSheet | null — ...`).
- `model MonsterSkill`: добавить `spriteAttack Json? // ClassSpriteSheet | null — анимация атаки под скилл` (по образцу `ClassSkill.spriteAttack`).

Создать `libs/shared/prisma/migrations/0012_monster_sprites/migration.sql`:

```sql
-- Спрайт-листы моба: idle (стоит) и attack (автоатака), JSON ClassSpriteSheet.
ALTER TABLE "Monster" ADD COLUMN "spriteIdle" JSONB;
ALTER TABLE "Monster" ADD COLUMN "spriteAttack" JSONB;
-- Своя анимация атаки на каждый скилл моба.
ALTER TABLE "MonsterSkill" ADD COLUMN "spriteAttack" JSONB;
```

Выполнить `npm run prisma:generate` (миграцию к локальной БД применит
пользователь сам — БД не трогать).

### Шаг 2. Контракты (`libs/shared/contracts/src/lib/contracts.ts`)

- `AdminMonsterDto`: добавить `spriteIdle: ClassSpriteSheet | null;` и `spriteAttack: ClassSpriteSheet | null;`.
- `AdminMonsterCreatePayload`: добавить опциональные `spriteIdle?: ClassSpriteSheet | null;` и `spriteAttack?: ClassSpriteSheet | null;` (update наследуется через `Partial`).
- `AdminMonsterSkillDto`: добавить `spriteAttack: ClassSpriteSheet | null;` (`AdminMonsterSkillInput = Omit<Dto,'id'>` подхватит сам).
- Новый публичный контракт + NATS-паттерн (в `NATS_PATTERNS` рядом с monster-паттернами):

```ts
MONSTER_VISUALS_GET: 'monster.visuals.get',

/** Визуал моба для клиента (GET /monsters/:id/visuals). */
export interface MonsterVisualsRequest { monsterId: string; }

export interface MonsterSkillVisualDto {
  code: string;
  spriteAttack: ClassSpriteSheet | null;
}

export interface MonsterVisualsDto {
  id: string;
  name: string;
  iconUrl: string | null;
  spriteIdle: ClassSpriteSheet | null;
  spriteAttack: ClassSpriteSheet | null;
  skills: MonsterSkillVisualDto[]; // только скиллы с заданным спрайтом можно не фильтровать — отдаём все
}
```

### Шаг 3. game-core: общий валидатор спрайтов

В `class-admin.service.ts` есть приватные `validateSprite(sprite, field)` и
`toSpriteInput(sprite)`. Вынести их **без изменения поведения** в новый файл
`apps/game-core/src/app/admin/sprite-sheet.util.ts` (экспортируемые функции
`validateSpriteSheet`, `spriteSheetToJsonInput`), а в `class-admin.service.ts`
заменить тела приватных методов на вызовы этих функций (публичный интерфейс
сервиса не менять, его тесты должны пройти без правок).

### Шаг 4. game-core: админка мобов (`apps/game-core/src/app/admin/monster-admin.service.ts`)

По образцу class-admin.service:

- В select моба (аналог `CLASS_SELECT` — найди, как monster-admin выбирает поля) добавить `spriteIdle`, `spriteAttack`; в маппинге в `AdminMonsterDto` привести `Json` → `ClassSpriteSheet | null` (как `toDto` у классов).
- В create/update: валидировать оба спрайта через `validateSpriteSheet`, класть через `spriteSheetToJsonInput`; в update — только если поле передано (`!== undefined`), как у классов.
- В replace скиллов: принимать и сохранять `spriteAttack` каждого скилла (валидация тем же хелпером, поле `skills[i].spriteAttack`).

### Шаг 5. game-core: публичный визуал

Новый модуль `apps/game-core/src/app/monster/` (по образцу `character/`):
`monster.module.ts`, `monster.controller.ts` (`@MessagePattern(NATS_PATTERNS.MONSTER_VISUALS_GET)`),
`monster.service.ts` — читает моба по id (select: id, name, iconUrl, spriteIdle,
spriteAttack + `monsterSkills` (code, spriteAttack) с сортировкой по `sortOrder`),
маппит в `MonsterVisualsDto`. Моб не найден → ошибка тем же способом, каким
кидает публичный класс-хендлер в `character.controller.ts`/его сервисе при
неизвестном `classCode` (посмотри и повтори — чтобы gateway вернул 404).
Зарегистрировать модуль в `app.module.ts` game-core.

### Шаг 6. api-gateway

- `apps/api-gateway/src/app/dto/admin/monster.dto.ts` (или где лежат admin-DTO мобов):
  добавить поля спрайтов в response/create DTO по образцу `class.dto.ts` —
  переиспользовать существующий `ClassSpriteSheetDto` (импортировать, не
  дублировать). В create/update DTO — `@ApiPropertyOptional` + `@IsOptional()` +
  `@ValidateNested()` + `@Type(() => ClassSpriteSheetDto)`. В DTO скилла моба —
  то же для `spriteAttack`.
- `admin-monsters.controller.ts`: если payload собирается перечислением полей
  (как в `admin-classes.controller.ts`) — добавить новые поля и в create, и в
  update, и в replace скиллов. **Проверь внимательно: пропущенное поле в этом
  маппинге — типичная ошибка, TypeScript её не поймает** (payload-поля опциональны).
- Публичный REST: новый `apps/api-gateway/src/app/monsters/monsters.controller.ts`
  (по образцу `character/classes.controller.ts`): `GET /monsters/:id/visuals`,
  `@UseGuards(GatewayJwtGuard)`, swagger-аннотации, шлёт
  `MONSTER_VISUALS_GET` через `NatsRpcService`. Response-DTO — в
  `apps/api-gateway/src/app/dto/response/monster-response.dto.ts` (по образцу
  `class-response.dto.ts`). Зарегистрировать контроллер в модуле gateway (найди,
  где регистрируется `ClassesController`, и сделай так же).

### Шаг 7. Тесты backend

- `monster-admin.service.spec.ts` — дополнить по образцу `class-admin.service.spec.ts`:
  - create с валидным спрайтом → сохраняется (проверить, что в `prisma.…create` ушёл JSON);
  - create/update с битым спрайтом (например, `frameCount > columns*rows` или `fps <= 0` — посмотри, что именно валидирует `validateSpriteSheet`) → ошибка;
  - update без поля спрайта → поле не попадает в data; update с `null` → зануляется;
  - replace скиллов сохраняет `spriteAttack` каждого скилла.
- Новый `apps/game-core/src/app/monster/monster.service.spec.ts`: возвращает DTO с полями и скиллами; неизвестный id → ошибка.
- Прогнать: `npx nx run-many -t test` и `npm run build` — всё зелёное.

---

## Часть 2 — troy-admin

### Шаг 1. Общий компонент спрайтов

Переместить `ClassSpritesPanel.tsx`, `SpriteAnimatedPreview.tsx`, `spriteUtils.ts`,
`useImageNaturalSize.ts` из `src/pages/classes/` в `src/components/sprites/`
(git mv, обновить импорты в файлах classes). Переименовать
`ClassSpritesPanel` → `SpritesPanel`, а тип пропа `name: SpriteFieldName` заменить
на `name: NamePath` из antd (`Form.useWatch` и `Form.Item` принимают NamePath —
проверь, что вложенные пути вида `['skills', 0, 'spriteAttack']` работают).
Страницы классов после переезда должны работать без изменений поведения.

### Шаг 2. API-типы

- `src/api/monsters.ts`: в `Monster` добавить `spriteIdle: ClassSpriteSheet | null;`
  и `spriteAttack: ClassSpriteSheet | null;` (тип импортировать из `src/api/classes.ts`,
  он там уже экспортируется — проверь имя).
- `src/api/monsterSkills.ts`: в тип скилла добавить `spriteAttack: ClassSpriteSheet | null;`.

### Шаг 3. Форма моба (`src/pages/monsters/MonsterMainForm.tsx`)

По образцу `ClassMainForm.tsx`:

- В тип значений формы добавить `spriteIdle?: SpriteFormValue` и
  `spriteAttack?: SpriteFormValue`; при инициализации — `toSpriteForm(...)`, при
  сабмите — `toSprite(...)`. Хелперы и тип `SpriteFormValue` уже экспортируются
  из `spriteUtils.ts` (после шага 1 — `src/components/sprites/spriteUtils.ts`).
- В разметку добавить `Row` с двумя `SpritesPanel`:
  «Стоит (карта/батл)» — name `spriteIdle`, «Автоатака (батл)» — name
  `spriteAttack`. Дефолты сетки взять как у классов (`{ columns: 4, rows: 6,
  frameCount: 19, fps: 10 }`).

### Шаг 4. Спрайт в скиллах моба (`src/pages/monsters/MonsterSkillsPanel.tsx`)

Скиллы редактируются inline-таблицей через `Form.List name="skills"`. Встроить
панель спрайта прямо в строку нельзя — сделать так:

- Добавить колонку «Спрайт»: кнопка, текст — `✓` если у строки задан
  `spriteAttack`, иначе `—`.
- Клик открывает `Modal` с `SpritesPanel`, привязанной к полю
  `['skills', index, 'spriteAttack']` той же формы (через проп `name` как NamePath).
  В модалке достаточно панели + кнопки «Закрыть» (значение и так живёт в форме);
  кнопка «Убрать спрайт» — `form.setFieldValue(['skills', index, 'spriteAttack'], undefined)`.
- При сабмите replace-запроса маппить `spriteAttack` через `toSprite(...)` (не
  забыть: остальные поля скилла не трогать).
- Проверь, что при удалении/переупорядочивании строк `Form.List` значение
  спрайта едет вместе со строкой (antd это делает сам, но убедись, что колонка
  читает значение по `field.name`, а не по внешнему индексу).

### Шаг 5. Список мобов (`src/pages/monsters/MonstersPage.tsx`)

В таблицу добавить колонку «Спрайты» с тегами, как в `ClassesPage.tsx`
(колонка «Спрайты»): `стоит ✓/—`, `атака ✓/—` (зелёный если задан).

### Шаг 6. Проверка админки

`npm run build` (tsc + vite) — без ошибок. Ничего в других страницах не ломать.

---

## Definition of Done (чеклист)

- [x] Миграция `0012_monster_sprites` написана руками, `prisma migrate dev` не запускался.
- [x] `npm run prisma:generate` выполнен, backend собирается: `npm run build`.
- [x] Все backend-тесты зелёные: `npx nx run-many -t test` (включая новые).
- [x] Admin CRUD мобов принимает/возвращает `spriteIdle`/`spriteAttack`; replace скиллов — `spriteAttack` на скилл; невалидный спрайт отклоняется с понятной ошибкой.
- [x] `GET /monsters/:id/visuals` (JWT) отдаёт `{ id, name, iconUrl, spriteIdle, spriteAttack, skills: [{ code, spriteAttack }] }`, на неизвестный id — 404; эндпоинт виден в Swagger.
- [x] В админке: у моба два спрайт-слота с загрузкой/превью (как у классов), у каждого скилла — свой спрайт через модалку, в списке мобов — теги наличия спрайтов.
- [x] Страницы классов работают как раньше (компоненты переехали без регрессий), `npm run build` админки зелёный.
- [x] Никаких новых зависимостей, никакого рефакторинга вне описанных шагов.

## Отчёт по завершении

Кратко: что сделано по шагам, вывод прогона тестов и билдов (обеих реп), список
изменённых/новых файлов. Если что-то из инструкции не сошлось с реальным кодом
(другие имена файлов/полей) — напиши, что нашёл и как поступил.
