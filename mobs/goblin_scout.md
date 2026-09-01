# Goblin Scout — Гоблин-разведчик

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/goblin_scout.yaml` (манифеста ещё нет — завести при генерации).

## 1. Название

| | |
|---|---|
| `code` манифеста | `goblin_scout` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Goblin Scout |
| Название RU | Гоблин-разведчик |
| `isElite` | false |

## 2. Описание

**Роль в бою:** быстрый мили 3 уровня · колет часто и мелко · берётся давлением, HP немного — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Тощий гоблин в лохмотьях, глаза так и бегают. В открытый бой не рвётся: кружит рядом,
> тычет кривым ножом и целит туда, где не прикрыто.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 3 | hp | 117 |
| strength | 13 | intelligence | 2 |
| armor | 5 | magicResist | 1 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 40 | goldReward | 16 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида, якорь lvl 3 в `content-generation.md`. Юркому разбойнику по кривым
допустимы dodge 3–8 — см. Расхождения.

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

### Алгоритм боя

Каждый тик (вне каста и стана) моб идёт по скиллам по `sortOrder` и берёт **первый**, у
которого готов кулдаун и выполнено `condition`; автоатака идёт своим ритмом по `attackSpeed`
и заполняет промежутки — см. `game-design/combat.md`, «Поведение моба в бою».

1. `opener` → **Backstab** — открывашка: пока игрок не втянулся, разведчик заходит со спины
   и бьёт разово и больно (каст 0.5s видно в ленте намерений). Один раз за бой.
2. `always` → **Gutting Nick** — рабочая лошадка: инстант каждые 8s, мелкий укол + кровотечение.
   Инстант не блокирует автоатаку — отсюда «колет часто и мелко».

Ресурсов у моба нет — гейт только кулдаун + условие. Фаз (`self_hp_below`) нет намеренно:
скаут дохлый (117 hp), до «фазы ярости» он в норме не доживает — сложность даёт давление
кровотечением, а не переключение режимов.

| sortOrder | code | name (EN) | condition | Cast | CD | Dmg type | Base | Scaling | Эффект |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `mob_backstab` | Backstab | `opener` | 0.5s | 12s | PHYSICAL | 12 | STR × 0.6 | — |
| 2 | `mob_gutting_nick` | Gutting Nick | `always` | 0s (инстант) | 8s | PHYSICAL | 4 | STR × 0.25 | DOT 2.5/сек, 6s |

Бюджет урона (STR 13; игрок 3 ур.: воин ≈ 222 hp, маг ≈ 110 hp — `leveling.md`):

- Backstab ≈ 12 + 0.6×13 ≈ **20** до брони — 9% hp воина, 18% hp мага, в бюджете «≤ 35%».
- Gutting Nick ≈ 4 + 0.25×13 ≈ **7** до брони + 15 кровотечением (DOT считается от
  `effectValue` в секунду и **броню игнорирует**) ≈ 22 за 6s.
- Пик открытия (Backstab + Gutting Nick подряд) ≈ 42 по магу — под потолком комбо «≤ 50%».

**Backstab** — `description` (в игре, RU): Заходит со спины и всаживает нож под лопатку —
разовый физический удар на открытии боя, ~20 урона до брони.
- `icon`: `a crooked rusty dagger stabbing downward from behind with a dull olive motion streak`
- `cast`: `Backstab — darts forward low, drives the crooked dagger in with a quick twist and slips back`

**Gutting Nick** — `description` (в игре, RU): Быстрый порез по незащищённому месту:
~7 урона сразу и кровотечение 2.5 в секунду 6 секунд, броня его не держит.
- `icon`: `a crooked rusty dagger with a dripping red blood streak along the blade`
- `cast`: `Gutting Nick — a fast low slash across the belly with the crooked dagger, thin red arc trailing the blade`

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/goblin_scout.yaml`;
итоговые промты после генерации — из `goblin_scout.state.json` сюда.

### Визуальный бриф

- Силуэт: тощий сгорбленный гоблин в капюшоне из мешковины, кривой нож остриём вниз,
  острые уши торчат из-под капюшона — капюшон + уши читаются на 32 px.
- Цвета: тускло-оливковая кожа + серо-бурые лохмотья; `accentColor` — dull olive.
- Размеры: моб 96–128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A skinny hunched goblin scout with dull olive skin, pointed ears poking through a ragged
burlap hood, shifty yellow eyes, a crooked rusty dagger held low, tattered rags and a small
loot pouch on the belt. Color scheme: dull olive skin, grey-brown rags, muted dark medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a hooded goblin head with pointed ears and a crooked dagger |
| `accentColor` | dull olive |
| `weaponRest` | the crooked dagger held low in a reverse grip, knees bent |
| `attackMotion` | Circles half a step, then a quick low stabbing lunge with the dagger |
| `hitMotion` | Yelps and hops back, clutching the shoulder |
| `deathMotion` | Crumples to the knees, drops the dagger, falls flat |
| `arena` (фон арены) | An ambush spot on a narrow forest trail: dense bushes, a crooked wooden watch-post with a rag flag, scattered stolen sacks |

