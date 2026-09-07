# Stone Golem — Каменный голем

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/stone_golem.yaml`.

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
сгенерён 07.09 (seed 8812 у кадра, $1.85 с перегенами; баланс RD после — $22.45), промты
ниже — из `stone_golem.state.json`. `keyframeSide` и `death` идут через `overrides` —
разбор в Реализации.

### Визуальный бриф

- Силуэт: приземистая глыбистая фигура, огромные кулаки до земли, маленькая «голова»
  в плечах, трещины со свечением — массивные кулаки читаются на 32 px.
- Цвета: холодный сине-серый камень + мох, тусклое свечение в трещинах;
  `accentColor` — pale blue-grey.
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
| `accentColor` | pale blue-grey (осветлён против «cold blue-grey»: тёмная иконка тонет в рамке) |
| `weaponRest` | standing like a monolith, huge fists hanging heavy at the sides |
| `attackMotion` | Slowly raises both fists overhead, then a crushing downward smash |
| `hitMotion` | Barely shifts, stone chips fly off the shoulder |
| `deathMotion` | The glow in the cracks dies out, the blocks crumble apart into a pile of rubble |
| `arena` (фон арены) | Ancient ruined masonry hall open to the sky: toppled columns, cracked flagstone floor, moss and pale glowing runes on the stones |

### Слоты (канон: в бою моб справа, смотрит ВЛЕВО; клиент не зеркалит)

| Слот БД | Style | Кадры/fps | Промт |
|---|---|---|---|
| keyframeSide (влево) | `rd_pro__fantasy` (override) | 128 | `A hulking stone golem assembled from cracked grey masonry blocks, huge heavy fists hanging to the ground, a small head sunk between massive shoulders, patches of moss and faint pale glow in the cracks. Color scheme: cold blue-grey stone, green moss, pale glow, muted dark medieval fantasy. Strict side view in profile, facing to the LEFT, full body shot from head to feet, the whole figure fits inside the canvas with clear empty margin above the head and below the feet, zoomed out, no cropping, not a portrait, calm menacing stance with standing like a monolith, huge fists hanging heavy at the sides, centered, on a plain white background.` |
| `iconUrl` (маркер) | `rd_plus__skill_icon` ×2 | 64→128 | `Map marker icon of a massive cracked stone fist, one dominant pale blue-grey color, bold readable silhouette, medieval dark fantasy, on a plain white background.` |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 | `Standing still facing left, extremely subtle and slow breathing, almost no movement, standing like a monolith, huge fists hanging heavy at the sides, no weapon motion` |
| `spriteAttack` | `custom_action` | 8 / 12 | `Slowly raises both fists overhead, then a crushing downward smash, facing left, clear wind-up then a fast powerful strike with follow-through` |
| `spriteHit` | `custom_action` | 6 / 12 | `Barely shifts, stone chips fly off the shoulder, facing left, takes a hit from the left: sharp recoil backwards to the right, brief stagger, then returns to the stance` |
| `spriteDeath` | `custom_action` (override; **не** `__destroy`) | 8 / 8 | `The glow in the cracks dies out, the blocks crumble apart into a pile of rubble, facing left, frame by frame: the pale glow in the cracks fades out, the golem topples over sideways to the ground and breaks apart on impact, the masonry blocks scatter loose across the ground, the last frame is a flat wide heap of separate broken blocks lying on the ground, no standing figure, no legs, no head, only rubble` |
| `arenaBackground` | `rd_pro__fantasy` 256 (opaque) | 1×1 | `An ancient ruined masonry hall open to the sky: toppled columns, cracked flagstone floor, moss and pale glowing runes on the stones. Wide battle arena background scene, open trampled ground across the lower third where fighters stand, clear uncluttered middle, scenery and horizon in the upper half, moody lighting, no creatures, no people, no text, muted dark medieval fantasy environment.` |

### Чек-лист

- [x] маркер читается (каменный кулак в портрете; на карте рисуется `spriteIdle`)
- [x] idle/attack/hit/death; hit — крошка от плеча; death — в последнем кадре груда обломков
- [x] фон арены
- [ ] заведён в БД (seed есть), publish залил визуал — **проверка на устройстве**

## 7. Реализация

- Моб есть в seed (`Stone Golem`), `description` в seed добавлен (01.09); на dev описание залил
  publish из манифеста.
- Арт сгенерён и залит на dev 07.09 (`troy-assets/out/stone_golem/`, манифест
  `assets/mobs/stone_golem.yaml`, $1.85). Скиллов нет.

**Что чинили:**

1. **Кадр обрезало.** Массивную тушу модель распирает на весь холст: первый прогон срезал
   голову и ступни (alpha 10%). Оверрайд `keyframeSide` с `zoomed out` + `clear empty margin
   above the head and below the feet` — фигура влезла целиком.
2. **`__destroy` не годится для смерти — подтверждено дважды.** Карточка просила его как
   «распад на обломки», но он, как и на слизне, проел дыру в торсе и оставил фигуру стоять
   все 8 кадров. Дальше: `custom_action` с вертикальным оседанием дал приседающего голема
   (силуэт остался узнаваемым), и сработал только третий заход — **через завал набок**
   («topples over sideways … breaks apart on impact … only rubble»). Вывод: модель хорошо
   умеет заваливание (кабан, волк) и плохо — исчезновение силуэта, поэтому распад надо
   описывать как падение с последующим развалом.
3. Два `inference_failed` подряд на attack и hit — сбой RD, не платный; повтор тем же вызовом
   прошёл с первого раза.

### Расхождения код ↔ документы

- По кривым `content-generation.md` голему положен attackSpeed 0.6–0.7, в seed — 1.0.
  Кандидат на балансовую правку.
