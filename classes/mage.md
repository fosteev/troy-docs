# Mage — Маг

> Карточка класса по [_template.md](_template.md). Раздел «Реализация» — что в БД и коде. Кап уровня — **10**, скиллов — **4**.

## 1. Название

| | |
|---|---|
| `code` | `mage` |
| Название (RU / EN) | Маг / Mage |
| Дев-двойник | нет — арт залит прямо в `mage` (dev MinIO), 30.08 |

## 2. Описание

**Роль:** дальний бой · дамагер-кастер · фронтлоад (сильный старт, потом экономит).

**Описание класса — `CharacterClass.description` (в игре, экран выбора; RU, локализация — последний этап roadmap):**
> Ушёл из башни, не дописав диссертацию: решил, что руны лучше проверять на живых. Начинает бой с полным запасом маны и не стесняется тратить её сразу — главное, чтобы противник кончился раньше.

**Короткое (карточка, ≤ 60 символов):** «Огонь и лёд. Бьёт первым — и очень больно».

**Тэги стиля игры:** кастер · дальний · бурст · требует расчёта.

**Сильные стороны:** самый высокий урон за каст; полная мана с первой секунды; контроль (slow) и щит в ките; высокий Magic Resist.
**Слабые стороны:** мало HP и брони — мили-мобы и физический урон бьют больно; медленные касты (1–2.5с) срываются от stun; без маны остаётся слабая автоатака.

## 3. Основной ресурс — Mana (Мана)

| | |
|---|---|
| `resourceType` | `MANA` |
| Диапазон | 0 – `baseMana + INT×8` (64 на 1 ур., 244 на 10 ур.) |
| Старт боя | полный |
| Вне боя | не существует (каждый бой с полной) |
| UI | синяя полоса под HP |

```
max_mana   = 0 + INT * 8
mana_regen = max_mana * 0.01 * (1 + SPI * 0.02) в секунду   // 0.70/с на 1 ур., 3.12/с на 10 ур.
mana = clamp(mana, 0, max_mana)
```

Spirit — множитель регена. INT растёт и максимум, и реген одновременно, поэтому Spirit для мага — вторичный стат.

## 4. Характеристики

### Стартовые (уровень 1) и авто-рост

| Атрибут | Старт | За уровень | На 10 ур. |
|---|---|---|---|
| Strength | 2 | +0.5 | 6.5 |
| Intelligence | 8 | +2.5 | 30.5 |
| Stamina | 3 | +1.0 | 12 |
| Agility | 4 | +0.8 | 11.2 |
| Spirit | 5 | +1.0 | 14 |

Старт: сумма 22, рост: сумма 5.8 — **ниже норматива 6.5** (см. расхождения). Плюс 2 свободных очка/уровень (18 за 2→10).

Константы (`CharacterClass`): `baseHp 17`, `baseMana 0`, `baseAttackSpeed 0.5`.

### Производные

```
HP = 17 + STA*10 + STR*2      Armor = STA*2      MR = INT*1.5
Attack Speed = 0.5 * (1 + AGI*0.01)      Crit = AGI*0.15 %
Автоатака = base_spell_dmg + INT*0.5 (MAGICAL) — магическая стрела
```

### Таблица 1–10 (авто-рост, без свободных очков и экипировки)

| Ур. | STR | INT | STA | AGI | SPI | HP | Armor | MR | Atk speed (интервал) | Crit | Mana / regen |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2 | 8 | 3 | 4 | 5 | 51 | 6 | 12 | 0.520 (1.92с) | 0.60% | 64 / 0.70/с |
| 2 | 2.5 | 10.5 | 4 | 4.8 | 6 | 62 | 8 | 15.75 | 0.524 (1.91с) | 0.72% | 84 / 0.94/с |
| 3 | 3 | 13 | 5 | 5.6 | 7 | 73 | 10 | 19.5 | 0.528 (1.89с) | 0.84% | 104 / 1.19/с |
| 4 | 3.5 | 15.5 | 6 | 6.4 | 8 | 84 | 12 | 23.25 | 0.532 (1.88с) | 0.96% | 124 / 1.44/с |
| 5 | 4 | 18 | 7 | 7.2 | 9 | 95 | 14 | 27 | 0.536 (1.87с) | 1.08% | 144 / 1.70/с |
| 6 | 4.5 | 20.5 | 8 | 8 | 10 | 106 | 16 | 30.75 | 0.540 (1.85с) | 1.20% | 164 / 1.97/с |
| 7 | 5 | 23 | 9 | 8.8 | 11 | 117 | 18 | 34.5 | 0.544 (1.84с) | 1.32% | 184 / 2.24/с |
| 8 | 5.5 | 25.5 | 10 | 9.6 | 12 | 128 | 20 | 38.25 | 0.548 (1.82с) | 1.44% | 204 / 2.53/с |
| 9 | 6 | 28 | 11 | 10.4 | 13 | 139 | 22 | 42 | 0.552 (1.81с) | 1.56% | 224 / 2.82/с |
| 10 | 6.5 | 30.5 | 12 | 11.2 | 14 | 150 | 24 | 45.75 | 0.556 (1.80с) | 1.68% | 244 / 3.12/с |

