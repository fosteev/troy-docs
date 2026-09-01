# Orc Raider — Орк-налётчик

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/orc_raider.yaml` (манифеста ещё нет — завести при генерации).

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
| level | 6 | hp | 130 |
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
итоговые промты после генерации — из `orc_raider.state.json` сюда.

### Визуальный бриф

- Силуэт: широкие плечи, сгорбленная бычья посадка головы, зазубренный тесак на плече,
  нижние клыки — клыки и тесак читаются на 32 px.
- Цвета: оливково-серая кожа + разномастный тёмный металл, кроваво-красная боевая
  раскраска; `accentColor` — dark blood red.
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
| `accentColor` | dark blood red |
| `weaponRest` | the jagged cleaver resting across the shoulders, one hand on the hilt |
| `attackMotion` | Hefts the cleaver off the shoulders, then a broad sweeping sideways slash |
| `hitMotion` | Grunts, guards with the forearm, takes half a step back |
| `deathMotion` | Drops to one knee, leans on the cleaver, then falls face-first |
| `arena` (фон арены) | A looted caravan wreck on a dirt road: an overturned cart, scattered broken crates, thin smoke rising, dusty plains behind |

### Слоты (канон: в бою моб справа, смотрит ВЛЕВО; клиент не зеркалит)

| Слот БД | Style | Кадры/fps | Промт |
|---|---|---|---|
| keyframeSide (влево) | `rd_pro__fantasy` | 128 | → из state |
| `iconUrl` (маркер) | `rd_plus__skill_icon` ×2 | 64→128 | → из state |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 | → из state |
| `spriteAttack` | `custom_action` | 8 / 12 | → из state |
| `spriteHit` | `custom_action` | 6 / 12 | → из state |
| `spriteDeath` | `custom_action` | 8 / 8 | → из state |
| `arenaBackground` | `rd_pro__fantasy` 256 (opaque) | 1×1 | → из state (`arena` в манифесте) |

### Чек-лист

- [ ] маркер читается на карте (32 px, один доминирующий цвет)
- [ ] idle/attack/hit/death; hit — отдача вправо; death — лежит в последнем кадре
- [ ] фон арены
- [ ] заведён в БД (seed есть), publish залил визуал, проверка на устройстве

## 7. Реализация

- Моб есть в seed (`Orc Raider`), `description` в seed добавлен (01.09); на dev описание
  завести через админку (seed не гонять).

### Расхождения код ↔ документы

- Нет.
