# Мобы — доработка до уровня классов

> **Статус: фаза A сделана (30.08), B–D открыты.**

Сквозная тема (как `assets/`): довести мобов до того же стандарта, что классы после 30.08 —
описания для игрока, полный арт-конвейер, карточки в доках, персональный фон арены.

## Продуктовый результат

Игрок видит у моба: имя, описание (тап по маркеру / интро боя), уникальный фон арены, читаемые
названия скиллов в логе и ленте намерений (вместо «Stun Slam» из кода). Контент-мейкер заводит
моба целиком из карточки + манифеста без ручных правок БД.

## Фазы

### A. БД / API / админка — [x] сделано 30.08

- [x] `Monster.description` (текст игроку), `Monster.arenaBackground` (персональный фон арены,
      приоритет над фоном зоны: `monster.arenaBackground ?? zone.arenaBackground` в снапшоте боя)
- [x] `MonsterSkill.name` (клиент «очеловечивал» код: `mob_stun_slam` → Stun Slam) и
      `MonsterSkill.description`
- [x] Миграция `0016_monster_descriptions_arena` (только ADD COLUMN, `migrate deploy`)
- [x] Контракты + admin API + Swagger; клиентские DTO: `MonsterVisualsDto.description`,
      `MonsterSkillVisualDto.name`
- [x] Админка: «Описание» у моба, слот «Фон арены» (как у зоны), «Название»/«Описание» у скилла
- [x] Seed: поля у существующих моб-скиллов (`name`), описания мобов — в фазе B вместе с карточками

### B. Доки — карточки мобов

- [ ] `troy-docs/mobs/` — карточка на моба по [_template.md](../../mobs/_template.md)
      (статы/награды/дропы/скиллы с алгоритмом боя/промты арта/фон арены); эталон завести на
      `goblin_warrior`
- [ ] Гайд `generation/mob.md` — сквозной, по образцу [generation/class.md](../../generation/class.md)
- [ ] Описания (RU) 10 seed-мобам — в карточки и в seed; EN — этап локализации MVP-5 (уже учтён)

### C. Конвейер / арт

- [ ] `publish.mjs` mob: `db:`-блоки скиллов (создание недостающих + name/description), заливка
      `arenaBackground`; манифест-пример дополнить
- [ ] Фон арены: решить генератор — RD (`rd_pro__*` 256px, пиксель-арт в стиле боя) vs hi-res
      (Шаг 5, Nano Banana); формат в БД уже `ClassSpriteSheet` 1×1
- [ ] Пилот: goblin_warrior целиком (иконка-маркер, idle/attack/hit/death, скилл, фон) ≈ $1.6;
      **баланс RD $1.54 — пополнить до старта**
- [ ] Боссы (`isElite`): размер 192, стиль `rd_pro__horror` — вынести в `styles/boss.yaml` или
      параметризовать `mob.yaml`

### D. Клиент (Flutter)

- [ ] Имена скиллов моба из `MonsterVisualsDto.skills[].name` (фолбэк — humanize), лог + лента намерений
- [ ] Описание моба: тап по маркеру на карте и/или интро боя
- [ ] Тултип скилла моба (если появится UI) — description
- [ ] Фон арены от моба работает без правок (приходит в снапшоте) — только проверить на устройстве

## DoD

Backend: `npx nx run-many -t test`, build зелёные; migrate deploy на dev; Swagger актуален.
Админка: tsc + build чистые, поля редактируются и сохраняются. Клиент: `flutter analyze` + тесты.
Карточка goblin_warrior заполнена, пилотный моб виден в игре с описанием и фоном.

## Промт для сессии

> Продолжаем тему «Мобы» по `troy-docs/roadmap/mobs/README.md`. Прочитай его целиком, затем
> `troy-docs/mobs/_template.md`, `troy-docs/generation/class.md` (образец гайда),
> `troy-assets/styles/mob.yaml` и `troy-assets/assets/mobs/goblin_warrior.yaml`. Фаза A сделана —
> начни с первой незакрытой галочки фазы B/C/D. Правила: `troy/CLAUDE.md` (backend),
> `troy-flutter/CLAUDE.md` (клиент), карточка = источник правды, seed на dev не гонять,
> `prisma migrate dev` не использовать (только deploy). Баланс RD проверь до генерации.
