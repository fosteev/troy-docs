# Database — Схема базы данных

## Обзор

Два ключевых разделения:
- **User** — аккаунт (авторизация, верификация email)
- **Character** — игровой персонаж (класс, статы, уровень, инвентарь)

Один User может иметь несколько Character, но только один активный на карте.

---

## Модели

### User (аккаунт)

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| email | String, unique | Адрес почты (уникален в системе) |
| passwordHash | String | Хеш пароля |
| createdAt | DateTime | |
| updatedAt | DateTime | |

User создаётся **только после** верификации email. Если email подтверждён — можно задать пароль и создать аккаунт.

Связи: `characters[]`, `refreshTokens[]`, `passwordResets[]`

---

### EmailVerification (верификация почты)

Верификация происходит **до** создания User. Флоу:
1. Пользователь вводит email → создаётся запись с 6-значным кодом, код отправляется на почту
2. Пользователь вводит код → `verified = true`
3. Только после этого можно создать User с этим email + пароль

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| email | String | Адрес почты |
| code | String | 6-значный код |
| expiresAt | DateTime | Время истечения (now + 15 мин) |
| verified | Boolean, default false | Успешно ли подтверждён |
| createdAt | DateTime | |

---

### Character (игровой персонаж)

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| userId | UUID, FK → User | |
| name | String, unique | Имя персонажа |
| class | Enum: WARRIOR, MAGE | Класс |
| level | Int, default 1 | Уровень (макс. 30) |
| exp | Int, default 0 | Текущий опыт |
| gold | Int, default 0 | Золото |
| isActive | Boolean, default false | Активный на карте (один на User) |
| **Базовые атрибуты** | | |
| strength | Float | STR (стартовое + авто-рост за уровни) |
| intelligence | Float | INT |
| stamina | Float | STA |
| agility | Float | AGI |
| spirit | Float | SPI |
| **Свободные очки** | | |
| freePointsStr | Int, default 0 | Очки игрока в STR |
| freePointsInt | Int, default 0 | Очки игрока в INT |
| freePointsSta | Int, default 0 | Очки игрока в STA |
| freePointsAgi | Int, default 0 | Очки игрока в AGI |
| freePointsSpi | Int, default 0 | Очки игрока в SPI |
| **Текущее состояние** | | |
| currentHp | Float | Текущее HP (может быть < максимума) |
| currentMana | Float, default 0 | Текущая мана (для Mage) |
| currentRage | Float, default 0 | Текущая ярость (для Warrior, 0..100) |
| battleLockUntil | DateTime? | До какого времени персонаж выведен из строя (`incapacitated`) после поражения |
| **Геолокация** | | |
| lat | Float? | Широта |
| lng | Float? | Долгота |
| lastMovedAt | DateTime? | Последнее перемещение |
| createdAt | DateTime | |
| updatedAt | DateTime | |

Связи: `inventory[]`, `battleLogs[]`

#### Стартовые атрибуты по классу

| Атрибут | Warrior | Mage |
|---|---|---|
| strength | 8 | 2 |
| intelligence | 2 | 8 |
| stamina | 6 | 3 |
| agility | 3 | 4 |
| spirit | 3 | 5 |

#### Авто-рост за уровень

При каждом левел-апе базовые атрибуты увеличиваются (прибавляем к полям в БД):

| Атрибут | Warrior | Mage |
|---|---|---|
| strength | +2.5 | +0.5 |
| intelligence | +0.5 | +2.5 |
| stamina | +2.0 | +1.0 |
| agility | +1.0 | +0.8 |
| spirit | +0.5 | +1.0 |

#### Производные статы (вычисляются в коде, не хранятся в БД)

```
total_str = strength + freePointsStr + equipment_str_bonus
total_int = intelligence + freePointsInt + equipment_int_bonus
total_sta = stamina + freePointsSta + equipment_sta_bonus
total_agi = agility + freePointsAgi + equipment_agi_bonus
total_spi = spirit + freePointsSpi + equipment_spi_bonus

maxHp        = base_hp + total_sta * 10 + total_str * 2
maxMana      = base_mana + total_int * 8                  // только для Mage
physAtk      = base_atk + total_str * 2
magicAtk     = base_matk + total_int * 2.5
armor        = base_armor + total_sta * 2 + equipment_armor
magicResist  = base_mr + total_int * 1.5 + equipment_mr
attackSpeed  = base_as * (1 + total_agi * 0.01)
critChance   = base_crit + total_agi * 0.15
dodge        = equipment_dodge
ragePerAuto  = 5 * (1 + total_spi * 0.02)                // Warrior
manaRegen    = maxMana * regen_rate * (1 + total_spi * 0.02) // Mage
```

