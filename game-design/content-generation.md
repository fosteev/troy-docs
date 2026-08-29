# Content Generation — система генерации контента через ИИ

Единый документ для генерации **классов** и **боссов/мобов** любым ИИ (Claude, GPT,
image-генераторы). Содержит: канон (что нельзя нарушать), балансовые кривые,
готовые промт-шаблоны для данных (JSON) и для визуала (спрайты).

Принцип: **генератор выдаёт данные строго в полях реальной схемы БД** — результат
вставляется через админку (страницы Classes / Monsters) без ручного маппинга.

Связанные документы: [classes.md](classes.md), [stats-and-formulas.md](stats-and-formulas.md),
[combat.md](combat.md), [pixel-art-design.md](pixel-art-design.md),
[character-generation-prompt.md](character-generation-prompt.md) (базовые image-промты).

---

## 1. Канон — жёсткие ограничения движка

Всё, что генерируется, обязано укладываться в эти рамки. Промт-шаблоны ниже уже
включают их, но при ручной генерации сверяйся с этим списком.

### Атрибуты и формулы

- Пять атрибутов: **STR, INT, STA, AGI, SPI**. Других нет.
- Урон: `raw = baseDamage + scalingStat × scalingRatio`, затем крит (×2.0),
  затем reduction `defense / (defense + 100)`, затем dodge.
- HP персонажа: `base_hp + STA×10 + STR×2`. Mana: `base_mana + INT×8`.
- Rage: фиксированный 0–100, старт боя с 0. Mana: старт боя с полной.

### Enum'ы схемы (только эти значения)

| Поле | Значения |
|---|---|
| `resourceType` | `RAGE`, `MANA` |
| `damageType` | `PHYSICAL`, `MAGICAL` (null для утилити-скиллов) |
| `scalingStat` | **только `STR` или `INT`** — AGI/SPI-скейлинга в движке нет |
| `effectType` | `NONE`, `STUN`, `SLOW`, `DOT`, `BUFF`, `ABSORB`, `HEAL` |
| `rarity` (предметы) | `COMMON`, `UNCOMMON`, `RARE`, `EPIC`, `LEGENDARY` |
| `condition` (скиллы моба) | `always`, `opener`, `self_hp_below`, `target_hp_below` |

> ⚠️ Новый класс с механикой «урон от ловкости» сгенерировать нельзя, пока в
> `ScalingStat` не добавят AGI. Rogue при имплементации либо скейлится от STR,
> либо сначала расширяется enum + эвалюатор урона.

### Семантика эффектов (см. combat.md)

| effectType | effectValue | effectDurationSec |
|---|---|---|
| `STUN` | — (0) | длительность стана |
| `SLOW` | — (замедление фикс. −30% AS) | длительность |
| `DOT` | урон за тик (тик = 1/сек) | длительность |
| `BUFF` | % бафа (напр. 20 = +20% ATK) | длительность |
| `ABSORB` | размер щита (может скейлиться) | длительность |
| `HEAL` | объём лечения | 0 |

### Условия скиллов моба

Мобы кастуют по приоритету `sortOrder` (меньше — раньше), первый скилл с готовым
CD и выполненным условием:

| condition | conditionValue | Когда |
|---|---|---|
| `always` | null | всегда |
| `opener` | null | только первый каст в бою |
| `self_hp_below` | % (0–100) | HP моба ниже порога — фаза «ярости» |
| `target_hp_below` | % (0–100) | HP игрока ниже порога — добивание |

### Целевые поля БД

**CharacterClass**: `code` (стабильный slug, латиница), `name`, `description`,
`strength/intelligence/stamina/agility/spirit` (база 1 уровня),
`baseHp`, `baseMana`, `baseAttackSpeed`, `resourceType`, `isActive`.

**ClassSkill**: `slot` (1–6), `unlockLevel`, `code`, `name`, `castTimeSec`,
`cooldownSec`, `resourceType`, `resourceCost`, `damageType`, `baseDamage`,
`scalingStat`, `scalingRatio`, `effectType`, `effectValue`, `effectDurationSec`.

