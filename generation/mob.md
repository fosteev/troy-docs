# Генерация нового моба — от идеи до игры

Полный порядок, по образцу [class.md](class.md); здесь — только отличия и точные шаги.
Эталон прохождения: `goblin_warrior` (карточка `mobs/goblin_warrior.md`, манифест
`troy-assets/assets/mobs/goblin_warrior.yaml`). Один моб с одним скиллом ≈ **$1.3–1.6**
кредитов Retro Diffusion (точную цену считает `--dry`).

## Чем моб отличается от класса (канон — `troy-assets/styles/mob.yaml`)

- В бою моб стоит **справа и смотрит ВЛЕВО** (клиент спрайт не зеркалит) — ключевой кадр
  сразу в профиль влево, текстом; edit-поворот из фронта не нужен.
- Нет `keyframeFront`, `keyframeTop`, `portrait`, `walk`, `attackIdle`. Есть **hit**
  (получил удар слева → отдача вправо) и **death** (падает; последний кадр лежит —
  клиент держит его до экрана итога).
- Иконка — не эмблема класса, а **маркер на карте** (рисуется 32–48 px): один доминирующий
  цвет (`accentColor`), золото — только вторичный акцент.
- У мобов нет ресурса — скиллы гейтятся кулдауном и `condition` (алгоритм —
  `game-design/combat.md`); 0–2 скилла, у элиток до 2 (боссы 3–4 — см. ниже).
- Боссы (`isElite`): `kind: boss` в манифесте → шаблон `styles/boss.yaml` (keyframe 192,
  `rd_pro__horror`; фон арены остаётся fantasy). Остальной ход тот же.

## Что понадобится

То же, что для класса (`class.md`, «Что понадобится»): RD-ключ (`source ~/.config/troy/rd.env`),
поднятый backend + креды админки, репо `troy-assets` и `troy-docs`.

## Шаг 1. Карточка моба (дизайн)

`troy-docs/mobs/_template.md` → скопировать в `mobs/<code>.md`, заполнить все `{…}`.
Бюджеты статов/наград по уровням — `game-design/content-generation.md` («Мобы — якорные
значения» + правила интерполяции); множители босса — там же. Санити-чек урона: один скилл
≤ 35% max HP игрока-одноклассника (hp воина ≈ 100 + 24×L), стан+нюк ≤ 50%.

Обязательные тексты (RU; EN — этап локализации MVP-5):
- описание моба → `Monster.description` (тап по маркеру, интро боя, ≤ 220, без чисел);
- на каждый скилл → `MonsterSkill.name` (лог боя, лента намерений) и
  `MonsterSkill.description` (с числом эффекта).

Карточка — источник правды: числа меняются сначала в ней, потом в seed/админке и манифесте.

## Шаг 2. Моб в БД

Publish самого моба **не создаёт** — только находит по `name`. Поэтому сначала завести в
админке (страница Monsters): статы, награды и дроп из карточки. Скиллы можно inline-таблицей
там же — или не заводить: publish создаст недостающие из `db:`-блоков манифеста (Шаг 3).
Базовые 10 мобов живут в `troy-backend/prisma/seed.ts` — изменения дублировать туда (свежая
БД должна воспроизводиться); **на dev seed не гонять** — он чистит kills/inventory.

## Шаг 3. Манифест для генерации

`troy-assets/assets/mobs/<code>.yaml` — переносится из карточки (раздел «Поля манифеста»).
Пример со всеми полями — `goblin_warrior.yaml`. Содержит **только описание**; промты собирает
шаблон `styles/mob.yaml` — его не трогать (единый вид игры).

Поля: `kind: mob`, `code`, `name` (как в БД!), `description` (текст игроку — publish зальёт
в `Monster.description`), `subject` (внешность + цветовая схема, без ракурса/фона/слов
«pixel art»), `emblem`, `accentColor`, `weaponRest`, `attackMotion`, `hitMotion`,
`deathMotion`, `arena` (сцена персонального фона арены: местность + 2–3 детали, без существ
и текста); на каждый скилл (ключ = `MonsterSkill.code` в БД): `name`, `description`,
`icon`, `cast` и `db:` (боевые поля `MonsterSkill` — по нему publish создаст недостающий
скилл). Палитра общая (`palette/troy-dark-gold.png`) — новые цвета через `tools/palette.mjs`.