### Билды (18 свободных очков)

| Билд | Куда очки | Что даёт на 10 ур. |
|---|---|---|
| Glass Cannon | INT | +144 маны, +27 MR, Meteor +32 урона |
| Battle Mage | STA | +180 HP, +36 Armor — переживает мили-мобов |
| Speed | AGI | +18% скорость атаки, +2.7% крит (касты быстрее не становятся — см. combat.md) |
| Sustain | SPI | реген 3.12 → 4.00/с на 10 ур. — в долгих боях +1 Fireball |

### Экипировка

Посох (двуручный, определяет визуал автоатаки — стрела из кристалла), мантия/ткань (MR > armor). Щиты и тяжёлая броня — недоступны.

## 5. Скиллы

Слоты **1 / 3 / 6 / 10**. Все — `resourceType MANA`, `damageType MAGICAL`, скейл от `INT`. Урон = `baseDamage + INT * scalingRatio` (далее MR цели, крит). Касты срываются от STUN.

| Слот | Ур. | code | Название EN / RU | Cast | CD | Mana | Base | Scaling | Эффект | Статус |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | `fireball` | Fireball / Огненный шар | 1.5s | 3s | 25 | 30 | INT × 1.2 | NONE | в БД |
| 2 | 3 | `frost_bolt` | Frost Bolt / Ледяная стрела | 1s | 5s | 30 | 18 | INT × 0.8 | SLOW 30 %, 3s | в БД (unlock 2 → 3) |
| 3 | 6 | `arcane_shield` | Arcane Shield / Чародейский щит | 0s | 18s | 25 | 0 | INT × 0.5 (щит) | ABSORB 30 + INT×0.5, 10s | seed + манифест `db:` |
| 4 | 10 | `meteor` | Meteor / Метеор | 2.5s | 15s | 40 | 80 | INT × 1.8 | NONE | seed + манифест `db:` |

Экономика маны: 1 ур. — 64 маны = Fireball ×2 и всё, дальше автоатака и 0.7/с. 10 ур. — 244 маны, реген 3.12/с: открытие Meteor (40) + Frost Bolt (30) + Fireball ×5 за первые ~15с, потом Fireball раз в ~8с на регене. Класс обязан «выиграть первые 20 секунд».

Поля `ClassSkill` для новых скиллов:

```yaml
arcane_shield: { slot: 3, unlockLevel: 6,  castTimeSec: 0,   cooldownSec: 18, resourceType: MANA, resourceCost: 25,
                 damageType: null, baseDamage: 0, scalingStat: INT, scalingRatio: 0.5,
                 effectType: ABSORB, effectValue: 30, effectDurationSec: 10 }   # щит = effectValue + INT*scalingRatio
meteor:        { slot: 4, unlockLevel: 10, castTimeSec: 2.5, cooldownSec: 15, resourceType: MANA, resourceCost: 40,
                 damageType: MAGICAL, baseDamage: 80, scalingStat: INT, scalingRatio: 1.8,
                 effectType: NONE, effectValue: 0, effectDurationSec: 0 }
```

### Описания и промты

Поля `icon` / `cast` — в `troy-assets/styles/class.yaml` → `skill.icon` / `skill.anim` (ракурс «facing right», фон и стиль добавляет шаблон).

**Fireball** — «Сгусток огня с кристалла посоха. Хлеб мага.»
- `description` (в игре, RU): Сгусток огня с кристалла посоха. Хлеб мага: дешёвый и стабильный магический урон.
- `icon`: `a blazing orange fireball with a trailing tail of embers, flying to the right`
- `cast`: `Fireball — sweeps the staff forward with both hands, the crystal flares and a blazing orange fireball with a trail of embers shoots forward from its tip`
- ✅ сгенерировано (state `skill:*`)

**Frost Bolt** — «Ледяной осколок. Замедляет цель на 30 % на 3 с.»
- `description` (в игре, RU): Ледяной осколок замедляет цель: на 3 с её скорость атаки падает на 30 %.
- `icon`: `a jagged pale-blue ice shard with frost crystals and a cold white mist trail`
- `cast`: `Frost Bolt — raises the staff, the crystal turns icy blue, a jagged ice shard with a cold mist trail launches forward, frost flakes scatter`
- ✅ сгенерировано (state `skill:*`)

