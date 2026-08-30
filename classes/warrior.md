# Warrior — Воин

> Карточка класса — единственный источник правды для баланса и генерации арта. Раздел «Реализация» — что в БД и коде.
> Кап уровня текущего этапа — **10**, скиллов у класса — **4**.

## 1. Название

| | |
|---|---|
| `code` (стабильный id для клиента) | `warrior` |
| Название (RU / EN) | Воин / Warrior |
| Дев-двойник в dev-БД | `knight` («Рыцарь») — визуальная проба конвейера, статы и скиллы скопированы с воина; после приёмки арт переезжает на `warrior`, `knight` удаляется |

## 2. Описание

**Роль:** ближний бой, высокая выживаемость, стабильный физический урон. Танк-дамагер, который *разгоняется*: чем дольше бой и чем больше урона получает, тем чаще бьёт скиллами.

**Лор (для экрана выбора персонажа, ≤ 220 символов):**
> Латник из старой гвардии. Не знает магии и не верит в неё — верит в сталь, щит и в то, что любой бой можно выстоять. Ярость копится с каждым ударом, полученным и нанесённым.

**Короткое (карточка выбора, ≤ 60 символов):** «Сталь и щит. Держит удар и бьёт в ответ всё сильнее».

**Тэги стиля игры:** танк · мили · разгон · простой в освоении.

**Сильные стороны:** много HP и брони; не зависит от ресурса на старте — автоатаки всегда работают; stun в кит-е.
**Слабые стороны:** первые секунды боя без скиллов (ярость 0); низкий Magic Resist — страдает от магов; нет дальнего боя и хила.

## 3. Основной ресурс — Rage (Ярость)

| | |
|---|---|
| `resourceType` | `RAGE` |
| Диапазон | 0–100, фиксированный, не скейлится |
| Старт боя | 0 |
| Вне боя | не существует (сбрасывается) |
| UI | оранжево-красная полоса под HP; в 0 — тусклая |

```
При автоатаке:        rage += 5 * (1 + SPI * 0.02)
При получении урона:  rage += damage_taken * 0.15 * (1 + SPI * 0.02)   // любой источник, в т.ч. DoT
rage = clamp(rage, 0, 100)
```

Spirit — единственный множитель. SPI 3 (1 ур.) → 5.30 за автоатаку; SPI 7.5 (10 ур.) → 5.75.

## 4. Характеристики

### Стартовые (уровень 1) и авто-рост

| Атрибут | Старт | За уровень | На 10 ур. (без очков и шмота) |
|---|---|---|---|
| Strength | 8 | +2.5 | 30.5 |
| Intelligence | 2 | +0.5 | 6.5 |
| Stamina | 6 | +2.0 | 24 |
| Agility | 3 | +1.0 | 12 |
| Spirit | 3 | +0.5 | 7.5 |

Сумма авто-роста — 6.5/уровень (норматив из `content-generation.md`). Плюс **2 свободных очка** за уровень: 18 за 2→10.

Константы класса (`CharacterClass`): `baseHp 22`, `baseMana 0`, `baseAttackSpeed 0.8`.

### Производные (формулы — `stats-and-formulas.md`)

```
HP           = 22 + STA*10 + STR*2
Armor        = STA*2 (+ шмот)          Magic Resist = INT*1.5 (+ шмот)
Attack Speed = 0.8 * (1 + AGI*0.01)     Crit         = AGI*0.15 %
Автоатака    = base_weapon_dmg + STR*0.8 (физ.)
```

### Таблица 1–10 (авто-рост, без свободных очков и экипировки)

