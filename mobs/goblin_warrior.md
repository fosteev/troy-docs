# Goblin Warrior — Гоблин-вояка

> Эталонная карточка моба (пилот фазы B/C `roadmap/mobs`). Карточка — источник правды:
> числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/goblin_warrior.yaml`, не наоборот.

## 1. Название

| | |
|---|---|
| `code` манифеста | `goblin_warrior` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Goblin Warrior |
| Название RU | Гоблин-вояка |
| `isElite` | false |

## 2. Описание

**Роль в бою:** мили-дамагер · опасен телеграфированным ударом дубиной (Club Smash) ·
берётся уроном в окно каста — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Коренастый вояка гоблинского племени: ржавый нагрудник, помятый баклер и шипастая дубина.
> Дерётся нагло и просто — подпрыгивает и лупит со всего размаха; успей ответить, пока дубина в воздухе.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 4 | hp | 141 |
| strength | 16 | intelligence | 3 |
| armor | 7 | magicResist | 2 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 52 | goldReward | 22 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида (`troy-backend/prisma/seed.ts`), сидят между якорями
`content-generation.md` (lvl 3: 117 hp / 40 exp, lvl 5: 161 hp / 65 exp). `nothingWeight: 0` —
с моба всегда что-то падает.

## 4. Дроп

| Item | weight | minQty | maxQty |
|---|---|---|---|
| Health Potion | 60 | 1 | 2 |
| Leather Armor | 20 | 1 | 1 |
| Iron Sword | 12 | 1 | 1 |
| Knight Shield | 6 | 1 | 1 |
| Swift Boots | 2 | 1 | 1 |

Пока это общая seed-таблица всех 10 мобов; персональный дроп — контент-задача вне темы «Мобы».

## 5. Скиллы (0–2, у элиток до 2)

Алгоритм боя моба: скиллы проверяются по `sortOrder` (меньше — раньше), `condition` гейтит
(`always` / `opener` / `self_hp_below:N` / …) — см. `game-design/combat.md`.

| sortOrder | code | name (EN) | condition | Cast | CD | Dmg type | Base | Scaling | Эффект |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `mob_club_smash` | Club Smash | always | 1.0s | 7s | PHYSICAL | 14 | STR × 0.6 | — |

Один скилл: телеграфированный нюк на кулдауне. Урон ≈ 14 + 0.6×16 ≈ **24** до брони —
~8% max HP воина 4 ур. (hp ≈ 110 + 37×L ≈ 260), в бюджете «≤ 35%». Каст 1.0s — окно,
которое видно в ленте намерений.

**Club Smash** — `description` (в игре, RU): Подпрыгивает и обрушивает шипастую дубину двумя
руками — тяжёлый физический удар, ~24 урона до брони.
- `icon`: `a rusty spiked wooden club smashing down with a brown-orange dust impact`
- `cast`: `Club Smash — jumps up and slams the spiked club down with both hands, dust burst at the impact`

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/goblin_warrior.yaml`;
итоговые промты после генерации — из `goblin_warrior.state.json` сюда.

### Визуальный бриф

- Силуэт: коренастый и сгорбленный; шипастая дубина на плече; маленький круглый баклер;
  острые уши + зубастая ухмылка — опознавательный признак, читается на 32 px.
- Цвета: болезненно-зелёная кожа + ржавый оранжево-бурый металл, грязная кожа;
  `accentColor` для маркера — sickly green.
- Размеры: моб 128 (босс 192), иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A short stocky goblin warrior with green warty skin, pointed ears and a jagged toothy grin,
crude rusty iron chest plate over rags, a spiked wooden club in the right hand, a small
dented buckler on the left arm. Color scheme: sickly green skin, rusty brown-orange metal,
dirty leather, muted dark medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a snarling goblin head with pointed ears and a rusty spiked club |
| `accentColor` | sickly green |
| `weaponRest` | the spiked club resting on the shoulder and the buckler lowered |
| `attackMotion` | Winds the spiked club far back behind the head, then a heavy sideways smash |
| `hitMotion` | Flinches, the buckler flies up |
| `deathMotion` | Drops the club, clutches the chest, staggers |
| `arena` (фон арены) | A muddy goblin war-camp clearing at dusk: trampled dirt ground, crude wooden spike barricades, a smoldering campfire with faint embers, ragged banners on crooked poles, a dark forest edge behind |

### Слоты (канон: в бою моб справа, смотрит ВЛЕВО; клиент не зеркалит)