**Monster**: `name`, `level`, `hp`, `strength`, `intelligence`, `armor`,
`magicResist`, `attackSpeed`, `dodge`, `isElite`, `spawnable`, `nothingWeight`,
`expReward`, `goldReward`.

**MonsterSkill**: `code`, `castTimeSec`, `cooldownSec`, `damageType`,
`baseDamage`, `scalingStat`, `scalingRatio`, `effectType`, `effectValue`,
`effectDurationSec`, `sortOrder`, `condition`, `conditionValue`.

> Авто-рост атрибутов за уровень для новых классов сейчас захардкожен в
> механике под Warrior/Mage паттерны — при генерации класса указывай
> предлагаемый рост в описании, имплементация уточнит.

---

## 2. Балансовые кривые

### Мобы — якорные значения (из продакшн-сида)

| Lvl | HP | STR | Armor | MR | EXP | Gold | Пример |
|---|---|---|---|---|---|---|---|
| 1 | 39–46 | 7–8 | 1–2 | 0 | 18–20 | 7–8 | Slime, Forest Rat |
| 3 | 78 | 13 | 5 | 1 | 40 | 16 | Goblin Scout |
| 5 | 107 | 18 | 8 | 2 | 65 | 28 | Dire Wolf |
| 8 | 189 | 26 | 15 | 6 | 110 | 50 | Stone Golem |
| 10 | 221 | 33 | 16 | 10 | 160 | 80 | Drake Whelp |

Правила интерполяции для обычного моба уровня L:

```
hp        ≈ 21×L + 22        (танки +15%, кастеры −15%)
strength  ≈ 2.8×L + 5        (кастеры: часть переносится в intelligence)
armor     ≈ 1.6×L            (кастеры −30%, но magicResist ≈ armor кастера)
magicResist ≈ 1.0×L          (кастеры ×2)
expReward ≈ 0.5×L² + 9.5×L + 10
goldReward ≈ 0.42 × expReward
attackSpeed: 0.8–1.2 (быстрые твари до 1.4, големы 0.6–0.7)
dodge: 0 почти всем; юркие (крысы, разбойники) 3–8
```

### Босс (elite) — множители от обычного моба того же уровня

```
hp × 2.5–3.0
основной статовый стат (str или int) × 1.2–1.4
armor / magicResist × 1.3–1.5
expReward × 3–4,  goldReward × 3–5
isElite: true
скиллов: 3–4 (у обычного моба 0–2), обязательно хотя бы одна «фаза»
  (self_hp_below) и/или opener
nothingWeight: 0 (босс всегда что-то дропает)
```

Санити-чек босса: игрок соответствующего уровня в среднем шмоте должен убивать
его за **40–90 секунд**, потратив 50–80% HP. Урон одного скилла босса не должен
превышать **35% max HP** игрока-одноклассника того же уровня (стан+нюк комбо —
не больше 50%).

### Скиллы классов — бюджет (из Warrior/Mage)

| Слот | Unlock | Роль | CD | Cost (% макс. ресурса) | baseDamage | scalingRatio |
|---|---|---|---|---|---|---|
| 1 | 3 | хлебный нюк | 3–4s | ~15 | 25–35 | 1.0–1.2 |
| 2 | 6 | контроль (stun/slow) | 8–10s | ~20 | 10–15 | 0.5–0.6 |
| 3 | 10 | утилити (buff/absorb) | 18–20s | ~25 | 0 | 0–0.5 |
| 4 | 15 | тяжёлый нюк (длинный каст) | 12–15s | ~35–40 | 40–80 | 1.2–1.8 |
| 5 | 20 | нишевый нюк (execute/бурст) | 8–10s | ~30 | 50–60 | 1.4–1.6 |
| 6 | 25 | ультимативный (дефанс/DoT) | 20–28s | ~40–45 | 0–20 | 0–0.6 |

