# Character Generation Prompt — AI Image Generator

## Назначение

Универсальный промт для генерации персонажей Troy в едином визуальном стиле через ИИ-генераторы изображений (Midjourney, DALL-E, Stable Diffusion, Flux и т.д.).

---

## Base Style Prompt (основа для всех персонажей)

Этот блок вставляется в каждый промт как стилевая основа:

```
dark fantasy pixel art character, 32-bit retro RPG style, visible pixels but high detail,
dark background (#0D0D0F), warm amber-gold accent highlights (#D4A827),
front-facing full body sprite, centered on canvas, no anti-aliasing, clean pixel edges,
muted dark color palette with warm gold accents, medieval fantasy aesthetic,
inspired by Octopath Traveler and Darkest Dungeon pixel art style,
single character on solid dark background, game asset, transparent background ready
```

---

## Промты по классам

### Warrior (Воин)

```
dark fantasy pixel art character, 32-bit retro RPG style, visible pixels but high detail,
dark background, warm amber-gold accent highlights,
front-facing full body sprite, centered on canvas, no anti-aliasing, clean pixel edges,

muscular warrior, broad shoulders, heavy dark steel armor with golden rivets,
one-handed sword in right hand, shield with emblem in left hand,
helmet with visor and red plume, steel boots,
color palette: dark steel gray, deep crimson red, gold accents,
battle-ready heroic pose, standing firmly,

muted dark color palette, medieval dark fantasy aesthetic,
inspired by Octopath Traveler and Darkest Dungeon pixel art,
single character, game asset sprite sheet style
```

### Mage (Маг)

```
dark fantasy pixel art character, 32-bit retro RPG style, visible pixels but high detail,
dark background, warm amber-gold accent highlights,
front-facing full body sprite, centered on canvas, no anti-aliasing, clean pixel edges,

slender tall mage, long dark blue and purple robe with glowing runes,
wooden staff with glowing crystal on top in right hand,
hood partially covering face, glowing cyan eyes,
magical glow around hands, arcane energy particles,
color palette: deep navy blue, dark purple, cyan-blue glow, gold trim,
mystical pose, standing with staff,

muted dark color palette, medieval dark fantasy aesthetic,
inspired by Octopath Traveler and Darkest Dungeon pixel art,
single character, game asset sprite sheet style
```

### Rogue (Разбойник) — Planned

```
dark fantasy pixel art character, 32-bit retro RPG style, visible pixels but high detail,
dark background, warm amber-gold accent highlights,
front-facing full body sprite, centered on canvas, no anti-aliasing, clean pixel edges,

lean agile rogue, dark leather armor, hooded cloak,
dual daggers in both hands, belt with vials of poison,
half-face mask or bandana, sharp watchful eyes,
color palette: dark brown leather, charcoal black, poison green accents, gold buckles,
stealthy ready pose, slight crouch,

muted dark color palette, medieval dark fantasy aesthetic,
inspired by Octopath Traveler and Darkest Dungeon pixel art,
single character, game asset sprite sheet style
```

---

## Промты для монстров

### Шаблон монстра (база)

```
dark fantasy pixel art monster, 32-bit retro RPG style, visible pixels but high detail,
dark background (#0D0D0F), front-facing sprite, centered on canvas,
no anti-aliasing, clean pixel edges,
[MONSTER DESCRIPTION HERE],
muted dark color palette with [ACCENT COLOR] accents,
medieval dark fantasy aesthetic, game enemy sprite,
inspired by Octopath Traveler and Darkest Dungeon pixel art
```

### Примеры монстров по уровням

**Weak (lvl 1-5) — маленький спрайт:**
```
...small pixel art rat monster, mangy fur, glowing red eyes, sharp teeth,
aggressive stance, simple design, low-level enemy...
```

**Medium (lvl 6-15) — средний спрайт:**
```
...medium pixel art goblin warrior, rusty armor, crude sword,
green skin, pointed ears, menacing grin, mid-level enemy...
```

**Strong (lvl 16-25) — крупный спрайт:**
```
...large pixel art undead knight, dark corroded plate armor,
ghostly blue glow in helmet visor, spectral greatsword,
tattered cape, imposing presence, high-level enemy...
```

**Elite (lvl 25-30) — большой спрайт:**
```
...massive pixel art demon lord, dark red skin, towering horns,
burning eyes, infernal flames around fists,
spiked armor, huge wings partially spread, boss-level enemy...
```

---

## Промты для предметов (Loot Icons)

### Шаблон иконки предмета

```
dark fantasy pixel art item icon, 32x32 pixel icon style,
dark background, golden border frame,
[ITEM DESCRIPTION],
clean pixel edges, no anti-aliasing,
RPG inventory icon, game asset
```

### Примеры

**Оружие:**
```
...steel longsword with golden crossguard, slight glow on blade edge...
```

**Броня:**
```
...dark plate chestpiece with golden rivets, battle-worn texture...
```

**Магический предмет:**
```
...glowing purple crystal ring, arcane energy wisps, rare item purple border...
```

---

## Промты для UI-элементов

### Портрет персонажа (для карточки выбора)

```
dark fantasy pixel art character portrait, bust shot, 64x64 pixel style,
dark background with subtle vignette,
[CLASS-SPECIFIC DESCRIPTION: armor/robe details, face, expression],
warm amber-gold border frame, RPG character select portrait,
clean pixel edges, no anti-aliasing, game UI asset
```

### Фоновая сцена (Login Screen)

```
dark fantasy pixel art landscape, wide scene, atmospheric,
ancient stone ruins in dark forest, distant mountains on horizon,
scattered amber firefly particles, subtle mist,
color palette: deep blacks, dark blues, warm amber-gold light sources,
muted and moody, torch light casting warm glow on stone,
RPG game menu background, high detail pixel art,
inspired by Octopath Traveler environment art
```

---

## Negative Prompts (что исключать)

Добавлять в negative prompt для всех генераций:

```
smooth gradients, anti-aliasing, blurry, 3D render, realistic, photorealistic,
watercolor, oil painting, sketch, pencil drawing, cartoon, chibi, anime,
modern clothing, sci-fi elements, bright neon colors, white background,
multiple characters (unless specifically requested), text, watermark, signature,
low quality, jpeg artifacts, deformed, extra limbs
```

---

## Параметры генерации (рекомендации)

| Параметр | Значение |
|---|---|
| Aspect ratio | 1:1 для спрайтов, 9:16 для полноростовых, 16:9 для фонов |
| Resolution | 512x512 или 1024x1024 (затем downscale) |
| CFG Scale (SD) | 7-9 |
| Steps (SD) | 30-50 |
| Style (MJ) | `--style raw` для меньшей стилизации |
| Stylize (MJ) | `--s 250-400` |

---

## Как поддерживать единый стиль

1. **Всегда включать base style block** — первые 3 строки промта должны быть одинаковыми для всех персонажей
2. **Фиксированная палитра** — использовать HEX-коды из `pixel-art-design.md` в промте
3. **Референс "Octopath Traveler + Darkest Dungeon"** — эти две игры задают нужный уровень детализации и атмосферу
4. **Одинаковая поза** — front-facing, full body, centered — для консистентности спрайтов
5. **Seed lock (если поддерживается)** — фиксировать seed при генерации серии, менять только описание персонажа
6. **Batch-генерация** — генерировать всех персонажей одной серией, не возвращаясь к ним позже с другими настройками
7. **Negative prompt обязателен** — без него стиль будет дрифтить между генерациями