| Слот БД | Style | Кадры/fps | Промт |
|---|---|---|---|
| keyframeSide (влево) | `rd_pro__fantasy` | 128 | ✓ state (ниже) |
| `iconUrl` (маркер) | `rd_plus__skill_icon` ×2 | 64→128 | ✓ state (ниже) |
| `spriteIdle` | `rd_advanced_animation__idle` | 8 / 5 | ✓ state (ниже) |
| `spriteAttack` | `custom_action` | 8 / 12 | ✓ state (ниже) |
| `spriteHit` | `custom_action` | 6 / 12 | ✓ state (ниже) |
| `spriteDeath` | `custom_action` (или `__destroy`) | 8 / 8 | ✓ state (ниже) |
| `MonsterSkill.spriteAttack` | `custom_action` | 8 / 12 | раздел 5 |
| `arenaBackground` | `rd_pro__fantasy` 256 (opaque) | 1×1 | ✓ state (ниже) |

### Итоговые промты (из state, генерация 01.09, $1.56)

```
keyframeSide:  A short stocky goblin warrior with green warty skin, pointed ears and a jagged toothy grin, crude rusty iron chest plate over rags, a spiked wooden club in the right hand, a small dented buckler on the left arm. Color scheme: sickly green skin, rusty brown-orange metal, dirty leather, muted dark medieval fantasy. Strict side view in profile, facing to the LEFT, full body, feet visible, calm menacing stance with the spiked club resting on the shoulder and the buckler lowered, small margin to the canvas edge, centered, on a plain white background.
icon:          Map marker icon of a snarling goblin head with pointed ears and a rusty spiked club, one dominant sickly green color, bold readable silhouette, medieval dark fantasy, on a plain white background.
anim:idle:     Standing still facing left, extremely subtle and slow breathing, almost no movement, the spiked club resting on the shoulder and the buckler lowered, no weapon motion
anim:attack:   Winds the spiked club far back behind the head, then a heavy sideways smash, facing left, clear wind-up then a fast powerful strike with follow-through
anim:hit:      Flinches, the buckler flies up, facing left, takes a hit from the left: sharp recoil backwards to the right, brief stagger, then returns to the stance
anim:death:    Drops the club, clutches the chest, staggers, facing left, collapses and falls to the ground, the last frame lies still
skill icon:    Skill icon: a rusty spiked wooden club smashing down with a brown-orange dust impact, vivid readable silhouette, warm gold frame accents, medieval dark fantasy, on a plain white background.
skill cast:    Club Smash — jumps up and slams the spiked club down with both hands, dust burst at the impact, facing left, clear wind-up then the action with follow-through
arenaBackground: A muddy goblin war-camp clearing at dusk: trampled dirt ground, crude wooden spike barricades, a smoldering campfire with faint embers, ragged banners on crooked poles, a dark forest edge behind. Wide battle arena background scene, open trampled ground across the lower third where fighters stand, clear uncluttered middle, scenery and horizon in the upper half, moody lighting, no creatures, no people, no text, muted dark medieval fantasy environment.
```

### Чек-лист

- [x] маркер читается на карте (32 px, один доминирующий цвет) — зелёная башка с дубиной;
      нюанс: уши читаются как рога, на 32 px не мешает
- [x] idle/attack/hit/death; hit — отдача вправо; death — лежит в последнем кадре
      (в 1–2 кадрах удара attack/cast — цветные смазы, как у рыцаря: на 12 fps читается блюром)
- [x] скиллы (icon + cast), фон арены (нижняя треть свободна под бойцов)
- [ ] заведён в БД: seed + publish залил всё на dev (01.09); **проверка на устройстве — осталась**

## 7. Реализация

Моб (статы/дроп) — админка (или seed для базовых 10); publish находит его по `name` и заливает
визуал, `description`, фон арены, создаёт недостающие скиллы из `db:`-блоков манифеста.

- Моб есть в seed (`Goblin Warrior`, статы раздела 3), `description` в seed добавлен (01.09).
- Пилот прогнан 01.09: генерация $1.56, publish на dev залил описание, маркер, 4 листа,
  фон арены (1×1) и создал `mob_club_smash` из `db:`-блока (проверено через admin API).
  Осталась проверка на устройстве (см. чек-лист и фазу D roadmap).
- В seed моб-скиллы базовых 10 — при балансе контента.

### Расхождения код ↔ документы

- Seed-скиллы мобов (`mob_stun_slam`, `mob_fire_bolt`, …) прицеплены к `monsters[0]`/`monsters[1]`
  (фактически Slime и Forest Rat) — dev-проба боевого алгоритма, лору не соответствует;
  разнести по мобам при заполнении карточек остальных.
- Ключ скилла в манифесте был `club_smash` — переименован в `mob_club_smash` под конвенцию
  кодов БД (`mob_*`).
