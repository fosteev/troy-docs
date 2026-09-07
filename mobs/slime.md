# Slime — Слизень

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/slime.yaml`.

## 1. Название

| | |
|---|---|
| `code` манифеста | `slime` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Slime |
| Название RU | Слизень |
| `isElite` | false |

## 2. Описание

**Роль в бою:** мешок HP для 1 уровня · медленный и предсказуемый · берётся чем угодно — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Дрожащий ком едкой слизи, выползающий на тропы после дождя. Медленно перетекает к добыче
> и наваливается всем телом — просто, предсказуемо и на удивление больно.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 1 | hp | 69 |
| strength | 7 | intelligence | 1 |
| armor | 1 | magicResist | 0 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 20 | goldReward | 8 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида; якорь lvl 1 в `content-generation.md` (59–69 hp / 18–20 exp).

## 4. Дроп

| Item | weight | minQty | maxQty |
|---|---|---|---|
| Health Potion | 60 | 1 | 2 |
| Leather Armor | 20 | 1 | 1 |
| Iron Sword | 12 | 1 | 1 |
| Knight Shield | 6 | 1 | 1 |
| Swift Boots | 2 | 1 | 1 |

Общая seed-таблица всех 10 мобов; персональный дроп — контент-задача вне темы «Мобы».

## 5. Скиллы (0–2, у элиток до 2)

По дизайну — **без скиллов** (автоатаки хватает мобу 1 уровня). Фактически в seed на Слизне
висит dev-проба «brute»-алгоритма (см. Расхождения):

| sortOrder | code | name (EN) | condition | Cast | CD | Dmg type | Base | Scaling | Эффект |
|---|---|---|---|---|---|---|---|---|---|
| 0 | `mob_stun_slam` | Stun Slam | opener | 1.2s | 8s | PHYSICAL | 8 | STR × 0.4 | STUN 1.5s |
| 1 | `mob_reckless_blow` | Reckless Blow | self_hp_below:30 | 0 | 5s | PHYSICAL | 20 | STR × 0.9 | — |
| 2 | `mob_heavy_swing` | Heavy Swing | always | 0 | 6s | PHYSICAL | 12 | STR × 0.5 | — |

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/slime.yaml`;
сгенерён 07.09 (seed 3301, $1.88 с учётом перегенов; баланс RD после — $4.17), промты ниже —
из `slime.state.json`. Attack и death идут через `overrides.anims` в манифесте — общий шаблон
безглазой бесформенной массе не подходит (см. Реализация).

### Визуальный бриф

- Силуэт: бесформенный полупрозрачный ком с тёмным ядром внутри; капли стекают вниз —
  ядро и капающий контур читаются на 32 px.
- Цвета: кислотно-зелёная полупрозрачная масса + тёмное ядро; `accentColor` — acid green.
- Размеры: моб 96–128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A quivering blob of translucent acid-green slime with a darker murky nucleus inside,
dripping goo, no limbs, low and wide. Color scheme: acid green jelly, dark olive nucleus,
muted dark medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a dripping round slime blob with a dark nucleus |
| `accentColor` | acid green |
| `weaponRest` | its jelly mass slowly pulsing, drops of goo falling |
| `attackMotion` | Rears its mass up high, then slams down in a heavy sticky splash |
| `hitMotion` | Ripples violently, splatters a few drops, dents inward |
| `deathMotion` | Loses cohesion and melts down into a flat puddle |
| `arena` (фон арены) | A damp mossy forest hollow after rain: dark puddles on trampled ground, a rotten fallen log, faint green mist between old trees |

### Слоты (канон: в бою моб справа, смотрит ВЛЕВО; клиент не зеркалит)