### Слоты (канон: в бою моб справа, смотрит ВЛЕВО; клиент не зеркалит)

| Слот БД | Style | Кадры/fps | Промт |
|---|---|---|---|
| keyframeSide (влево) | `rd_pro__fantasy` | 128 | ✓ state (ниже) |
| `iconUrl` (маркер) | `rd_plus__skill_icon` ×2 | 64→128 | ✓ state (ниже) |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 | ✓ state (ниже) |
| `spriteAttack` | `custom_action` | 8 / 12 | ✓ state (ниже) |
| `spriteHit` | `custom_action` | 6 / 12 | ✓ state (ниже) |
| `spriteDeath` | `custom_action` | 8 / 8 | ✓ state (ниже) |
| `MonsterSkill.spriteAttack` | `custom_action` | 8 / 12 | раздел 5 |
| `arenaBackground` | `rd_pro__fantasy` 256 (opaque) | 1×1 | ✓ state (ниже) |

### Итоговые промты (из state, генерация 01.09, $2.15; seed 1337, маркер — 8123, Gutting Nick — 5150)

```
keyframeSide:  A skinny hunched goblin scout with dull olive skin, pointed ears poking through a ragged burlap hood, shifty yellow eyes, a crooked rusty dagger held low, tattered rags and a small loot pouch on the belt. Color scheme: dull olive skin, grey-brown rags, muted dark medieval fantasy. Strict side view in profile, facing to the LEFT, full body, feet visible, calm menacing stance with the crooked dagger held low in a reverse grip, knees bent, small margin to the canvas edge, centered, on a plain white background.
icon:          Map marker icon of a hooded goblin head with pointed ears and a crooked dagger, one dominant dull olive color, bold readable silhouette, medieval dark fantasy, on a plain white background.
anim:idle:     Standing still facing left, extremely subtle and slow breathing, almost no movement, the crooked dagger held low in a reverse grip, knees bent, no weapon motion
anim:attack:   Circles half a step, then a quick low stabbing lunge with the dagger, facing left, clear wind-up then a fast powerful strike with follow-through
anim:hit:      Yelps and hops back, clutching the shoulder, facing left, takes a hit from the left: sharp recoil backwards to the right, brief stagger, then returns to the stance
anim:death:    Crumples to the knees, drops the dagger, falls flat, facing left, collapses and falls to the ground, the last frame lies still
backstab icon: Skill icon: a crooked rusty dagger stabbing downward from behind with a dull olive motion streak, vivid readable silhouette, warm gold frame accents, medieval dark fantasy, on a plain white background.
backstab cast: Backstab — darts forward low, drives the crooked dagger in with a quick twist and slips back, facing left, clear wind-up then the action with follow-through
nick icon:     Skill icon: a crooked rusty dagger with a dripping red blood streak along the blade, vivid readable silhouette, warm gold frame accents, medieval dark fantasy, on a plain white background.
nick cast:     Gutting Nick — a short quick low slash with the crooked dagger, tight compact motion close to the body, a few small dark red blood droplets at the blade tip, facing left, clear wind-up then the action with follow-through
arenaBackground: An ambush spot on a narrow forest trail: dense bushes crowding the path, a crooked wooden watch-post with a ragged flag, scattered stolen sacks on the ground, dark forest behind. Wide battle arena background scene, open trampled ground across the lower third where fighters stand, clear uncluttered middle, scenery and horizon in the upper half, moody lighting, no creatures, no people, no text, muted dark medieval fantasy environment.
```

Маркер с seed 1337 вышел чёрно-серым (капюшон съедал `accentColor`) — перегенерён с 8123.
Каст Gutting Nick сначала («thin red arc trailing the blade») дал огромное розовое кольцо
вокруг моба — формулировку сузили до компактного движения с каплями, seed 5150.

### Чек-лист

- [x] маркер читается на карте (32 px, один доминирующий цвет)
- [x] idle/attack/hit/death; hit — отдача вправо (центр масс 75.9 → 80.4 → 73.6); death — лежит в последнем кадре
- [x] фон арены
- [x] иконки и касты скиллов (Backstab, Gutting Nick)
- [x] заведён в БД (seed есть), publish залил визуал и создал оба скилла — проверка на устройстве за тобой

## 7. Реализация

- Моб есть в seed (`Goblin Scout`), `description` в seed добавлен (01.09); на dev описание
  завести через админку (seed не гонять).
- Арт сгенерирован и залит (01.09): манифест `troy-assets/assets/mobs/goblin_scout.yaml`,
  `publish.mjs` обновил на dev `iconUrl`, `spriteIdle/Attack/Hit/Death`, `arenaBackground`
  и `description` (Monster `4524927f`).
- Скиллы `mob_backstab` / `mob_gutting_nick` созданы publish'ем из `db:`-блоков манифеста
  (01.09) и продублированы в `troy-backend/prisma/seed.ts` — свежая БД воспроизводит их сама.

### Расхождения код ↔ документы

- По кривым `content-generation.md` юркому разбойнику допустимы dodge 3–8, в seed — 0.
  Кандидат на балансовую правку.
