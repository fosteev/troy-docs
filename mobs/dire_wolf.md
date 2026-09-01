# Dire Wolf — Лютоволк

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/dire_wolf.yaml` (манифеста ещё нет — завести при генерации).

## 1. Название

| | |
|---|---|
| `code` манифеста | `dire_wolf` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Dire Wolf |
| Название RU | Лютоволк |
| `isElite` | false |

## 2. Описание

**Роль в бою:** быстрый хищник 5 уровня · плотный физический урон автоатакой · берётся бронёй и ответным давлением — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Матёрый волк ростом по пояс, серая шкура в старых шрамах. Кружит, держит дистанцию
> и бросается в горло, стоит отвести взгляд.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 5 | hp | 107 |
| strength | 18 | intelligence | 3 |
| armor | 8 | magicResist | 2 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 65 | goldReward | 28 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида, якорь lvl 5 в `content-generation.md`. Быстрой твари по кривым
допустим attackSpeed до 1.4 — см. Расхождения.

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

Скиллов нет (0 — допустимо). Кандидат при балансе: рывок в горло при низком HP игрока
(`target_hp_below`, попытка добить) — завести через карточку, seed/админку и манифест.

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/dire_wolf.yaml`;
итоговые промты после генерации — из `dire_wolf.state.json` сюда.

### Визуальный бриф

- Силуэт: крупный поджарый волк с опущенной головой и вздыбленным загривком, длинные
  лапы — низкая хищная стойка читается на 32 px.
- Цвета: стально-серая шкура со шрамами + янтарные глаза; `accentColor` — steel grey.
- Размеры: моб 96–128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A huge lean dire wolf with shaggy steel-grey fur, old pale scars across the flank, raised
hackles, bared fangs and glowing amber eyes, head held low in a hunting stance. Color scheme:
steel grey fur, amber eyes, muted dark medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a snarling wolf head with bared fangs and raised hackles |
| `accentColor` | steel grey |
| `weaponRest` | crouched low on all fours, head down, hackles raised |
| `attackMotion` | Coils back on the haunches, then lunges forward with snapping jaws |
| `hitMotion` | Flinches back, ears flat, snarling |
| `deathMotion` | Legs give way, collapses onto its side, head drops last |
| `arena` (фон арены) | A moonlit pine forest edge: pale mist between dark trunks, frost-bitten grass, gnawed bones near a shallow den |

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

- Моб есть в seed (`Dire Wolf`), `description` в seed добавлен (01.09); на dev описание
  завести через админку (seed не гонять).

### Расхождения код ↔ документы

- По кривым `content-generation.md` быстрой твари допустим attackSpeed до 1.4, в seed — 1.0.
  Кандидат на балансовую правку.
