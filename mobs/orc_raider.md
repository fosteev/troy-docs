# Orc Raider — Орк-налётчик

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/orc_raider.yaml`.

## 1. Название

| | |
|---|---|
| `code` манифеста | `orc_raider` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Orc Raider |
| Название RU | Орк-налётчик |
| `isElite` | false |

## 2. Описание

**Роль в бою:** мили-дамагер 6 уровня · широкие тяжёлые удары · берётся контролем и киттингом — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Плечистый орк в разномастной трофейной броне, с зазубренным тесаком. Пришёл не воевать,
> а грабить: бьёт широко, жадно и без затей.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 6 | hp | 195 |
| strength | 22 | intelligence | 4 |
| armor | 10 | magicResist | 3 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 80 | goldReward | 35 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида, между якорями lvl 5 и lvl 8 (`content-generation.md`).

## 4. Дроп

| Item | weight | minQty | maxQty |
|---|---|---|---|
| Health Potion | 60 | 1 | 3 |
| Leather Armor | 20 | 1 | 1 |
| Iron Sword | 12 | 1 | 1 |
| Knight Shield | 6 | 1 | 1 |
| Swift Boots | 2 | 1 | 1 |

Общая seed-таблица всех 10 мобов (у мобов старше Dire Wolf зелье до 3 шт.);
персональный дроп — контент-задача вне темы «Мобы».

## 5. Скиллы (0–2, у элиток до 2)

Скиллов нет (0 — допустимо). Кандидат при балансе: «ярость грабителя» при низком своём HP
(`self_hp_below`, усиленный удар) — завести через карточку, seed/админку и манифест.

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/orc_raider.yaml`;
сгенерён 07.09 (seed 6633 у кадра / 6655 у фона, $2.10 с перегенами; баланс RD после — $24.30),
промты ниже — из `orc_raider.state.json`. Самый капризный моб из шести: три прогона на кадр
и три на фон — разбор в Реализации.

### Визуальный бриф

- Силуэт: широкие плечи, сгорбленная бычья посадка головы, зазубренный тесак на плече,
  нижние клыки — клыки и тесак читаются на 32 px.
- Цвета: оливково-серая кожа + разномастный тёмный металл, кроваво-красная боевая
  раскраска; `accentColor` — olive green (красный акцент уводил иконку в демона).
- Размеры: моб 96–128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A broad-shouldered orc raider with olive-grey skin, jutting lower tusks, dark blood-red war
paint across the face, mismatched trophy armor of dented plates and furs, a jagged heavy
cleaver. Color scheme: olive-grey skin, dark iron, blood-red paint accents, muted dark
medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | an orc head with jutting tusks and blood-red war paint |
| `accentColor` | olive green (не «dark blood red» — иконка выходила красным демоном) |
| `weaponRest` | the jagged cleaver resting across the shoulders, one hand on the hilt |
| `attackMotion` | Hefts the cleaver off the shoulders, then a broad sweeping sideways slash |
| `hitMotion` | Grunts, guards with the forearm, takes half a step back |
| `deathMotion` | Drops to one knee, leans on the cleaver, then falls face-first |
| `arena` (фон арены) | A long abandoned caravan wreck on an empty dirt road: an overturned cart, scattered broken crates, thin smoke rising, dusty plains behind (было «looted» — модель дорисовывала мародёра) |

### Слоты (канон: в бою моб справа, смотрит ВЛЕВО; клиент не зеркалит)

