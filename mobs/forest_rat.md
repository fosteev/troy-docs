# Forest Rat — Лесная крыса

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/forest_rat.yaml` (манифеста ещё нет — завести при генерации).

## 1. Название

| | |
|---|---|
| `code` манифеста | `forest_rat` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Forest Rat |
| Название RU | Лесная крыса |
| `isElite` | false |

## 2. Описание

**Роль в бою:** юркий кусака 1 уровня · мало HP, быстро суетится · берётся парой ударов — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Облезлая крыса-переросток с голым хвостом и жёлтыми резцами. Мечется под ногами, кусает
> исподтишка и отскакивает — попасть по ней труднее, чем кажется.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 1 | hp | 59 |
| strength | 8 | intelligence | 1 |
| armor | 2 | magicResist | 0 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 18 | goldReward | 7 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида; якорь lvl 1 в `content-generation.md`. По кривым юркой твари
положены dodge 3–8 и attackSpeed до 1.4 — см. Расхождения.

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

По дизайну — **без скиллов** (кусается автоатакой). Фактически в seed на крысе висит
dev-проба «caster»-алгоритма (см. Расхождения):

| sortOrder | code | name (EN) | condition | Cast | CD | Dmg type | Base | Scaling | Эффект |
|---|---|---|---|---|---|---|---|---|---|
| 0 | `mob_finisher_bolt` | Finisher Bolt | target_hp_below:35 | 1.5s | 7s | MAGICAL | 22 | INT × 0.8 | — |
| 1 | `mob_fire_bolt` | Fire Bolt | always | 0 | 5s | MAGICAL | 12 | INT × 0.5 | — |

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/forest_rat.yaml`;
итоговые промты после генерации — из `forest_rat.state.json` сюда.

### Визуальный бриф

- Силуэт: низкая горбатая тушка на четырёх лапах, длинный голый хвост дугой, торчащие
  резцы — хвост и резцы читаются на 32 px.
- Цвета: серо-бурая свалявшаяся шерсть + розовый хвост; `accentColor` — dusty brown.
- Размеры: моб 96–128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A mangy oversized forest rat on all fours with matted grey-brown fur, a long bald pink tail,
yellow buck teeth and beady eyes, hunched low. Color scheme: dusty grey-brown fur, pale pink
tail, muted dark medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a snarling rat head with long whiskers and bared yellow teeth |
| `accentColor` | dusty brown |
| `weaponRest` | crouched low on all fours, tail twitching |
| `attackMotion` | Darts forward and bites with a quick snap, then springs back |
| `hitMotion` | Squeals and jerks sideways, fur bristling |
| `deathMotion` | Staggers, rolls onto its side, the tail goes limp |
| `arena` (фон арены) | A forest floor by a gnawed burrow under tree roots: scattered refuse and small bones, dry leaves, dim undergrowth behind |

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

- Моб есть в seed (`Forest Rat`), `description` в seed добавлен (01.09); на dev описание
  завести через админку (seed не гонять).

### Расхождения код ↔ документы

- Seed-скиллы раздела 5 — dev-проба «caster»-алгоритма (`monsters[1]` в seed): магические
  болты у крысы с INT 1 — абсурд по лору. Решить при балансе: снять или перенести
  Necromancer Acolyte.
- По кривым `content-generation.md` юркой твари положены dodge 3–8 и attackSpeed до 1.4,
  в seed — дефолтные 0 / 1.0. Кандидат на балансовую правку.