| Ур. | STR | INT | STA | AGI | SPI | HP | Armor | MR | Atk speed (интервал) | Crit | Rage/auto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 8 | 2 | 6 | 3 | 3 | 98 | 12 | 3 | 0.824 (1.21с) | 0.45% | 5.30 |
| 2 | 10.5 | 2.5 | 8 | 4 | 3.5 | 123 | 16 | 3.75 | 0.832 (1.20с) | 0.60% | 5.35 |
| 3 | 13 | 3 | 10 | 5 | 4 | 148 | 20 | 4.5 | 0.840 (1.19с) | 0.75% | 5.40 |
| 4 | 15.5 | 3.5 | 12 | 6 | 4.5 | 173 | 24 | 5.25 | 0.848 (1.18с) | 0.90% | 5.45 |
| 5 | 18 | 4 | 14 | 7 | 5 | 198 | 28 | 6 | 0.856 (1.17с) | 1.05% | 5.50 |
| 6 | 20.5 | 4.5 | 16 | 8 | 5.5 | 223 | 32 | 6.75 | 0.864 (1.16с) | 1.20% | 5.55 |
| 7 | 23 | 5 | 18 | 9 | 6 | 248 | 36 | 7.5 | 0.872 (1.15с) | 1.35% | 5.60 |
| 8 | 25.5 | 5.5 | 20 | 10 | 6.5 | 273 | 40 | 8.25 | 0.880 (1.14с) | 1.50% | 5.65 |
| 9 | 28 | 6 | 22 | 11 | 7 | 298 | 44 | 9 | 0.888 (1.13с) | 1.65% | 5.70 |
| 10 | 30.5 | 6.5 | 24 | 12 | 7.5 | 323 | 48 | 9.75 | 0.896 (1.12с) | 1.80% | 5.75 |

### Билды (18 свободных очков)

| Билд | Куда очки | Что даёт на 10 ур. |
|---|---|---|
| Tank | STA | +180 HP, +36 Armor |
| DPS | STR | +36 к урону автоатаки/… ×1.2 у Heavy Strike |
| Crit | AGI | +18% attack speed, +2.7% crit |
| Berserk | SPI | rage/auto 5.75 → 7.55 — на ~30% чаще скиллы |

### Экипировка

Слоты общие (`inventory`), предпочтения: одноручный меч + щит (щит обязателен для визуала Shield Slam), тяжёлая броня (armor > MR). Двуручное оружие для воина — не планируется до поднятия капа.

## 5. Скиллы

Слоты открываются на **1 / 3 / 6 / 10**. Все — `resourceType RAGE`, `damageType PHYSICAL`, скейл от `STR`. Урон = `baseDamage + STR * scalingRatio` (далее броня цели, крит).

| Слот | Ур. | code | Название | Cast | CD | Rage | Base | Scaling | Эффект | Статус |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | `heavy_strike` | Heavy Strike / Тяжёлый удар | 0s | 4s | 25 | 20 | STR × 1.2 | NONE | в БД |
| 2 | 3 | `shield_slam` | Shield Slam / Удар щитом | 0s | 8s | 35 | 10 | STR × 0.6 | STUN 1.5s | в БД |
| 3 | 6 | `battle_cry` | Battle Cry / Боевой клич | 0s | 20s | 25 | 0 | — | BUFF +20% ATK, 8s | план |
| 4 | 10 | `whirlwind` | Whirlwind / Вихрь | 1s | 12s | 40 | 40 | STR × 1.2 | NONE | план |

Экономика ярости на 10 ур.: 5.75/автоатака при интервале 1.12с ≈ 5.1 rage/с без учёта входящего урона → Heavy Strike каждые ~5с (упирается в CD 4с), Shield Slam каждые ~8с (CD), Whirlwind — раз в ~12–15с.

Все поля `ClassSkill` для новых скиллов:

```yaml
battle_cry: { slot: 3, unlockLevel: 6,  castTimeSec: 0, cooldownSec: 20, resourceType: RAGE, resourceCost: 25,
              damageType: null, baseDamage: 0, scalingStat: null, scalingRatio: 0,
              effectType: BUFF, effectValue: 0.20, effectDurationSec: 8 }
whirlwind:  { slot: 4, unlockLevel: 10, castTimeSec: 1, cooldownSec: 12, resourceType: RAGE, resourceCost: 40,
              damageType: PHYSICAL, baseDamage: 40, scalingStat: STR, scalingRatio: 1.2,
              effectType: NONE, effectValue: 0, effectDurationSec: 0 }
```