Базовые значения по классу — см. [stats-and-formulas.md](../game-design/stats-and-formulas.md).

#### Правила ресурса по классу

- `class = WARRIOR`: используется `currentRage` (0..100), `currentMana = 0`
- `class = MAGE`: используется `currentMana` (0..maxMana), `currentRage = 0`
- `class = MAGE`: при каждом старте боя выполняется `currentMana = maxMana`
- Вне боя у Warrior `currentRage` принудительно сбрасывается в `0`

Рекомендуемые `CHECK`-ограничения:

```sql
CHECK (level BETWEEN 1 AND 30);
CHECK (current_rage BETWEEN 0 AND 100);
CHECK (exp >= 0 AND gold >= 0);
```

#### Правило поражения (геолокация)

- При `defeat` не меняем `lat/lng` (никакого респавна в другую точку)
- Выставляем `battleLockUntil = now() + interval '60 seconds'`
- Пока `now() < battleLockUntil`, бой для персонажа запрещён
- После окончания lock-а сервер восстанавливает `HP/Mana` до 30% и сбрасывает `Rage` в 0

#### Ограничение: один активный персонаж

Нужен DB-уровень, а не только код:

```sql
CREATE UNIQUE INDEX ux_character_one_active_per_user
ON character(user_id)
WHERE is_active = true;
```

---

### ClassSkill (справочник классовых скиллов)

Хранит балансные параметры скиллов Warrior/Mage (cast, cooldown, resource cost, эффекты).  
Разблокировка считается по `class + level`, отдельная таблица прогресса скиллов персонажа не нужна.

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| class | Enum: WARRIOR, MAGE | Класс, которому принадлежит скилл |
| slot | Int | Позиция в панели: 1..6 |
| unlockLevel | Int | Уровень открытия (3/6/10/15/20/25) |
| code | String | Системный код (`heavy_strike`, `meteor`) |
| name | String | Отображаемое имя |
| castTimeSec | Float | Время каста |
| cooldownSec | Float | Кулдаун |
| resourceType | Enum: RAGE, MANA | Тип ресурса |
| resourceCost | Float | Стоимость ресурса |
| damageType | Enum?: PHYSICAL, MAGICAL | Тип урона (nullable для чистых баффов) |
| baseDamage | Float, default 0 | Базовый урон |
| scalingStat | Enum?: STR, INT | Скейлящий атрибут |
| scalingRatio | Float, default 0 | Коэффициент скейла |
| effectType | Enum: NONE, STUN, SLOW, DOT, BUFF, ABSORB, HEAL | Тип эффекта |
| effectValue | Float, default 0 | Величина эффекта |
| effectDurationSec | Float, default 0 | Длительность эффекта |
| isActive | Boolean, default true | Можно быстро выключить скилл из баланса |
| createdAt | DateTime | |
| updatedAt | DateTime | |

Уникальные ключи:
- `(class, slot)`
- `(class, code)`

---

### RefreshToken

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| token | String, unique | JWT refresh token |
| userId | UUID, FK → User | |
| expiresAt | DateTime | |
| createdAt | DateTime | |

---

### PasswordReset

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| token | String, unique | Токен сброса |
| userId | UUID, FK → User | |
| expiresAt | DateTime | |
| used | Boolean, default false | |
| createdAt | DateTime | |

---

### Item (предмет)

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| name | String | Название |
| type | Enum: WEAPON, ARMOR, CONSUMABLE | Тип предмета |
| slot | Enum?: HEAD, BODY, WEAPON, SHIELD, BOOTS, ACCESSORY | Слот экипировки |
| rarity | Enum: COMMON..LEGENDARY, default COMMON | Редкость |
| **Бонусы к атрибутам** | | |
| strBonus | Int, default 0 | +STR |
| intBonus | Int, default 0 | +INT |
| staBonus | Int, default 0 | +STA |
| agiBonus | Int, default 0 | +AGI |
| spiBonus | Int, default 0 | +SPI |
| **Бонусы к защите** | | |
| armorBonus | Int, default 0 | +Armor |
| magicResistBonus | Int, default 0 | +Magic Resist |
| **Бонусы к урону** | | |
| physDmgBonus | Int, default 0 | +Physical Damage (base_weapon_dmg) |
| magicDmgBonus | Int, default 0 | +Magic Damage (base_spell_dmg) |
| iconUrl | String? | URL иконки |

Связи: `inventory[]`, `dropTables[]`

---

### CharacterInventory (инвентарь персонажа)

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| characterId | UUID, FK → Character | |
| itemId | UUID, FK → Item | |
| quantity | Int, default 1 | Количество |
| isEquipped | Boolean, default false | Экипирован ли |

Уникальный ключ: `(characterId, itemId)`

---