| Слот БД | Style | Кадры/fps | Промт |
|---|---|---|---|
| keyframeSide (влево) | `rd_pro__fantasy` (override) | 128 | `A broad-shouldered orc raider standing tall on both legs in heavy boots, mismatched trophy armor of dented plates and furs, a jagged heavy cleaver in hand, olive-grey skin, jutting lower tusks, dark blood-red war paint. Color scheme: olive-grey skin, dark iron, blood-red paint accents, muted dark medieval fantasy. Strict side view in profile, facing to the LEFT, full body shot from head to feet, both boots planted on the ground, the whole figure fits inside the canvas with empty margin above the head and below the feet, not a portrait, not a bust, no cropping, calm menacing stance with the jagged cleaver resting across the shoulders, one hand on the hilt, centered, on a plain white background.` |
| `iconUrl` (маркер) | `rd_plus__skill_icon` ×2 | 64→128 | `Map marker icon of an orc head with jutting tusks and blood-red war paint, one dominant olive green color, bold readable silhouette, medieval dark fantasy, on a plain white background.` |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 | `Standing still facing left, extremely subtle and slow breathing, almost no movement, the jagged cleaver resting across the shoulders, one hand on the hilt, no weapon motion` |
| `spriteAttack` | `custom_action` | 8 / 12 | `Hefts the cleaver off the shoulders, then a broad sweeping sideways slash, facing left, clear wind-up then a fast powerful strike with follow-through` |
| `spriteHit` | `custom_action` | 6 / 12 | `Grunts, guards with the forearm, takes half a step back, facing left, takes a hit from the left: sharp recoil backwards to the right, brief stagger, then returns to the stance` |
| `spriteDeath` | `custom_action` | 8 / 8 | `Drops to one knee, leans on the cleaver, then falls face-first, facing left, collapses and falls to the ground, the eyes close as it goes down, the last frame lies still with the eyes shut` |
| `arenaBackground` | `rd_pro__fantasy` 256 (opaque, override) | 1×1 | `A long abandoned caravan wreck on an empty dirt road: an overturned cart, scattered broken crates, thin smoke rising, dusty plains behind. Wide battle arena background scene, open trampled ground across the lower third where fighters stand, clear uncluttered middle, scenery and horizon in the upper half, moody lighting, completely deserted and empty: no creatures, no people, no humanoid figures, no silhouettes, no characters, no text, muted dark medieval fantasy environment.` |

### Чек-лист

- [x] маркер читается (портрет в карточке тапа; на карте рисуется `spriteIdle`)
- [x] idle/attack/hit/death; hit — отдача вправо; death — падает ничком, лежит в последнем кадре
- [x] фон арены — без людей (с третьего прогона)
- [ ] заведён в БД (seed есть), publish залил визуал — **проверка на устройстве**

## 7. Реализация

- Моб есть в seed (`Orc Raider`), `description` в seed добавлен (01.09); на dev описание залил
  publish из манифеста.
- Арт сгенерён и залит на dev 07.09 (`troy-assets/out/orc_raider/`, манифест
  `assets/mobs/orc_raider.yaml`, $2.10 — самый дорогой из шести). Скиллов нет.

**Три грабли, по одной на каждый переген:**

1. **Иконка → красный демон.** С `accentColor: dark blood red` шаблон иконки
   (`one dominant {accentColor} color`) давал рогатую красную морду без орочьих признаков.
   Акцент переведён на `olive green`, кроваво-красное осталось вторичной раскраской — орк
   опознаётся. `accentColor` уходит только в промт иконки, так что правка стоит $0.03.
2. **Кадр → портрет.** Исходный `subject` вёл с лица (клыки, раскраска на лице), и модель
   дважды зумила: сначала фронтальный кадр с отдельно висящим мечом, потом поясной портрет.
   Лечится в `subject` (вести с фигуры и позы, а не с лица) + оверрайд `keyframeSide` с явными
   `full body shot from head to feet`, `not a portrait, not a bust, no cropping`.
3. **Фон → человек в кадре.** Слово «looted» модель отыгрывала буквально и дважды ставила
   фигуру мародёра с мечом ровно туда, где стоят бойцы, — при том что базовый шаблон уже
   содержит «no creatures, no people». Помогло `long abandoned` + перечисление запретов
   (`no humanoid figures, no silhouettes, no characters`).

### Расхождения код ↔ документы

- Нет.