| Слот БД | Style | Кадры/fps | Промт |
|---|---|---|---|
| keyframeSide (влево) | `rd_pro__fantasy` | 128 | `A quivering blob of translucent acid-green slime with a darker murky nucleus inside, dripping goo, no limbs, low and wide. Color scheme: acid green jelly, dark olive nucleus, muted dark medieval fantasy. Strict side view in profile, facing to the LEFT, full body, feet visible, calm menacing stance with its jelly mass slowly pulsing, drops of goo falling, small margin to the canvas edge, centered, on a plain white background.` |
| `iconUrl` (маркер) | `rd_plus__skill_icon` ×2 | 64→128 | `Map marker icon of a dripping round slime blob with a dark nucleus, one dominant acid green color, bold readable silhouette, medieval dark fantasy, on a plain white background.` |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 | `Standing still facing left, extremely subtle and slow breathing, almost no movement, its jelly mass slowly pulsing, drops of goo falling, no weapon motion` |
| `spriteAttack` | `custom_action` (override) | 8 / 12 | `Rears its mass up high, then slams down in a heavy sticky splash, facing left, frame by frame: the mass squashes down, then stretches tall upward as a wind-up, then throws itself forward to the left and slams flat and wide on the ground with goo splashing to the left, the last frames settle back into the round resting shape, no spinning, no rotation` |
| `spriteHit` | `custom_action` | 6 / 12 | `Ripples violently, splatters a few drops, dents inward, facing left, takes a hit from the left: sharp recoil backwards to the right, brief stagger, then returns to the stance` |
| `spriteDeath` | `custom_action` (override) | 8 / 8 | `Loses cohesion and melts down into a flat puddle, facing left, the jelly body sags and melts downward frame by frame, spreading wider and flatter, the last frame is a flat still puddle of goo lying on the ground with the nucleus sunk into it` |
| `arenaBackground` | `rd_pro__fantasy` 256 (opaque) | 1×1 | `A damp mossy forest hollow after rain: dark puddles on trampled ground, a rotten fallen log, faint green mist between old trees. Wide battle arena background scene, open trampled ground across the lower third where fighters stand, clear uncluttered middle, scenery and horizon in the upper half, moody lighting, no creatures, no people, no text, muted dark medieval fantasy environment.` |

### Чек-лист

- [x] маркер читается на карте (32 px, один доминирующий цвет)
- [x] idle/attack/hit/death; hit — отдача вправо; death — в последнем кадре плоская лужа
- [x] фон арены
- [ ] заведён в БД (seed есть), publish залил визуал — **проверка на устройстве**

## 7. Реализация

- Моб есть в seed (`Slime`), `description` в seed добавлен (01.09); на dev описание залил
  publish из манифеста.
- Арт сгенерён и залит на dev 07.09 (`troy-assets/out/slime/`, манифест `assets/mobs/slime.yaml`,
  seed 3301, $1.88 вместе с перегенами). Скиллы не генерились — по дизайну их нет.

**Что пришлось поправить в конвейере (общее, не только слизень):**

1. Первый прогон дал **золотого** слизня: в палитре был единственный зелёный `#2E6B30` (XP-бар),
   и кислотную массу RD снесло в золото. В `tools/palette.mjs` добавлены `acid #8FD62E`,
   `acidDark #46521F`, `moss #4C7A38` (по образцу navy/violet/cyan для мага), палитра пересобрана
   → 32 цвета. Ранее сгенерённые ассеты не затронуты.
2. `gen.mjs` не умел переопределять шаблон под конкретную тварь — добавлен блок `overrides`
   в манифесте (`overrides.stills.<цель>` / `overrides.anims.<цель>` мержатся поверх
   `styles/<kind>.yaml`).
3. `spriteDeath`: карточка просила `__destroy`, но он рассыпает искрами и оставляет ком стоять —
   вернулись к `custom_action` с покадровым описанием «оседает и растекается в плоскую лужу».
   Общий death из `styles/mob.yaml` (падает, закрывает глаза) безглазой массе тоже не подходит.
4. `spriteAttack`: без оверрайда модель крутила ком вокруг оси. Помогло покадровое описание
   (сжался → вытянулся вверх → бросок влево → возврат, `no spinning`) — приём тот же, что у death.

### Расхождения код ↔ документы

- Seed-скиллы раздела 5 — dev-проба «brute»-алгоритма (`monsters[0]` в seed), лору слизня
  не соответствуют и нарушают лимит 0–2 (три штуки). Решить при балансе контента: снять со
  Слизня или перенести подходящему мобу.