### Monster (монстр)

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| name | String | Название |
| level | Int | Уровень |
| hp | Int | Здоровье |
| strength | Int, default 0 | Физическая сила (для урона) |
| intelligence | Int, default 0 | Магическая сила |
| armor | Int, default 0 | Броня |
| magicResist | Int, default 0 | Маг. сопротивление |
| attackSpeed | Float, default 1.0 | Скорость атаки |
| dodge | Float, default 0 | Уклонение (%), у обычных мобов 0 |
| isElite | Boolean, default false | Элитный моб (может иметь dodge > 0) |
| expReward | Int | Награда опытом |
| goldReward | Int | Награда золотом |
| iconUrl | String? | |

Связи: `dropTables[]`, `battleLogs[]`, `monsterSkills[]`

---

### MonsterSkill (скиллы мобов)

Мобы используют скиллы только по кулдауну, без ресурсной системы.

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| monsterId | UUID, FK → Monster | |
| code | String | Системный код |
| castTimeSec | Float, default 0 | Время каста |
| cooldownSec | Float | Кулдаун |
| damageType | Enum?: PHYSICAL, MAGICAL | Тип урона |
| baseDamage | Float, default 0 | Базовый урон |
| scalingStat | Enum?: STR, INT | Скейл |
| scalingRatio | Float, default 0 | Коэффициент скейла |
| effectType | Enum: NONE, STUN, SLOW, DOT, BUFF, ABSORB, HEAL | Тип эффекта |
| effectValue | Float, default 0 | Величина эффекта |
| effectDurationSec | Float, default 0 | Длительность эффекта |
| sortOrder | Int, default 0 | Приоритет в ротации |

Уникальный ключ: `(monsterId, code)`

---

### DropTable (таблица дропа)

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| monsterId | UUID, FK → Monster | |
| itemId | UUID, FK → Item | |
| weight | Int | Вес (для вероятности) |
| minQty | Int, default 1 | Мин. количество |
| maxQty | Int, default 1 | Макс. количество |

---

### BattleLog (лог боёв)

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| characterId | UUID, FK → Character | |
| monsterId | UUID, FK → Monster | |
| result | Enum: VICTORY, DEFEAT, ESCAPE | Результат боя |
| expDelta | Int | Изменение XP (может быть отрицательным при поражении) |
| goldDelta | Int | Изменение золота |
| lootJson | Json? | Выпавший лут (null при defeat/escape) |
| durationSec | Int | Длительность боя |
| hpAfter | Float | HP персонажа после завершения боя |
| manaAfter | Float, default 0 | Mana после завершения боя |
| rageAfter | Float, default 0 | Rage после завершения боя |
| createdAt | DateTime | |

---

### SpawnZone (зона спавна)

Поле `geometry` (PostGIS POLYGON) управляется через raw SQL, не в ORM.

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| name | String | Название зоны |
| zoneType | String | Тип зоны |
| monsterIds | String[] | ID монстров для спавна |
| minLevel | Int | Мин. уровень монстров |
| maxLevel | Int | Макс. уровень монстров |

---

### active_spawns (активные спавны)

Вне ORM — PostGIS GEOGRAPHY type, управляется через raw SQL.

| Поле | Тип | Описание |
|---|---|---|
| id | UUID, PK | |
| monster_id | UUID, FK → Monster | |
| spawn_zone_id | UUID, FK → SpawnZone | |
| location | GEOGRAPHY(POINT, 4326) | Координаты на карте |
| spawned_at | TIMESTAMPTZ | Время спавна |
| alive | Boolean, default true | Жив ли |

---

## Enums

| Enum | Значения |
|---|---|
| CharacterClass | WARRIOR, MAGE |
| ResourceType | RAGE, MANA |
| DamageType | PHYSICAL, MAGICAL |
| ScalingStat | STR, INT |
| EffectType | NONE, STUN, SLOW, DOT, BUFF, ABSORB, HEAL |
| BattleResult | VICTORY, DEFEAT, ESCAPE |
| ItemType | WEAPON, ARMOR, CONSUMABLE |
| ItemSlot | HEAD, BODY, WEAPON, SHIELD, BOOTS, ACCESSORY |
| Rarity | COMMON, UNCOMMON, RARE, EPIC, LEGENDARY |

---

## Диаграмма связей

```
EmailVerification (standalone, не привязана к User)

User 1──N Character
User 1──N RefreshToken
User 1──N PasswordReset

ClassSkill (standalone справочник по CharacterClass)

Character 1──N CharacterInventory
Character 1──N BattleLog

Item 1──N CharacterInventory
Item 1──N DropTable

Monster 1──N DropTable
Monster 1──N BattleLog
Monster 1──N MonsterSkill
```