**Arcane Shield** — «Купол из рун. Поглощает урон, пока не лопнет.»
- `description` (в игре, RU): Купол из рун поглощает урон, пока не лопнет. Прочность щита растёт от интеллекта.
- `icon`: `a translucent violet hexagonal arcane barrier with glowing cyan runes along its edge`
- `cast`: `Arcane Shield — slams the staff butt into the ground, a translucent violet dome of glowing cyan runes rises around the body and settles as a shimmering barrier`
- ✅ сгенерировано (state `skill:*`)

**Meteor** — «Долгий каст — и с неба падает камень в огне.»
- `description` (в игре, RU): Долгий каст — и с неба падает горящий камень. Самый мощный удар мага; оглушение срывает каст.
- `icon`: `a burning meteor rock with a long orange fire tail falling diagonally, cracks glowing red`
- `cast`: `Meteor — lifts the staff high overhead with both hands while chanting, the crystal blazes, then a burning rock crashes down from above in front of the mage with a fiery explosion and smoke`
- ✅ сгенерировано (state `skill:*`)

## 6. Максимальный уровень

**10.** XP `80 * level^1.5` — таблица в `leveling.md`. На 10 ур.: 4 скилла, 18 очков, кап. Резерв на поднятие капа: Lightning Bolt (5), Combustion (6).

## 7. Арт: промты на каждую картинку

### Визуальный бриф

- Силуэт: высокий и худой, длинная мантия до земли (ног не видно — при ходьбе сверху читается по посоху и капюшону), посох выше роста с **светящимся голубым кристаллом** — опознавательный знак класса на любом ракурсе и в 32 px, капюшон наброшен.
- Цвета: тёмно-синий `#1f2a5a`, тёмно-фиолетовый `#3b2354`, свечение циан `#5fd7ff`; золото `#d4a827` — только кант мантии и оковка посоха. Палитра общая `palette/troy-dark-gold.png` — **проверить, что в ней хватает синих/циановых** (собрана под воина; при нехватке — расширить палитру, а не менять цвета класса).
- Размеры: персонаж 128 (холст 144), вид сверху 64 (холст 80), иконка 128→×4 = 512, портрет 128.

### `subject`

```
A tall slender human mage, long dark navy blue robe with dark purple panels and faintly glowing cyan runes
along the hem and sleeves, worn gold trim, a tall gnarled wooden staff taller than the mage held in the right hand
with a glowing cyan crystal on top, the left hand open with a faint cyan magical glow,
a deep hood drawn over the head with glowing cyan eyes in the shadow, a gold clasp at the collar, simple leather boots.
Color scheme: deep navy blue, dark purple, cyan-blue glow, warm gold accents, muted dark medieval fantasy.
```

### Поля манифеста (`troy-assets/assets/classes/mage.yaml`)

| Поле | Значение |
|---|---|
| `emblem` | a tall wooden staff with a glowing cyan crystal crossed with an open spellbook, three cyan runes floating above |
| `portrait` | a gaunt hooded human mage, the hood drawn low, glowing cyan eyes in the shadow of the hood, sharp thin face, a gold clasp at the collar, faint cyan rune light on the cheek |
| `weaponRest` | the staff planted upright on the ground beside the body, the crystal glowing softly |
| `weaponCarry` | the tall staff in the right hand, the long robe trailing |
| `topdownDetail` | the deep hood with a glowing cyan crystal on the staff to the right, the long robe spreading around the feet |
| `attackMotion` | Thrusts the staff forward with both hands, the crystal flares and fires a bolt of cyan arcane energy forward |

### Ключевые кадры и анимации

Итоговые строки из `mage.state.json` (сгенерировано 30.08, ≈ $3.05 с двумя переделками top).