Ресурсная идентичность: RAGE-класс разгоняется (дешёвый слот 1, старт с 0),
MANA-класс фронтлоадит (может сразу слот 4, но истощается). Новый класс обязан
выбрать одну из двух систем и отыгрывать её паттерн.

Сумма стартовых атрибутов класса = **22** (Warrior 8/2/6/3/3, Mage 2/8/3/4/5).
Авто-рост за уровень в сумме = **6.5**. `baseHp`: танк ~22, кастер ~17,
середина ~19–20. `baseAttackSpeed`: 0.5 (медленный кастер) – 0.8 (мили) – 1.0
(быстрый мили).

---

## 3. LLM-промт: генерация босса

Скопировать блок целиком, заполнить `[...]`, отдать ИИ. Результат — JSON для
админки (страница Monsters: основная форма + inline-таблица скиллов + дроп).

````
Ты — гейм-дизайнер мобильной геолокационной RPG Troy (dark fantasy, пиксель-арт).
Сгенерируй БОССА для игры по жёстким правилам ниже. Отвечай ТОЛЬКО валидным JSON
по заданной структуре, без комментариев вне JSON.

## Вводные
- Уровень босса: [LEVEL]
- Тематика/локация: [например: кладбищенская нежить / лесная чаща / горные руины]
- Особенность механики (опционально): [например: фаза ярости на 30% HP]

## Правила движка (нарушение = брак)
- damageType: только PHYSICAL или MAGICAL. scalingStat: только STR или INT
  (STR моба = его физ. сила, INT = маг. сила).
- effectType: NONE | STUN | SLOW | DOT | BUFF | ABSORB | HEAL.
  DOT: effectValue = урон/сек, SLOW: фикс. −30% скорости атаки (value 0),
  BUFF: effectValue = +% урона, HEAL: разовое лечение.
- condition скилла: always | opener | self_hp_below | target_hp_below.
  Для *_hp_below обязателен conditionValue (порог в %), иначе conditionValue: null.
- Мобы выбирают скилл по sortOrder (меньше = приоритетнее): первый готовый по CD
  и условию. Ставь узкие условия (opener, hp_below) на меньший sortOrder, always — последним.
- Урон скилла считается как baseDamage + stat × scalingRatio, потом режется
  бронёй игрока по формуле def/(def+100).

## Баланс (уровень L = [LEVEL])
- hp = (21×L + 22) × 2.5..3.0
- strength ≈ (2.8×L + 5) × 1.2..1.4 — если босс физический; для кастера
  перелей 60–70% в intelligence
- armor ≈ 1.6×L × 1.3..1.5; magicResist ≈ L × 1.3..1.5 (кастеру MR выше)
- expReward = (0.5×L² + 9.5×L + 10) × 3..4; goldReward ≈ 0.42 × expReward × 3..5
- attackSpeed 0.7–1.1; dodge 0 (юркому боссу до 5)
- 3–4 скилла. Обязательно: минимум один с condition=self_hp_below (смена фазы)
  или opener. Один скилл не должен снимать больше ~35% HP игрока того же уровня
  (у игрока-война уровня L примерно hp ≈ 100 + 24×L).
- Скиллы босса: baseDamage крупного нюка ≈ 3–5 × (его уровень), scalingRatio 0.8–1.5,
  cooldownSec 6–25, castTimeSec 0–2.5 (длинный каст = сигнал игроку).

## Формат ответа
{
  "monster": {
    "name": "...",                  // англ., 1–3 слова, dark fantasy
    "level": 0,
    "hp": 0,
    "strength": 0,
    "intelligence": 0,
    "armor": 0,
    "magicResist": 0,
    "attackSpeed": 1.0,
    "dodge": 0,
    "isElite": true,
    "spawnable": true,
    "nothingWeight": 0,
    "expReward": 0,
    "goldReward": 0
  },
  "skills": [
    {
      "code": "snake_case_code",
      "castTimeSec": 0,
      "cooldownSec": 0,
      "damageType": "PHYSICAL",
      "baseDamage": 0,
      "scalingStat": "STR",
      "scalingRatio": 0,
      "effectType": "NONE",
      "effectValue": 0,
      "effectDurationSec": 0,
      "sortOrder": 0,
      "condition": "always",
      "conditionValue": null,
      "designNote": "зачем скилл, как игрок должен на него отвечать"
    }
  ],
  "lore": "2–3 предложения на русском: кто это, почему здесь, чем опасен",
  "dropHint": "какие типы предметов и какой rarity логичны в дропе",
  "imagePrompt": "англ. промт для генерации спрайта — см. секцию 5, шаблон босса, заполнить [MONSTER DESCRIPTION] и [ACCENT COLOR]"
}

