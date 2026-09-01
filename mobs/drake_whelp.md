# Drake Whelp — Молодой дрейк

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/drake_whelp.yaml` (манифеста ещё нет — завести при генерации).

## 1. Название

| | |
|---|---|
| `code` манифеста | `drake_whelp` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Drake Whelp |
| Название RU | Молодой дрейк |
| `isElite` | false |

## 2. Описание

**Роль в бою:** топовый обычный моб (кап 10) · смешанный урон, много HP · берётся полным арсеналом 10 уровня — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Молодой дрейк, ещё не вставший на крыло, — но уже с клыками, когтями и скверным характером.
> Плюётся огнём, хлещет хвостом и не понимает, почему его должны бояться меньше взрослых.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 10 | hp | 221 |
| strength | 33 | intelligence | 10 |
| armor | 16 | magicResist | 10 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 160 | goldReward | 80 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида, якорь lvl 10 в `content-generation.md`.

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

Скиллов нет (0 — допустимо). Кандидаты при балансе: огненный плевок (`always`, MAGICAL,
телеграфированный каст) и/или удар хвостом на открытии (`opener`) — топовому мобу просятся
оба (лимит 2). Завести через карточку, seed/админку и манифест.

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/drake_whelp.yaml`;
итоговые промты после генерации — из `drake_whelp.state.json` сюда.

### Визуальный бриф

- Силуэт: приземистый ящер на четырёх лапах, короткие недоразвитые крылья, рогатая голова,
  дымок из ноздрей, длинный хвост — рожки + крылья читаются на 32 px.
- Цвета: багровая чешуя + тёмное брюхо, огненно-оранжевые акценты (пасть, ноздри);
  `accentColor` — fiery orange.
- Размеры: моб 128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A young stocky drake on four clawed legs with crimson scales, a darker underbelly, stubby
half-grown wings, small horns, wisps of smoke from the nostrils and a long swaying tail.
Color scheme: crimson scales, dark grey underbelly, fiery orange glow in the maw, muted dark
medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a horned drake head breathing a small wisp of flame |
| `accentColor` | fiery orange |
| `weaponRest` | crouched on four legs, wings folded, the tail swaying slowly |
| `attackMotion` | Rears the head back, then snaps forward with claws and a short burst of flame |
| `hitMotion` | Screeches and flaps the stubby wings, staggering back |
| `deathMotion` | Staggers, folds the wings and slumps down, the smoke fades |
| `arena` (фон арены) | A scorched rocky nest site on a cliff ledge: charred bones and blackened stones, glowing embers in cracks, smoky orange haze |

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

- Моб есть в seed (`Drake Whelp`), `description` в seed добавлен (01.09); на dev описание
  завести через админку (seed не гонять).

### Расхождения код ↔ документы

- Нет.
