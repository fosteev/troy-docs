# Necromancer Acolyte — Послушник некроманта

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/necromancer_acolyte.yaml`.

## 1. Название

| | |
|---|---|
| `code` манифеста | `necromancer_acolyte` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Necromancer Acolyte |
| Название RU | Послушник некроманта |
| `isElite` | false |

## 2. Описание

**Роль в бою:** кастер 9 уровня · магический урон, высокий MR · берётся физическим давлением, брони мало — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Юнец в чёрной рясе, сбежавший к некромантам за силой. Держится поодаль и швыряет сгустки
> мертвенной энергии; вблизи храбрости у него заметно меньше.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 9 | hp | 254 |
| strength | 29 | intelligence | 12 |
| armor | 12 | magicResist | 12 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 130 | goldReward | 60 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида, между якорями lvl 8 и lvl 10 (`content-generation.md`);
кастерный профиль — часть STR по кривым уходит в INT, MR ×2.

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

Скиллов нет (0 — допустимо, но кастеру просятся). Кандидаты при балансе: тёмный болт
(`always`, MAGICAL, скейл от INT) + добивание при низком HP игрока (`target_hp_below`) —
профиль «caster»-алгоритма из `game-design/combat.md`; сюда же логично переехать dev-скиллам
`mob_fire_bolt`/`mob_finisher_bolt` с Лесной крысы (см. её карточку).

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/necromancer_acolyte.yaml`;
сгенерён 07.09 (seed 9907, $1.28 — весь набор с первого прогона, перегенов и оверрайдов ноль;
баланс RD после — $21.17), промты ниже — из `necromancer_acolyte.state.json`.

### Визуальный бриф

- Силуэт: худая фигура в рясе с глубоким капюшоном, короткий кривой посох, костяные
  амулеты — капюшон + свечение у посоха читаются на 32 px.
- Цвета: чёрно-серая ряса + мертвенно-лиловое свечение, бледная кожа;
  `accentColor` — necrotic purple.
- Размеры: моб 96–128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A gaunt young necromancer acolyte in a black hooded robe with bone trinkets on cords, pale
sickly skin, dark circles under the eyes, a short gnarled staff with a faint sickly purple
glow at the tip. Color scheme: black-grey robe, necrotic purple glow, pale skin, muted dark
medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a deep hood with a pale face and a wisp of purple flame |
| `accentColor` | necrotic purple |
| `weaponRest` | the gnarled staff held in both hands, hood low, slightly hunched |
| `attackMotion` | Raises the staff, gathers a crackling purple orb, then hurls it forward |
| `hitMotion` | Recoils, clutches the robe at the chest, the glow flickers |
| `deathMotion` | Falls to the knees, the staff rolls away, the purple glow dies out |
| `arena` (фон арены) | A desecrated graveyard at night: leaning headstones, an open dug grave, guttering candles, low purple mist over the ground |

### Слоты (канон: в бою моб справа, смотрит ВЛЕВО; клиент не зеркалит)

| Слот БД | Style | Кадры/fps | Промт |
|---|---|---|---|
| keyframeSide (влево) | `rd_pro__fantasy` | 128 | `A gaunt young necromancer acolyte standing tall in a long black hooded robe, bone trinkets on cords, a short gnarled staff with a faint sickly purple glow at the tip, pale sickly skin. Color scheme: black-grey robe, necrotic purple glow, pale skin, muted dark medieval fantasy. Strict side view in profile, facing to the LEFT, full body shot from head to feet, feet visible, the whole figure fits inside the canvas with clear empty margin above the head and below the feet, zoomed out, no cropping, not a portrait, not a bust, calm menacing stance with the gnarled staff held in both hands, hood low, slightly hunched, centered, on a plain white background.` |
| `iconUrl` (маркер) | `rd_plus__skill_icon` ×2 | 64→128 | `Map marker icon of a deep hood with a pale face and a wisp of purple flame, one dominant necrotic purple color, bold readable silhouette, medieval dark fantasy, on a plain white background.` |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 | `Standing still facing left, extremely subtle and slow breathing, almost no movement, the gnarled staff held in both hands, hood low, slightly hunched, no weapon motion` |
| `spriteAttack` | `custom_action` | 8 / 12 | `Raises the staff, gathers a crackling purple orb, then hurls it forward, facing left, clear wind-up then a fast powerful strike with follow-through` |
| `spriteHit` | `custom_action` | 6 / 12 | `Recoils, clutches the robe at the chest, the glow flickers, facing left, takes a hit from the left: sharp recoil backwards to the right, brief stagger, then returns to the stance` |
| `spriteDeath` | `custom_action` | 8 / 8 | `Falls to the knees, the staff rolls away, the purple glow dies out, facing left, collapses and falls to the ground, the eyes close as it goes down, the last frame lies still with the eyes shut` |
| `arenaBackground` | `rd_pro__fantasy` 256 (opaque) | 1×1 | `A desecrated graveyard at night: leaning headstones, an open dug grave, guttering candles, low purple mist over the ground. Wide battle arena background scene, open trampled ground across the lower third where fighters stand, clear uncluttered middle, scenery and horizon in the upper half, moody lighting, no creatures, no people, no text, muted dark medieval fantasy environment.` |

### Чек-лист

- [ ] маркер читается на карте (32 px, один доминирующий цвет)
- [ ] idle/attack/hit/death; hit — отдача вправо; death — лежит в последнем кадре
- [ ] скиллы (icon + cast), фон арены
- [ ] заведён в БД (seed есть), publish залил визуал, проверка на устройстве

## 7. Реализация

- Моб есть в seed (`Necromancer Acolyte`), `description` в seed добавлен (01.09); на dev
  описание залил publish из манифеста.
- Арт сгенерён и залит на dev 07.09 (`troy-assets/out/necromancer_acolyte/`, манифест
  `assets/mobs/necromancer_acolyte.yaml`, seed 9907, $1.28). **Единственный моб серии, где
  весь набор взлетел с первого прогона** — без перегенов и без оверрайдов: к этому моменту
  кадрирующие формулировки (`full body … not a portrait … margin`, `zoomed out`) уже переехали
  из разовых оверрайдов орка и голема в общий `styles/mob.yaml`.
- Мелочь на будущее: лиловое свечение посоха в ключевом кадре вышло бледным, почти белым —
  цвет тянут иконка и орб в attack. Если понадобится усилить, это переген только `keyframeSide`
  (и следом анимаций, они от него наследуются).

### Расхождения код ↔ документы

- Dev-скиллы «caster»-алгоритма в seed висят на Лесной крысе, хотя по лору место им здесь —
  решить при балансе контента (см. `forest_rat.md`).