| Слот | Style | Размер / кадры | Промт |
|---|---|---|---|
| `keyframeFront` | `rd_pro__fantasy` | 128 | `A tall slender human mage, long dark navy blue robe with dark purple panels and faintly glowing cyan runes along the hem and sleeves, worn gold trim, a tall gnarled wooden staff taller than the mage held in the right hand with a glowing cyan crystal on top, the left hand open with a faint cyan magical glow, a deep hood drawn over the head with glowing cyan eyes in the shadow, a gold clasp at the collar, simple leather boots. Color scheme: deep navy blue, dark purple, cyan-blue glow, warm gold accents, muted dark medieval fantasy. Front-facing full body, feet visible, small margin to the canvas edge, centered, on a plain white background.` |
| `keyframeSide` | `rd_pro__edit (input = front)` | 128 | `Redraw this exact character rotated 90 degrees into a strict side view in profile, facing to the RIGHT, full body, feet visible, calm guard stance with the staff planted upright on the ground beside the body, the crystal glowing softly, same armor, colors and proportions, small margin to the canvas edge, centered, on a plain white background.` |
| `keyframeTop` | `rd_pro__edit (input = front)` | 64 | `Redraw this exact character seen from directly above, a steep top-down camera angle like a classic top-down city game: the top of the helmet and the shoulders dominate, the body is foreshortened, the deep hood with a glowing cyan crystal on the staff to the right, the long robe spreading around the feet, standing, facing up, same armor and colors. The whole small figure including feet fits in the middle of the canvas with wide empty white margins around it, on a plain white background.` |
| `icon` → `iconUrl` | `rd_plus__skill_icon ×4` | 512 | `Class emblem icon: a tall wooden staff with a glowing cyan crystal crossed with an open spellbook, three cyan runes floating above, warm gold accents on dark steel, medieval dark fantasy, bold readable silhouette, on a plain white background.` |
| `portrait` | `portrait:rd_flux` | 128 | `Bust portrait of a gaunt hooded human mage, the hood drawn low, glowing cyan eyes in the shadow of the hood, sharp thin face, a gold clasp at the collar, faint cyan rune light on the cheek, dark moody lighting, warm gold rim light, on a plain white background.` |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 fps | `Standing completely still, extremely subtle and slow breathing, almost no movement, the staff planted upright on the ground beside the body, the crystal glowing softly, no weapon motion` |
| `spriteWalk` | `rd_advanced_animation__walking (от top)` | 8 / 10 fps | `Walking straight ahead seen from above, legs alternating, slight shoulder sway, the tall staff in the right hand, the long robe trailing` |
| `spriteAttackIdle` | `custom_action (от side)` | 8 / 5 fps | `Stands calmly in a guard stance facing right, feet planted, weapon held still, only a faint slow breathing motion, no swinging` |
| `spriteAttack` | `custom_action (от side)` | 8 / 12 fps | `Thrusts the staff forward with both hands, the crystal flares and fires a bolt of cyan arcane energy forward, facing right, clear wind-up then a fast powerful strike with follow-through` |
| `ClassSkill.spriteAttack` ×4 | `custom_action` (от side) | 8 / 12 fps | раздел 5 |

Особенности мага против воина: «замах → удар» для кастера = «жест/подъём посоха → выброс снаряда»; в attackIdle посох стоит, свечение статично; при ходьбе сверху ног не видно — движение читается по покачиванию посоха и капюшона. Канон направления карты — **строго вверх (север)**, голова у верхнего края, один лист на все направления (см. `_template.md`); текущий лист соответствует.

### Чек-лист готовности арта

- [x] keyframeFront, keyframeSide (чистый профиль вправо), keyframeTop
- [x] icon 512, portrait
- [x] spriteIdle, spriteWalk, spriteAttackIdle, spriteAttack
- [x] fireball, frost_bolt, arcane_shield, meteor (icon + cast); `arcane_shield`/`meteor` в БД создаёт `publish.mjs` из блока `db:` манифеста
- [ ] проверка на устройстве: карта, бой, выбор персонажа
- [x] залито `publish.mjs` под `code: mage` (класс + fireball/frost_bolt)

Замечания по результату: иконка Arcane Shield вышла «коробкой», а не куполом — кандидат на перегенерацию; top через `rd_pro__edit` нестабилен (одна попытка дала рыцаря в шлеме, другая — крупный план лица) — рабочий вариант получен исходным промтом при seed 4242, промт top **не трогать без нужды**.

Фактическая стоимость — ≈ $3.05 (план $2.51 + две переделки top). Баланс RD после: $3.10.

## 8. Реализация

| Что | Где |
|---|---|
| Класс | `CharacterClass` `mage` — seed `troy-backend/prisma/seed.ts`, админка |
| Скиллы | `ClassSkill`: `fireball`, `frost_bolt` в seed; `arcane_shield`, `meteor` — завести |
| Формулы маны | `game-core/battle`, ключ `resourceType MANA`; дизайн `stats-and-formulas.md` |
| Арт-манифест | `troy-assets/assets/classes/mage.yaml` (создан из этой карточки), state рядом после генерации |

### Расхождения код ↔ документы (решить)

1. `frost_bolt.unlockLevel` в seed исправлен 2 → 3; на dev значение обновит `publish.mjs`? — нет, publish не трогает unlockLevel существующих: поправить в админке.
2. `classes.md` раньше: Fireball 15 маны / 35 base, CD 4; Frost **Nova** 20 маны без каста. В БД: Fireball 25 / 30 / CD 3, Frost **Bolt** 30 / 18 / каст 1с / slow 30 % — карточка и `classes.md` приведены к БД.
3. Авто-рост мага в сумме **5.8**, норматив `content-generation.md` — 6.5. Либо поднять AGI +0.8 → +1.5 (скорость атаки/крит), либо признать норматив мягким. Предложение: AGI +1.5.
4. ABSORB: как движок считает размер щита (effectValue vs baseDamage+scaling) — проверить в `battle` до заведения `arcane_shield`; в карточке принято `effectValue + INT×scalingRatio`.