### Описания и промты

Поля `icon` / `cast` вставляются в шаблоны `troy-assets/styles/class.yaml` → `skill.icon` / `skill.anim` (к ним автоматически добавляется «Skill icon: …, vivid readable silhouette, warm gold frame accents, medieval dark fantasy, on a plain white background» и «…, facing right, clear wind-up then the action with follow-through»). Каст-анимация — 8 кадров 12 fps от бокового ключевого кадра, холст 144. Иконка — `rd_plus__skill_icon` 64 → ×2.

**Heavy Strike** — «Обрушивает меч двумя руками. Просто, тяжело, больно.»
- `icon`: `a broad steel sword slamming down with a red-orange impact flash`
- `cast`: `Heavy Strike — lifts the sword with both hands high above the head and smashes it down with a massive impact, dust burst at the point of impact`
- ✅ сгенерировано (knight), в state: `skill:heavy_strike`

**Shield Slam** — «Таран щитом. Оглушает на 1.5 с — шанс сбить каст.»
- `icon`: `a round steel shield with a gold rim smashing forward, yellow stun stars around the rim`
- `cast`: `Shield Slam — lunges forward and rams the round shield into the enemy, a short stun shockwave ring bursts from the shield`
- ✅ сгенерировано (knight), в state: `skill:shield_slam`

**Battle Cry** — «Рёв, от которого крепче хват. +20% к атаке на 8 с.»
- `icon`: `an open shouting helmeted head in profile with three red-orange sound waves bursting from the mouth`
- `cast`: `Battle Cry — plants both feet, throws the head back and roars with the sword thrust up to the sky, a red-orange shockwave ring pulses outward from the body`
- ⬜ не сгенерировано

**Whirlwind** — «Разворот на пятке с мечом на вытянутой руке. Секунда замаха — и всё вокруг в стали.»
- `icon`: `a steel sword blade sweeping in a full circle leaving a curved silver-white motion trail`
- `cast`: `Whirlwind — spins a full 360 degrees on the spot with the sword held out at arm's length, the blade leaves a silver motion trail, shield tucked in, ends in the guard stance`
- ⬜ не сгенерировано

## 6. Максимальный уровень

**10.** XP по формуле `80 * level^1.5`:

| Уровень | XP до следующего | Суммарный XP |
|---|---|---|
| 1 → 2 | 80 | 80 |
| 2 → 3 | 226 | 306 |
| 3 → 4 | 416 | 722 |
| 4 → 5 | 640 | 1,362 |
| 5 → 6 | 894 | 2,256 |
| 6 → 7 | 1176 | 3,432 |
| 7 → 8 | 1482 | 4,914 |
| 8 → 9 | 1810 | 6,724 |
| 9 → 10 | 2160 | 8,884 |

На 10 уровне: все 4 скилла, 18 свободных очков распределено, дальше XP не начисляется (кап). Поднятие капа — отдельный этап: слоты 5–6 из резерва `content-generation.md` (Execution, Iron Wall).

## 7. Арт: промты на каждую картинку

Конвейер — `troy-assets` (Retro Diffusion), правила и грабли — `roadmap/assets/` (README + pitfalls.md), что сработало — `troy-assets/styles/README.md`. **Промты ниже — итоговые строки, которые реально ушли в API** (state `knight`), собраны из `styles/class.yaml` + манифеста. Общие правила: без слов «pixel art» и «transparent», фон «on a plain white background» + `remove_bg`, палитра `palette/troy-dark-gold.png`, seed 4242.

### Визуальный бриф

