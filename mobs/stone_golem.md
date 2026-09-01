# Stone Golem — Каменный голем

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/stone_golem.yaml` (манифеста ещё нет — завести при генерации).

## 1. Название

| | |
|---|---|
| `code` манифеста | `stone_golem` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Stone Golem |
| Название RU | Каменный голем |
| `isElite` | false |

## 2. Описание

**Роль в бою:** танк 8 уровня · медленный, толстая броня, редкие тяжёлые удары · берётся магией и терпением — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Глыбы старой кладки, собранные чужой волей воедино. Двигается медленно, бьёт редко —
> но каждый удар каменного кулака ломает щиты и рёбра.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 8 | hp | 284 |
| strength | 26 | intelligence | 5 |
| armor | 15 | magicResist | 6 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 110 | goldReward | 50 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида, якорь lvl 8 в `content-generation.md`. Голему по кривым положен
attackSpeed 0.6–0.7 — см. Расхождения.

## 4. Дроп

| Item | weight | minQty | maxQty |
|---|---|---|---|
| Health Potion | 60 | 1 | 3 |
| Leather Armor | 20 | 1 | 1 |
| Iron Sword | 12 | 1 | 1 |
| Knight Shield | 6 | 1 | 1 |
| Swift Boots | 2 | 1 | 1 |

Общая seed-таблица всех 10 мобов; персональный дроп — контент-задача вне темы «Мобы».

## 5. Скиллы (0–2, у элиток до 2)

Скиллов нет (0 — допустимо). Кандидат при балансе: телеграфированный удар обоими кулаками
с оглушением (`always`, длинный каст ~1.5s, STUN) — завести через карточку, seed/админку
и манифест.

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/stone_golem.yaml`;
итоговые промты после генерации — из `stone_golem.state.json` сюда.

### Визуальный бриф

- Силуэт: приземистая глыбистая фигура, огромные кулаки до земли, маленькая «голова»
  в плечах, трещины со свечением — массивные кулаки читаются на 32 px.
- Цвета: холодный сине-серый камень + мох, тусклое свечение в трещинах;
  `accentColor` — cold blue-grey.
- Размеры: моб 128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A hulking stone golem assembled from cracked grey masonry blocks, huge heavy fists hanging
to the ground, a small head sunk between massive shoulders, patches of moss and faint pale
glow in the cracks. Color scheme: cold blue-grey stone, green moss, pale glow, muted dark
medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a massive cracked stone fist |
| `accentColor` | cold blue-grey |
| `weaponRest` | standing like a monolith, huge fists hanging heavy at the sides |
| `attackMotion` | Slowly raises both fists overhead, then a crushing downward smash |
| `hitMotion` | Barely shifts, stone chips fly off the shoulder |
| `deathMotion` | The glow in the cracks dies out, the blocks crumble apart into a pile of rubble |
| `arena` (фон арены) | Ancient ruined masonry hall open to the sky: toppled columns, cracked flagstone floor, moss and pale glowing runes on the stones |

### Слоты (канон: в бою моб справа, смотрит ВЛЕВО; клиент не зеркалит)

| Слот БД | Style | Кадры/fps | Промт |
|---|---|---|---|
| keyframeSide (влево) | `rd_pro__fantasy` | 128 | → из state |
| `iconUrl` (маркер) | `rd_plus__skill_icon` ×2 | 64→128 | → из state |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 | → из state |
| `spriteAttack` | `custom_action` | 8 / 12 | → из state |
| `spriteHit` | `custom_action` | 6 / 12 | → из state |
| `spriteDeath` | `__destroy` (распад на обломки) | 8 / 8 | → из state |
| `arenaBackground` | `rd_pro__fantasy` 256 (opaque) | 1×1 | → из state (`arena` в манифесте) |

### Чек-лист

- [ ] маркер читается на карте (32 px, один доминирующий цвет)
- [ ] idle/attack/hit/death; hit — отдача вправо; death — лежит в последнем кадре
- [ ] фон арены
- [ ] заведён в БД (seed есть), publish залил визуал, проверка на устройстве

## 7. Реализация

- Моб есть в seed (`Stone Golem`), `description` в seed добавлен (01.09); на dev описание
  завести через админку (seed не гонять).

### Расхождения код ↔ документы

- По кривым `content-generation.md` голему положен attackSpeed 0.6–0.7, в seed — 1.0.
  Кандидат на балансовую правку.
