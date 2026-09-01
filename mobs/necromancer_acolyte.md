# Necromancer Acolyte — Послушник некроманта

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/necromancer_acolyte.yaml` (манифеста ещё нет — завести при генерации).

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
| level | 9 | hp | 169 |
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
итоговые промты после генерации — из `necromancer_acolyte.state.json` сюда.

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
- [ ] скиллы (icon + cast), фон арены
- [ ] заведён в БД (seed есть), publish залил визуал, проверка на устройстве

## 7. Реализация

- Моб есть в seed (`Necromancer Acolyte`), `description` в seed добавлен (01.09); на dev
  описание завести через админку (seed не гонять).

### Расхождения код ↔ документы

- Dev-скиллы «caster»-алгоритма в seed висят на Лесной крысе, хотя по лору место им здесь —
  решить при балансе контента (см. `forest_rat.md`).