- Силуэт: широкие плечи, тяжёлые латы, круглый щит слева, одноручный меч справа, шлем с забралом и **алым плюмажем** (главный опознавательный знак класса на любом ракурсе и в 32 px).
- Цвета: тёмная сталь `#4a4f57`, алый `#8b1a1a`, тёплое золото `#d4a827` — только акценты (заклёпки, кант, эмблема щита).
- Нативный размер персонажа 128 px (холст анимаций 144), вид сверху 64 px (холст 80), иконка класса 128 → ×4 = **512 px**, портрет 128.
- Листы: 8 кадров → 4×2, кадр = холст; хранятся lossless webp в S3 под UUID.

### Описание персонажа (`subject`, подставляется во все ключевые кадры)

```
A muscular human warrior, broad shoulders, heavy dark steel plate armor with golden rivets and a worn gold trim,
one-handed sword held in the right hand, round shield with a gold emblem on the left arm,
steel helmet with a visor and a deep crimson plume, steel boots.
Color scheme: dark steel gray, deep crimson red, warm gold accents, muted dark medieval fantasy.
```

Поля манифеста (`assets/classes/warrior.yaml`):

| Поле | Значение |
|---|---|
| `emblem` | a crossed steel sword and a round shield with a gold rim and a crimson plume above |
| `portrait` | a grim human warrior in a dark steel helmet with the visor raised, crimson plume, scarred face, stern eyes, gold-trimmed gorget |
| `weaponRest` | the sword tip lowered and the shield resting at the side |
| `weaponCarry` | sword in the right hand, round shield on the left arm |
| `topdownDetail` | crimson plume on the helmet, round shield on the left, sword on the right |
| `attackMotion` | Raises the sword high overhead with the whole body, then a heavy downward slash with full weight behind it, shield braced |

### Ключевые кадры

| Слот | Где используется | Style | Размер | Промт |
|---|---|---|---|---|
| `keyframeFront` | экран персонажа, старт idle | `rd_pro__fantasy` | 128 | `{subject} Front-facing full body, feet visible, small margin to the canvas edge, centered, on a plain white background.` |
| `keyframeSide` | старт боевых анимаций | `rd_pro__edit`, input = front | 128 | `Redraw this exact character rotated 90 degrees into a strict side view in profile, facing to the RIGHT, full body, feet visible, calm guard stance with the sword tip lowered and the shield resting at the side, same armor, colors and proportions, small margin to the canvas edge, centered, on a plain white background.` |
| `keyframeTop` | старт walk (карта) | `rd_pro__edit`, input = front, 128 → 64 | 64 | `Redraw this exact character seen from directly above, a steep top-down camera angle like a classic top-down city game: the top of the helmet and the shoulders dominate, the body is foreshortened, crimson plume on the helmet, round shield on the left, sword on the right, standing, facing up, same armor and colors. The whole small figure including feet fits in the middle of the canvas with wide empty white margins around it, on a plain white background.` |
| `icon` → `iconUrl` | выбор класса, HUD боя (портрет-иконка), 512 px | `rd_plus__skill_icon` ×4 | 128→512 | `Class emblem icon: a crossed steel sword and a round shield with a gold rim and a crimson plume above, warm gold accents on dark steel, medieval dark fantasy, bold readable silhouette, on a plain white background.` |
| `portrait` | резерв: диалоги/результат боя (в БД слота пока нет) | `portrait:rd_flux` | 128 | `Bust portrait of a grim human warrior in a dark steel helmet with the visor raised, crimson plume, scarred face, stern eyes, gold-trimmed gorget, dark moody lighting, warm gold rim light, on a plain white background.` |

> `reference_images` в RD держит стиль, но **не поворачивает** — side/top только через `rd_pro__edit`. Side выходит 3/4 вправо, не строгий профиль — принято.

### Анимации (`ClassSpriteSheet`)

