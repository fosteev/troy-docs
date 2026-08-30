# Mage — Маг

> Карточка класса по [_template.md](_template.md). Раздел «Реализация» — что в БД и коде. Кап уровня — **10**, скиллов — **4**.

## 1. Название

| | |
|---|---|
| `code` | `mage` |
| Название (RU / EN) | Маг / Mage |
| Дев-двойник | нет — арт генерируется сразу под `mage` (`isActive` уже true, спрайты сейчас пустые/бандл) |

## 2. Описание

**Роль:** дальний бой · дамагер-кастер · фронтлоад (сильный старт, потом экономит).

**Лор (экран выбора, ≤ 220 символов):**
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
| 3 | 6 | `arcane_shield` | Arcane Shield / Чародейский щит | 0s | 18s | 25 | 0 | INT × 0.5 (щит) | ABSORB 30 + INT×0.5, 10s | план |
| 4 | 10 | `meteor` | Meteor / Метеор | 2.5s | 15s | 40 | 80 | INT × 1.8 | NONE | план |

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
- `icon`: `a blazing orange fireball with a trailing tail of embers, flying to the right`
- `cast`: `Fireball — sweeps the staff forward with both hands, the crystal flares and a blazing orange fireball with a trail of embers shoots forward from its tip`
- ⬜ не сгенерировано

**Frost Bolt** — «Ледяной осколок. Замедляет цель на 30 % на 3 с.»
- `icon`: `a jagged pale-blue ice shard with frost crystals and a cold white mist trail`
- `cast`: `Frost Bolt — raises the staff, the crystal turns icy blue, a jagged ice shard with a cold mist trail launches forward, frost flakes scatter`
- ⬜ не сгенерировано

**Arcane Shield** — «Купол из рун. Поглощает урон, пока не лопнет.»
- `icon`: `a translucent violet hexagonal arcane barrier with glowing cyan runes along its edge`
- `cast`: `Arcane Shield — slams the staff butt into the ground, a translucent violet dome of glowing cyan runes rises around the body and settles as a shimmering barrier`
- ⬜ не сгенерировано

**Meteor** — «Долгий каст — и с неба падает камень в огне.»
- `icon`: `a burning meteor rock with a long orange fire tail falling diagonally, cracks glowing red`
- `cast`: `Meteor — lifts the staff high overhead with both hands while chanting, the crystal blazes, then a burning rock crashes down from above in front of the mage with a fiery explosion and smoke`
- ⬜ не сгенерировано

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

Промты собираются шаблоном `styles/class.yaml`; после генерации сюда копируются итоговые строки из `mage.state.json`.

| Слот | Style | Размер / кадры | Промт |
|---|---|---|---|
| `keyframeFront` | `rd_pro__fantasy` | 128 | → из state |
| `keyframeSide` | `rd_pro__edit` (input = front) | 128 | → из state |
| `keyframeTop` | `rd_pro__edit` (input = front) | 64 | → из state |
| `icon` → `iconUrl` | `rd_plus__skill_icon` ×4 | 512 | → из state |
| `portrait` | `portrait:rd_flux` | 128 | → из state |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 fps | → из state (шаблон: едва заметное дыхание, кристалл может мягко пульсировать) |
| `spriteWalk` | `rd_advanced_animation__walking` (от top) | 8 / 10 fps | → из state |
| `spriteAttackIdle` | `custom_action` (от side) | 8 / 5 fps | → из state |
| `spriteAttack` | `custom_action` (от side) | 8 / 12 fps | → из state |
| `ClassSkill.spriteAttack` ×4 | `custom_action` (от side) | 8 / 12 fps | раздел 5 |

Особенности мага против воина: «замах → удар» для кастера = «жест/подъём посоха → выброс снаряда»; в attackIdle посох стоит, свечение статично; при ходьбе сверху ног не видно — движение читается по покачиванию посоха и капюшона.

### Чек-лист готовности арта

- [ ] keyframeFront, keyframeSide, keyframeTop
- [ ] icon 512, portrait
- [ ] spriteIdle, spriteWalk, spriteAttackIdle, spriteAttack
- [ ] fireball, frost_bolt, arcane_shield, meteor (icon + cast)
- [ ] проверка на устройстве: карта, бой, выбор персонажа
- [ ] залито `publish.mjs` под `code: mage`

Ориентировочная стоимость полного набора — ≈ $2.3 (как у воина + 2 скилла).

## 8. Реализация

| Что | Где |
|---|---|
| Класс | `CharacterClass` `mage` — seed `troy-backend/prisma/seed.ts`, админка |
| Скиллы | `ClassSkill`: `fireball`, `frost_bolt` в seed; `arcane_shield`, `meteor` — завести |
| Формулы маны | `game-core/battle`, ключ `resourceType MANA`; дизайн `stats-and-formulas.md` |
| Арт-манифест | `troy-assets/assets/classes/mage.yaml` (создан из этой карточки), state рядом после генерации |

### Расхождения код ↔ документы (решить)

1. `frost_bolt.unlockLevel` в seed = **2**, по сетке слотов должно быть **3** — поправить seed.
2. `classes.md` раньше: Fireball 15 маны / 35 base, CD 4; Frost **Nova** 20 маны без каста. В БД: Fireball 25 / 30 / CD 3, Frost **Bolt** 30 / 18 / каст 1с / slow 30 % — карточка и `classes.md` приведены к БД.
3. Авто-рост мага в сумме **5.8**, норматив `content-generation.md` — 6.5. Либо поднять AGI +0.8 → +1.5 (скорость атаки/крит), либо признать норматив мягким. Предложение: AGI +1.5.
4. ABSORB: как движок считает размер щита (effectValue vs baseDamage+scaling) — проверить в `battle` до заведения `arcane_shield`; в карточке принято `effectValue + INT×scalingRatio`.