## Самопроверка перед ответом (выполни молча)
1. Все enum-значения из списка выше, ничего выдуманного.
2. hp/exp/gold в диапазонах формул.
3. sortOrder уникальны, условные скиллы раньше always.
4. Суммарный бурст (два самых сильных скилла подряд) < 50% HP игрока уровня L.
````

---

## 4. LLM-промт: генерация класса

Результат — JSON для админки (страница Classes: форма + 6 скиллов).

````
Ты — гейм-дизайнер мобильной геолокационной RPG Troy (dark fantasy, пиксель-арт).
Сгенерируй ИГРОВОЙ КЛАСС по жёстким правилам ниже. Отвечай ТОЛЬКО валидным JSON.

## Вводные
- Концепт класса: [например: паладин — гибрид урона и лечения / некромант — DoT и щиты]
- Ресурсная система: [RAGE или MANA — выбрать одну]

## Правила движка (нарушение = брак)
- Атрибуты только STR, INT, STA, AGI, SPI.
- scalingStat скиллов: ТОЛЬКО STR или INT. Класс обязан выбрать один основной
  дамаг-стат. «Урон от ловкости» невозможен — AGI даёт скорость атаки и крит пассивно.
- resourceType всех скиллов = ресурс класса. RAGE: макс 100, старт боя 0,
  копится автоатаками и полученным уроном. MANA: макс = INT×8 + baseMana,
  старт с полной, реген % в бою.
- effectType: NONE | STUN | SLOW | DOT | BUFF | ABSORB | HEAL.
- damageType: PHYSICAL или MAGICAL (null у чистых утилити).
- HP = baseHp + STA×10 + STR×2. Автоатака: физ. = weapon + STR×0.8,
  маг. = spell + INT×0.5.

## Баланс
- Стартовые атрибуты (уровень 1): сумма ровно 22. Основной стат 7–8,
  дамп-статы 2–3. (Warrior: 8/2/6/3/3, Mage: 2/8/3/4/5 — не дублируй их профиль.)
- Авто-рост за уровень: сумма ровно 6.5. Основной стат +2.5, второй +1.5..2.0.
- baseHp: 17 (стекло) — 22 (танк). baseMana: 0 у MANA-класса (всё от INT),
  0 у RAGE. baseAttackSpeed: 0.5–0.8 (0.8 быстрый мили, 0.5 медленный кастер).
- Ровно 6 скиллов, слоты и бюджет:
  | slot | unlockLevel | роль | CD | cost | baseDamage | scalingRatio |
  | 1 | 3  | хлебный нюк        | 3–4s   | ~15 | 25–35 | 1.0–1.2 |
  | 2 | 6  | контроль stun/slow | 8–10s  | ~20 | 10–15 | 0.5–0.6 |
  | 3 | 10 | утилити buff/absorb/heal | 18–20s | ~25 | 0 | 0–0.5 |
  | 4 | 15 | тяжёлый нюк, каст 1–2.5s | 12–15s | ~35–40 | 40–80 | 1.2–1.8 |
  | 5 | 20 | нишевый бурст/execute | 8–10s | ~30 | 50–60 | 1.4–1.6 |
  | 6 | 25 | ультимативный дефанс/DoT | 20–28s | ~40–45 | 0–20 | 0–0.6 |
  cost для RAGE — в очках ярости (макс 100), для MANA — сопоставимо с Mage
  (15/20/25/40/30/45 при мане ~64 на 1 уровне, скиллы верхних слотов
  балансируй под ману уровня анлока: мана ≈ (8 + 2.5×(L−1)) × 8).
