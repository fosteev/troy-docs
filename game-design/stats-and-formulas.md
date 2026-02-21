# Stats & Formulas — Характеристики и формулы

## Базовые атрибуты

Пять основных атрибутов, от которых зависит всё остальное:

| Атрибут | Описание |
|---|---|
| **Strength (STR)** | Физическая сила. Увеличивает физический урон и немного HP |
| **Intelligence (INT)** | Магическая сила. Увеличивает магический урон, максимальную ману и Magic Resist |
| **Stamina (STA)** | Выносливость. Увеличивает HP и броню |
| **Agility (AGI)** | Ловкость. Увеличивает скорость атаки, уменьшает время каста и кулдаунов, даёт шанс крита |
| **Spirit (SPI)** | Дух. Увеличивает генерацию ярости (Warrior) и регенерацию маны (Mage) |

### Источники атрибутов

1. **Стартовые** — зависят от класса (см. [classes.md](classes.md))
2. **Авто-рост за уровень** — фиксированный по классу
3. **Свободные очки** — 2 за уровень, распределяет игрок
4. **Экипировка** — бонусы от шмота

```
total_attribute = base + (auto_growth * (level - 1)) + free_points_invested + equipment_bonus
```

---

## Ресурсные системы

У каждого класса свой ресурс для использования скиллов:

### Rage (Ярость) — Warrior

Ярость **не существует** вне боя. В начале боя Rage = 0. Накапливается в бою, тратится на скиллы.

```
Rage: 0..100 (фиксированный максимум, не скейлится)

Генерация ярости:
  При получении урона:  rage += damage_taken * 0.15 * (1 + SPI * 0.02)
  При автоатаке:        rage += 5 * (1 + SPI * 0.02)

После каждого изменения:
  rage = clamp(rage, 0, 100)

Затухание:
  Вне боя rage сбрасывается в 0
```

Spirit влияет на скорость накопления ярости. При SPI=20 множитель = 1.4 (+40% генерация).

### Mana (Мана) — Mage

Каждый бой начинается с полной маны. Тратится на скиллы, восстанавливается в бою со временем.

```
Max_Mana = base_mana + INT * 8

Регенерация маны в бою:
  mana_regen = max_mana * 0.01 * (1 + SPI * 0.02) per second

После списания/регенерации:
  mana = clamp(mana, 0, max_mana)
```

Spirit влияет на скорость регенерации маны в бою. При SPI=20 множитель = 1.4 (+40% реген).

---

## Производные характеристики

Вычисляются из базовых атрибутов. Не задаются напрямую.

### HP (Здоровье)

```
HP = base_hp + STA * 10 + STR * 2
```

- `base_hp` — зависит от класса (Warrior: 22, Mage: 17)
- Основной источник: Stamina
- Strength даёт немного HP как бонус

### Mana (только Mage)

```
Mana = base_mana + INT * 8
```

- `base_mana` — зависит от класса (Mage: 0)
- Единственный источник максимума — Intelligence
- Warrior **не имеет маны**, использует Rage

### Physical Attack (Физическая атака) — UI-стат

```
Phys_ATK = base_atk + STR * 2
```

- `base_atk` — от класса и оружия
- **Отображается в профиле** как сводный показатель физической мощи
- В бою **не используется напрямую**: урон скиллов и автоатаки считается по отдельным формулам (см. [combat.md](combat.md) — `base_damage + scaling_stat * scaling_ratio`)

### Magic Attack (Магическая атака) — UI-стат

```
Magic_ATK = base_matk + INT * 2.5
```

- `base_matk` — от класса и оружия
- **Отображается в профиле** как сводный показатель магической мощи
- В бою **не используется напрямую**: урон скиллов и автоатаки считается по отдельным формулам (см. [combat.md](combat.md))

### Armor (Броня)

```
Armor = base_armor + STA * 2 + equipment_armor
```

- Снижает **физический** входящий урон
- Основной источник: Stamina и шмот

### Magic Resist (Магическое сопротивление)

```
Magic_Resist = base_mr + INT * 1.5 + equipment_mr
```

- Снижает **магический** входящий урон
- Основной источник: Intelligence и шмот

### Attack Speed (Скорость атаки)