| Слот БД | Вид | От кадра | Style | Кадры / fps | Промт |
|---|---|---|---|---|---|
| `spriteIdle` | анфас, экран персонажа | front | `rd_advanced_animation__idle` | 8 / 5 | `Standing completely still, extremely subtle and slow breathing, almost no movement, the sword tip lowered and the shield resting at the side, no weapon motion` |
| `spriteWalk` | сверху, маркер на карте | top | `rd_advanced_animation__walking` | 8 / 10 | `Walking straight ahead seen from above, legs alternating, slight shoulder sway, sword in the right hand, round shield on the left arm` |
| `spriteAttackIdle` | профиль вправо, бой | side | `rd_advanced_animation__custom_action` | 8 / 5 | `Stands calmly in a guard stance facing right, feet planted, weapon held still, only a faint slow breathing motion, no swinging` |
| `spriteAttack` | профиль вправо, автоатака | side | `rd_advanced_animation__custom_action` | 8 / 12 | `Raises the sword high overhead with the whole body, then a heavy downward slash with full weight behind it, shield braced, facing right, clear wind-up then a fast powerful strike with follow-through` |
| `ClassSkill.spriteAttack` ×4 | профиль вправо, каст | side | `rd_advanced_animation__custom_action` | 8 / 12 | см. раздел 5 |

Требования к анимациям (из ревью 30.08): idle — дыхание едва заметное; attackIdle — стоит, оружием не машет; attack — явный замах → удар, не «меч туда-сюда»; walk — вид сверху как в GTA 2, **строго вверх (север), голова у верхнего края** — один лист на все направления, клиент поворачивает по heading (см. `_template.md`). Лист перегенерирован 30.08 вечером под канон (первый шёл «на юг»).

### Чек-лист готовности арта

- [x] keyframeFront, keyframeSide, keyframeTop (30.08 вечер: перегенерирован на север — спина, затылок; 128→64 + `fix-top.mjs`, т.к. edit синил сталь)
- [x] icon 512, portrait
- [x] spriteIdle, spriteWalk, spriteAttackIdle, spriteAttack
- [x] heavy_strike (icon + cast), shield_slam (icon + cast)
- [ ] battle_cry (icon + cast), whirlwind (icon + cast) — после заведения скиллов в БД
- [ ] проверка на устройстве: карта (маркер), бой (стойка/атака/касты), выбор персонажа (иконка 512)
- [ ] перенос с `knight` на `warrior` (`publish.mjs` по `code: warrior`), удаление `knight`

## 8. Реализация — что где лежит

| Что | Где |
|---|---|
| Класс, статы, `resourceType` | `CharacterClass` (таблица), seed `troy-backend/prisma/seed.ts`, админка → Классы |
| Скиллы | `ClassSkill` (slot/unlockLevel/…/iconUrl/spriteAttack), seed + админка |
| Спрайты класса | `CharacterClass.spriteIdle/Walk/Attack/AttackIdle`, `iconUrl` — S3 (dev: MinIO `troy-assets`) |
| Формулы боя/ресурса | `game-core/battle` — ключ `resourceType`; дизайн в `combat.md`, `stats-and-formulas.md` |
| Клиент | `GET /classes`, `GET /classes/:code/skills`; спрайты через `ClassSprites` в `troy-flutter/features/classes` |
| Арт-манифест | `troy-assets/assets/classes/knight.yaml` (→ переименовать в `warrior.yaml` при переносе), state рядом |

### Расхождения код ↔ документы (решить)

1. `classes.md` раньше описывал Heavy Strike на 3 ур. (CD 3, 15 ярости, 25 + STR×1.0) и Shield Bash на 6 ур. — **приведено к БД** (1 ур. / 3 ур., `shield_slam`).
2. В `troy-assets/assets/classes/warrior.yaml` лежит старый манифест пробы Шага 0 — источник правды теперь `knight.yaml` до переноса.
3. Слоты 3–4 (`battle_cry`, `whirlwind`) в БД отсутствуют — завести через админку/seed до генерации арта.