- Ресурсная идентичность обязана читаться: RAGE-класс не может иметь дешёвый
  слот-4 нюк (нечем платить в начале боя), MANA-класс не должен получать ресурс от урона.

## Формат ответа
{
  "class": {
    "code": "snake_case",           // стабильный код для клиента
    "name": "...",                  // англ. название
    "nameRu": "...",
    "description": "2–3 предложения на русском: роль, стиль игры, сильные/слабые стороны",
    "strength": 0, "intelligence": 0, "stamina": 0, "agility": 0, "spirit": 0,
    "baseHp": 0, "baseMana": 0, "baseAttackSpeed": 0,
    "resourceType": "RAGE",
    "isActive": false,              // включаем вручную после балансировки
    "autoGrowthPerLevel": { "strength": 0, "intelligence": 0, "stamina": 0, "agility": 0, "spirit": 0 },
    "autoAttack": "описание автоатаки: тип урона и формула"
  },
  "skills": [
    {
      "slot": 1, "unlockLevel": 3,
      "code": "snake_case", "name": "...",
      "castTimeSec": 0, "cooldownSec": 0,
      "resourceType": "RAGE", "resourceCost": 0,
      "damageType": "PHYSICAL", "baseDamage": 0,
      "scalingStat": "STR", "scalingRatio": 0,
      "effectType": "NONE", "effectValue": 0, "effectDurationSec": 0,
      "designNote": "роль скилла в ротации"
    }
  ],
  "identity": "1 абзац: чем геймплейно отличается от Warrior и Mage",
  "imagePrompt": "англ. промт для спрайта — см. секцию 5, шаблон класса"
}

## Самопроверка перед ответом (выполни молча)
1. Сумма стартовых атрибутов = 22, рост = 6.5.
2. Все скиллы платят ресурсом класса; кривая cost согласована с ресурсной системой.
3. scalingStat согласован с основным атрибутом (STR-класс не скейлится от INT).
4. Профиль атрибутов не повторяет Warrior/Mage.
5. DPS-прикидка слота 1 на уровне 3 сопоставима с Heavy Strike/Fireball (±20%).
````

---

## 5. Image-промты: спрайты и иконки

База — [character-generation-prompt.md](character-generation-prompt.md): единый
стиль-блок, палитра из [pixel-art-design.md](pixel-art-design.md), negative prompt
обязателен. Здесь — специфика под спрайт-листы, которые реально ест движок.

### Формат спрайт-листа (ClassSpriteSheet)

Визуал хранится как webp-спрайт-лист в S3 + JSON-настройки в БД:

```
{ url, columns, rows, frameCount, fps, skipFrames? }
```

Дефолт сетки в админке: **4 колонки × 6 рядов, 19 кадров, 10 fps**.

Слоты анимаций:
- **Класс**: `spriteIdle` (стоит), `spriteWalk` (карта), `spriteAttack` (автоатака),
  `spriteAttackIdle` (боевая стойка) + `spriteAttack` на каждый скилл (ClassSkill).
- **Моб/босс**: `iconUrl` (иконка на карте), `spriteIdle`, `spriteAttack`
  + `spriteAttack` на каждый скилл (MonsterSkill).

> Генераторы картинок плохо делают целые sprite sheets — рабочий пайплайн:
> сгенерировать **одну ключевую позу** персонажа (промты ниже), добиться
> консистентности (seed lock / референс-картинка), затем анимационные кадры
> генерировать с этим референсом («same character, mid-swing attack frame»)
> или дорисовывать в Aseprite. Сетку листа собирать вручную/скриптом.

### Шаблон: босс