```
Attack_Speed = base_as * (1 + AGI * 0.01)
time_between_attacks = 1 / Attack_Speed (сек)
```

Базовые значения:

| Класс | base_as | Интервал при AGI=0 |
|---|---|---|
| Warrior | 0.8 | 1.25 сек |
| Mage | 0.5 | 2.0 сек |

### Crit Chance (Шанс крит. удара)

```
Crit_Chance = base_crit + AGI * 0.15 (%)
```

- `base_crit` — 0% для всех классов
- Дополнительно может приходить от шмота

### Crit Multiplier (Множитель крита)

```
Crit_Multiplier = 2.0 (фиксированный)
```

В будущем может увеличиваться от шмота и пассивок.

### Dodge (Уклонение)

```
Dodge = equipment_dodge (%)
```

- Только от шмота и пассивок, не от атрибутов
- При уклонении — 0 урона

---

## Сводная таблица производных

| Характеристика | Формула |
|---|---|
| **HP** | `base_hp + STA × 10 + STR × 2` |
| **Mana** (Mage) | `base_mana + INT × 8` |
| **Rage** (Warrior) | 0–100, генерируется в бою, скейлится от SPI |
| **Armor** | `base_armor + STA × 2 + equipment` |
| **Magic Resist** | `base_mr + INT × 1.5 + equipment` |
| **Phys Attack** (UI) | `base_atk + STR × 2` |
| **Magic Attack** (UI) | `base_matk + INT × 2.5` |
| **Attack Speed** | `base_as × (1 + AGI × 0.01)` |
| **Crit Chance** | `base_crit + AGI × 0.15` (%) |
| **Crit Multiplier** | ×2.0 (фиксированный) |
| **Dodge** | от шмота (%) |
| **Rage Gen** (Warrior) | `base × (1 + SPI × 0.02)` |
| **Mana Regen** (Mage) | `base × (1 + SPI × 0.02)` |

---

## Формула расчёта урона

### Шаг 1: Raw Damage (сырой урон)

Для скилла:
```
raw_damage = skill_base_damage + scaling_stat * scaling_ratio
```

Для автоатаки:
```
raw_damage = base_weapon_dmg + scaling_stat * auto_scaling_ratio
```

### Шаг 2: Crit Check

```
if random(0..100) < Crit_Chance:
    raw_damage = raw_damage * Crit_Multiplier
```

### Шаг 3: Defense Reduction

```
defense = Armor         (если damage_type == physical)
defense = Magic_Resist   (если damage_type == magical)

damage_reduction = defense / (defense + 100)
```

### Шаг 4: Dodge Check

```
if random(0..100) < target_Dodge:
    final_damage = 0  (MISS)
else:
    final_damage = raw_damage * (1 - damage_reduction)
```

### Шаг 5: Apply Damage

```
target_HP = target_HP - final_damage
if target_HP <= 0:
    target is defeated
```

---

## Таблица снижения урона по Armor/MR

| Defense | Reduction % |
|---|---|
| 10 | 9.1% |
| 25 | 20% |
| 50 | 33.3% |
| 75 | 42.9% |
| 100 | 50% |
| 150 | 60% |
| 200 | 66.7% |
| 300 | 75% |

Формула `defense / (defense + 100)` обеспечивает diminishing returns — каждая следующая единица брони даёт меньше, но никогда не даёт 100% снижения.

---

## Примеры расчётов

### Warrior lvl 1 бьёт автоатакой моба с 10 Armor

```
raw_damage = 10 + 8 * 0.8 = 16.4
crit_chance = 0.45% → скорее всего не крит
reduction = 10 / (10 + 100) = 9.1%
final_damage = 16.4 * (1 - 0.091) = 14.9
rage_gained = 5 * (1 + 3 * 0.02) = 5.3
```

### Mage lvl 1 кастует Fireball на моба с 5 Magic Resist

```
raw_damage = 35 + 8 * 1.2 = 44.6
mana_cost = 15, remaining_mana = 64 - 15 = 49
crit_chance = 0.6% → скорее всего не крит
reduction = 5 / (5 + 100) = 4.8%
final_damage = 44.6 * (1 - 0.048) = 42.5
```
