# Wild Boar — Дикий кабан

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/wild_boar.yaml`.

## 1. Название

| | |
|---|---|
| `code` манифеста | `wild_boar` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Wild Boar |
| Название RU | Дикий кабан |
| `isElite` | false |

## 2. Описание

**Роль в бою:** таран 2 уровня · ровный физический урон автоатакой · берётся разменом — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Матёрый секач с рваным ухом и жёлтыми клыками. Роет землю копытом, срывается в разбег
> и таранит всем весом — уворачиваться надо заранее.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 2 | hp | 93 |
| strength | 11 | intelligence | 1 |
| armor | 4 | magicResist | 1 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 30 | goldReward | 12 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида, между якорями lvl 1 и lvl 3 (`content-generation.md`).

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

Скиллов нет (0 — допустимо, урон автоатакой). Кандидат при балансе контента: телеграфированный
разбег-таран (`always`, каст ~1s) — завести через карточку, seed/админку и `db:`-блок манифеста.

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/wild_boar.yaml`;
сгенерён 07.09 (seed 4401, $1.28, без перегенов; баланс RD после — $2.89), промты ниже — из
`wild_boar.state.json`. Оверрайды шаблона не понадобились: зверь падает и закрывает глаза —
канон `styles/mob.yaml` подходит как есть.

### Визуальный бриф

- Силуэт: массивная низкая туша на коротких ногах, горб щетины на загривке, загнутые
  клыки — клыки и горб читаются на 32 px.
- Цвета: тёмно-бурая щетина + грязно-жёлтые клыки; `accentColor` — dark russet.
- Размеры: моб 96–128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A massive wild boar with dark bristly fur, a ridge of stiff hair along the back, a torn ear,
curved yellowed tusks and small angry eyes, heavy low body on short legs. Color scheme:
dark russet-brown bristle, dirty yellow tusks, muted dark medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a boar head with curved tusks and a bristly mane |
| `accentColor` | dark russet |
| `weaponRest` | standing heavy on all fours, head lowered, tusks forward |
| `attackMotion` | Paws the ground, then charges headlong with an upward tusk sweep |
| `hitMotion` | Grunts and staggers a step sideways, shaking its head |
| `deathMotion` | Front legs buckle, the heavy body topples onto its side |
| `arena` (фон арены) | A churned forest clearing: uprooted black earth, broken saplings, shredded bark on old trunks, low evening light |

### Слоты (канон: в бою моб справа, смотрит ВЛЕВО; клиент не зеркалит)

| Слот БД | Style | Кадры/fps | Промт |
|---|---|---|---|
| keyframeSide (влево) | `rd_pro__fantasy` | 128 | `A massive wild boar with dark bristly fur, a ridge of stiff hair along the back, a torn ear, curved yellowed tusks and small angry eyes, heavy low body on short legs. Color scheme: dark russet-brown bristle, dirty yellow tusks, muted dark medieval fantasy. Strict side view in profile, facing to the LEFT, full body, feet visible, calm menacing stance with standing heavy on all fours, head lowered, tusks forward, small margin to the canvas edge, centered, on a plain white background.` |
| `iconUrl` (маркер) | `rd_plus__skill_icon` ×2 | 64→128 | `Map marker icon of a boar head with curved tusks and a bristly mane, one dominant dark russet color, bold readable silhouette, medieval dark fantasy, on a plain white background.` |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 | `Standing still facing left, extremely subtle and slow breathing, almost no movement, standing heavy on all fours, head lowered, tusks forward, no weapon motion` |
| `spriteAttack` | `custom_action` | 8 / 12 | `Paws the ground, then charges headlong with an upward tusk sweep, facing left, clear wind-up then a fast powerful strike with follow-through` |
| `spriteHit` | `custom_action` | 6 / 12 | `Grunts and staggers a step sideways, shaking its head, facing left, takes a hit from the left: sharp recoil backwards to the right, brief stagger, then returns to the stance` |
| `spriteDeath` | `custom_action` | 8 / 8 | `Front legs buckle, the heavy body topples onto its side, facing left, collapses and falls to the ground, the eyes close as it goes down, the last frame lies still with the eyes shut` |
| `arenaBackground` | `rd_pro__fantasy` 256 (opaque) | 1×1 | `A churned forest clearing: uprooted black earth, broken saplings, shredded bark on old trunks, low evening light. Wide battle arena background scene, open trampled ground across the lower third where fighters stand, clear uncluttered middle, scenery and horizon in the upper half, moody lighting, no creatures, no people, no text, muted dark medieval fantasy environment.` |

### Чек-лист

- [x] маркер читается на карте (32 px, один доминирующий цвет)
- [x] idle/attack/hit/death; hit — отдача вправо; death — лежит в последнем кадре, глаза закрыты
- [x] фон арены
- [ ] заведён в БД (seed есть), publish залил визуал — **проверка на устройстве**

## 7. Реализация

- Моб есть в seed (`Wild Boar`), `description` в seed добавлен (01.09); на dev описание залил
  publish из манифеста.
- Арт сгенерён и залит на dev 07.09 (`troy-assets/out/wild_boar/`, манифест
  `assets/mobs/wild_boar.yaml`, seed 4401, $1.28 — с первого прогона, перегенов не было).
  Скиллов нет, генерить было нечего.

### Расхождения код ↔ документы

- Нет.