```
dark fantasy pixel art boss monster, 32-bit retro RPG style, visible pixels but high detail,
dark background (#0D0D0F), front-facing full body sprite, centered on canvas,
no anti-aliasing, clean pixel edges,

[MONSTER DESCRIPTION — из imagePrompt LLM-генерации: тело, броня/шкура, оружие,
 светящиеся элементы, поза],
massive imposing silhouette, boss-level enemy, larger and more detailed than regular mobs,
subtle glow on key elements (eyes, weapon, runes),
color palette: muted darks with [ACCENT COLOR] accents and warm gold details,

medieval dark fantasy aesthetic, game enemy sprite,
inspired by Octopath Traveler and Darkest Dungeon pixel art
```

Правило акцентного цвета: у босса **один** доминирующий акцент, читаемый на
мини-спрайте карты (ядовито-зелёный, инфернально-красный, призрачно-голубой,
некро-фиолетовый…). Золото — только вторичный акцент (это цвет UI).

Кадры для листов (те же вводные + замена последней строки позы):
- idle: `breathing idle pose, subtle menacing sway, frame N of idle animation loop`
- attack: `mid-attack frame, [weapon/claw] swing with motion arc, aggressive lunge`
- скилл X: `casting [skill visual: напр. necrotic burst], [ACCENT COLOR] energy flare`

### Шаблон: класс

```
dark fantasy pixel art character, 32-bit retro RPG style, visible pixels but high detail,
dark background (#0D0D0F), warm amber-gold accent highlights,
front-facing full body sprite, centered on canvas, no anti-aliasing, clean pixel edges,

[CLASS DESCRIPTION — из imagePrompt LLM-генерации: телосложение, броня/одежда,
 оружие, классовый магический эффект],
color palette: [2 основных тона класса] with gold accents,
heroic ready pose, standing,

muted dark color palette, medieval dark fantasy aesthetic,
inspired by Octopath Traveler and Darkest Dungeon pixel art,
single character, game asset sprite sheet style
```

Кадры: `idle` / `walk cycle frame, side profile` / `attack swing frame` /
`combat stance, weapon raised` / скиллы по designNote.

Иконка (класс `iconUrl`, скиллы, моб на карте):

```
dark fantasy pixel art icon, 64x64 pixel style, dark background,
[SUBJECT: emblem/weapon/skill effect], golden border frame,
clean pixel edges, no anti-aliasing, RPG game UI icon
```

Negative prompt — всегда (из character-generation-prompt.md):

```
smooth gradients, anti-aliasing, blurry, 3D render, realistic, photorealistic,
watercolor, oil painting, sketch, cartoon, chibi, anime, modern clothing,
sci-fi elements, bright neon colors, white background, multiple characters,
text, watermark, signature, low quality, deformed, extra limbs
```

---

## 6. Пайплайн: от промта до игры

```
1. LLM-промт (секция 3/4) → JSON с данными + lore + imagePrompt
2. Ревью баланса человеком: прогнать чек-лист самопроверки руками,
   прикинуть TTK против игрока целевого уровня
3. Админка:
   - Класс: Classes → создать (isActive=false), внести атрибуты и 6 скиллов
   - Босс: Monsters → создать (isElite=true), скиллы inline-таблицей,
     дроп-таблица по dropHint
4. Image-промты (секция 5) → генерация ключевой позы → консистентные кадры
   → сборка листа → загрузка через админку (конвертация в webp + S3 автоматом)
5. Настройка сетки листа в админке (columns/rows/frameCount/fps, превью там же)
6. Плейтест на dev: бой против целевого уровня, правка чисел в админке
7. Класс: isActive=true, когда баланс подтверждён. Босс: добавить в monsterIds
   нужной SpawnZone
```

### Чего генератору делать нельзя

- Выдумывать поля, enum-значения или механики вне канона (секция 1).
- Генерировать «пассивки», ауры, призывы, АоЕ по нескольким целям — движок
  боя строго 1×1, эффекты только из EffectType.
- Второй ресурс, комбо-поинты, заряды — ресурс один: RAGE или MANA.
- Скиллы классов вне сетки слотов 1–6 / уровней 3–25.
- Золотой (#D4A827) как основной цвет монстра — зарезервирован под UI и героику.
