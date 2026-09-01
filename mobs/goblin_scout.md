# Goblin Scout — Гоблин-разведчик

> Карточка — источник правды: числа меняются сначала здесь, потом в seed/админке и манифесте
> `troy-assets/assets/mobs/goblin_scout.yaml` (манифеста ещё нет — завести при генерации).

## 1. Название

| | |
|---|---|
| `code` манифеста | `goblin_scout` (snake_case; в БД моб ищется по `name`) |
| `name` (в БД, EN) | Goblin Scout |
| Название RU | Гоблин-разведчик |
| `isElite` | false |

## 2. Описание

**Роль в бою:** быстрый мили 3 уровня · колет часто и мелко · берётся давлением, HP немного — одна строка.

**Описание — `Monster.description` (в игре: тап по маркеру, интро боя; RU, ≤ 220):**
> Тощий гоблин в лохмотьях, глаза так и бегают. В открытый бой не рвётся: кружит рядом,
> тычет кривым ножом и целит туда, где не прикрыто.

## 3. Характеристики и награды

| | | | |
|---|---|---|---|
| level | 3 | hp | 78 |
| strength | 13 | intelligence | 2 |
| armor | 5 | magicResist | 1 |
| attackSpeed | 1.0 | dodge | 0 |
| expReward | 40 | goldReward | 16 |
| spawnable | true | nothingWeight | 0 |

Числа — из продакшн-сида, якорь lvl 3 в `content-generation.md`. Юркому разбойнику по кривым
допустимы dodge 3–8 — см. Расхождения.

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

Скиллов нет (0 — допустимо). Кандидат при балансе: подлый укол в спину на открытии боя
(`opener`, небольшой бонусный урон) — завести через карточку, seed/админку и манифест.

## 6. Арт: промты

Конвейер: `troy-assets/styles/mob.yaml` + манифест `assets/mobs/goblin_scout.yaml`;
итоговые промты после генерации — из `goblin_scout.state.json` сюда.

### Визуальный бриф

- Силуэт: тощий сгорбленный гоблин в капюшоне из мешковины, кривой нож остриём вниз,
  острые уши торчат из-под капюшона — капюшон + уши читаются на 32 px.
- Цвета: тускло-оливковая кожа + серо-бурые лохмотья; `accentColor` — dull olive.
- Размеры: моб 96–128, иконка-маркер 64→×2 (рисуется 32–48).

### `subject`

```
A skinny hunched goblin scout with dull olive skin, pointed ears poking through a ragged
burlap hood, shifty yellow eyes, a crooked rusty dagger held low, tattered rags and a small
loot pouch on the belt. Color scheme: dull olive skin, grey-brown rags, muted dark medieval fantasy.
```

### Поля манифеста

| Поле | Значение |
|---|---|
| `emblem` (маркер) | a hooded goblin head with pointed ears and a crooked dagger |
| `accentColor` | dull olive |
| `weaponRest` | the crooked dagger held low in a reverse grip, knees bent |
| `attackMotion` | Circles half a step, then a quick low stabbing lunge with the dagger |
| `hitMotion` | Yelps and hops back, clutching the shoulder |
| `deathMotion` | Crumples to the knees, drops the dagger, falls flat |
| `arena` (фон арены) | An ambush spot on a narrow forest trail: dense bushes, a crooked wooden watch-post with a rag flag, scattered stolen sacks |

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

- Моб есть в seed (`Goblin Scout`), `description` в seed добавлен (01.09); на dev описание
  завести через админку (seed не гонять).

### Расхождения код ↔ документы

- По кривым `content-generation.md` юркому разбойнику допустимы dodge 3–8, в seed — 0.
  Кандидат на балансовую правку.