## Шаг 4. Генерация (по шагам, с проверкой глазами)

```bash
cd troy-assets && source ~/.config/troy/rd.env
node tools/gen.mjs assets/mobs/<code>.yaml --dry             # план и цена, бесплатно
# 1) ключевой кадр (профиль влево) + маркер (~$0.1) → смотреть out/<code>/
node tools/gen.mjs assets/mobs/<code>.yaml keyframeSide icon
# 2) анимации (~$0.9)
node tools/gen.mjs assets/mobs/<code>.yaml anim:idle anim:attack anim:hit anim:death
# 3) скиллы (~$0.25 каждый: иконка + каст)
node tools/gen.mjs assets/mobs/<code>.yaml skill:<mob_code1>
# 4) персональный фон арены (256, opaque)
node tools/gen.mjs assets/mobs/<code>.yaml arenaBackground
```

Состояние, `--force`/`--seed`/`--budget`, просмотр листов — как у класса (`class.md`, Шаг 3).

### Приёмка (проверять каждую)

| Ассет | Критерий |
|---|---|
| keyframeSide | профиль **влево**, вся фигура с ногами, стойка с `weaponRest`, палитра держится |
| маркер (icon) | один доминирующий `accentColor`, силуэт `emblem` читается на 32 px, итог 128 (64 ×2) |
| idle | дыхание едва заметное, оружие неподвижно |
| attack | явный замах → удар с проносом, не «туда-сюда» |
| hit | отдача **назад-вправо** (удар прилетает слева), короткий шат, возврат в стойку |
| death | падает; **последний кадр лежит** (без «воскресающего» отскока) |
| иконки скиллов | предмет + один цветовой акцент, читается на 32 px |
| касты скиллов | уникальная анимация по `cast`, возврат в стойку |
| фон арены | без существ и текста; нижняя треть — свободная земля под бойцов, палитра игры |

## Шаг 5. Заливка в БД

```bash
ADMIN_API_URL=http://localhost:3000 ADMIN_EMAIL=… ADMIN_PASSWORD=… \
  node tools/publish.mjs assets/mobs/<code>.yaml
```

Publish (мобья ветка): находит Monster по `name`, заливает маркер (`iconUrl`), 4 листа
(idle/attack/hit/death), `description` и фон арены (лист 1×1 — из `state.arenaBackground`
после ген-цели `arenaBackground`, или из готового файла `arenaBackground:` в манифесте).
У существующих скиллов
обновляет визуал, `name` и `description` по `code`; недостающие создаёт из `db:`-блока
(без него — предупреждение `! skill … skipped`, числа существующих правятся в админке).
Идемпотентен: повторный запуск дозальёт только изменившееся (кэш по хэшу файла).

## Шаг 6. Финализация

1. Итоговые промты из `<code>.state.json` → карточка (раздел 6, колонка «Промт»).
2. Проверка на устройстве: маркер на карте (32 px), тап → описание, бой — idle/attack/hit/death,
   имя скилла в логе и ленте намерений, фон арены (моба или зоны).
3. Коммиты: `troy-docs` (карточка), `troy-assets` (манифест + state + `out/<code>/`),
   `troy-backend` (seed, если это базовый моб).

## Грабли

Все классовые грабли действуют (`class.md`, «Грабли»: без «pixel art»/«transparent», фон
«plain white background», `Connection: close` в `rd.mjs`, полный список —
`troy-assets/styles/README.md` и `roadmap/assets/pitfalls.md`). Мобьи сверху:

- Направление держать текстом «facing to the LEFT» во всех промтах — reference-кадр сам по
  себе поворот не гарантирует.
- В hit обязательно «takes a hit from the LEFT … recoil backwards to the RIGHT» — иначе
  модель рисует удар «в камеру» и отдачу в случайную сторону.
- Для death альтернатива `custom_action` — `rd_advanced_animation__destroy` (распад);
  выбирать по твари: скелету — распад, зверю — падение.
- Не добавлять мобу классовые цели (`keyframeFront`, `anim:walk`, …) — `gen.mjs` их не знает
  для `kind: mob` и упадёт с `unknown target`.
