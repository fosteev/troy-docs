# Troy — Image Reference Prompts (для генерации картинок-референсов)

> Промты под **генерацию изображений** (Midjourney / DALL·E / SDXL / Nano Banana и т.п.), а не под верстку.
> Логика: генерим (A) 2–3 фулл-скрин «north-star» композиции для атмосферы + (B) отдельные UI-ассеты под 9-slice + (C) фоны-сцены + (D) спрайты. Потом отдаёшь картинки мне — я собираю Flutter из ассетов (9-patch бордеры, `SpriteSheetAnimator`, композиция).
>
> **Правила для всех ассетов (B/C/D):** прозрачный фон (PNG alpha), **без вшитого текста** (текст добавляю во Flutter), один объект по центру кадра, единый пиксельный масштаб во всех генерациях.

---

## STYLE PREFIX — добавляй в начало КАЖДОГО промта

```
Dark fantasy pixel art, mid-resolution (visible clean pixels, no anti-aliasing,
not minimalist 8-bit), mobile game UI asset. Grim but noble medieval fantasy mood.
Palette: near-black backgrounds (#0D0D0F, #1A1A2E), warm gold/amber accents
(#D4A827 primary, #F0C040 bright highlight), off-white text color (#E0DDD5),
aged-bronze borders (#8B7430). Sharp rectangular corners, thin pixel gold borders,
faint stone texture, subtle glow on gold. Consistent pixel scale.
```

---

## Part A — Full-screen «north-star» комп (атмосфера + композиция)

Соотношение: **portrait 9:19.5** (или 1080×2340). Это цельные мокапы экранов — эталон стиля, не режем.

### A1 — Main Map
```
[STYLE PREFIX] Full mobile game screen, portrait. A dark stylized fantasy world map
seen from above (¾ top-down) — dim streets and buildings like aged dark parchment.
Center: a pixel-art hero character marker with a soft glowing circle beneath. Around
him 2–3 pixel monster sprites (goblin, skeleton, wolf) each with a small level badge
and a reddish marker. Top overlay: a player status bar with name, level, a red HP bar
and a blue mana bar, small portrait chip. Bottom: a row of 4 gold pixel navigation
icons (map, bag, character, gear). Mini-compass top-right. Atmospheric, torch-warm glow.
```

### A2 — Combat
```
[STYLE PREFIX] Full mobile game battle screen, portrait. Pixel-art arena background
(dark forest ruins) with ambient dust. Top: a large pixel monster sprite with a red
HP bar above it and name + level. Center: combat VFX — sword-slash arcs, sparks, a
floating yellow crit damage number rising. Bottom: a pixel hero sprite, and a combat
HUD with a red HP bar, an orange rage bar, and a horizontal row of 5 square skill
icon buttons (one darkened on cooldown, one greyed-out). Small flee button in a corner.
```

### A3 — Player Profile
```
[STYLE PREFIX] Full mobile game character profile screen, portrait. Dark sectioned
stone panel. Top: large pixel character bust portrait of an armored warrior, with a
green XP bar. Center: a pixel hero figure surrounded by 6 equipment slots arranged
around the body (head, body, weapon, shield, boots, accessory) — some filled with
gold-bordered item icons, head and accessory slots shown as empty pixel outlines.
Bottom: a two-column stats panel with pixel monospace numbers. Gold accents, thin
ornamental dividers with a small pixel diamond.
```

---

## Part B — UI-ассеты (прозрачный фон, под 9-slice / композицию во Flutter)

Соотношение под объект (квадрат/прямоугольник по смыслу). **Generate on transparent background, no text.**

### B1 — Panel frame (9-slice!)
```
[STYLE PREFIX] A single hollow rectangular UI panel frame, ornate gold pixel border
with small decorative pixel ornaments in the 4 corners, semi-transparent near-black
stone-textured fill in the center. Symmetric border on all sides so it can be stretched
as a 9-slice. Centered, transparent background, no text.
```

### B2 — Primary button (CTA)
```
[STYLE PREFIX] A single rectangular game button, 2–3px gold pixel border, dark-gold to
brighter-gold gradient fill, sharp corners, faint glow. Empty (no text). Transparent
background, centered.
```
Доп. варианты тем же промтом, меняя хвост: `...pressed/inset state, brighter fill` · `...disabled state, grey border and darker fill`.

### B3 — Input field
```
[STYLE PREFIX] A single rectangular text input field, thin 1px gold pixel border,
near-black semi-transparent fill. Empty, no text. Transparent background, centered.
```
Вариант фокуса: `...focused state, bright gold border with faint glow`.

### B4 — Stat bar (HP / Mana / Rage / XP)
```
[STYLE PREFIX] A single horizontal segmented progress bar for a game HUD, thin dark
pixel frame, [COLOR] segmented fill, ~70% filled. Transparent background, no text.
```
Подставляй `[COLOR]`: HP → `dark red #8B2020` · Mana → `dark blue #1E3A6E` · Rage → `dark orange #A04010` · XP → `muted green #2E6B30`.

### B5 — Inventory slot + rarity borders
```
[STYLE PREFIX] A single empty square inventory slot cell with a pixel border and a
dark recessed inner fill. Transparent background, centered, no item, no text.
```
5 рамок редкости (один промт, 5 прогонов меняя цвет): `square item-slot frame with a [RARITY] glowing pixel border` → Common `grey #606060` · Uncommon `green #3FA04A` · Rare `blue #3F6BA0` · Epic `purple #6B3FA0` · Legendary `gold #D4A827`.

### B6 — Navigation icons (по одной)
```
[STYLE PREFIX] A single gold pixel-art UI icon of a [SUBJECT], simple and readable at
small size, centered on transparent background, no text.
```
`[SUBJECT]`: folded map · leather pouch/bag · helmeted character bust · gear/cog · compass.

### B7 — Skill icons (по одной, под combat HUD)
```
[STYLE PREFIX] A single square pixel-art skill icon depicting [SKILL], vivid magical
glow, inside a thin gold frame. Transparent background, centered, no text.
```
`[SKILL]`: sword slash · fireball · frost nova · heal (green sparkles) · shield bash · whirlwind.

### B8 — Divider
```
[STYLE PREFIX] A thin horizontal gold pixel divider line with a small pixel diamond
centered. Transparent background, no text.
```

---

## Part C — Фоны / сцены (фулл-скрин, можно с лёгким параллакс-расслоением)

Portrait 9:19.5, можно непрозрачный фон.

### C1 — Login background
```
[STYLE PREFIX] Full-screen vertical background scene: dark fantasy stone ruins with a
dark forest and mountains on the horizon at dusk, floating embers and fireflies, a
faint dark heroic warrior silhouette with gold weapon highlights. Empty center-bottom
area for a login form. Atmospheric, moody.
```

### C2 — Character Select hall
```
[STYLE PREFIX] Full-screen vertical background: a dark stone castle hall lit by wall
torches with flickering flame glow, empty vertical space for a list of character cards.
```

### C3 — Battle arenas (набор)
```
[STYLE PREFIX] Full-screen vertical pixel-art battle arena background, [LOCATION],
atmospheric ambient particles, no characters.
```
`[LOCATION]`: dark forest clearing · crumbling stone ruins · underground cave · ashen ridge.

---

## Part D — Спрайты (под анимацию / маркеры; sprite-sheet если нужен)

Прозрачный фон. Для анимации проси **horizontal sprite sheet, N frames, evenly spaced, consistent canvas**.

### D1 — Hero classes
```
[STYLE PREFIX] Full-body pixel-art character sprite of a [CLASS], side/¾ view, idle
pose, transparent background, centered.
```
`[CLASS]`: Warrior — broad-shouldered, dark steel armor with gold rivets, sword + shield, steel/dark-red/gold palette · Mage — slim, dark blue/purple runed robe, glowing-crystal staff, blue magical glow.

### D2 — Map marker (top-down)
```
[STYLE PREFIX] Top-down (¾) pixel-art hero character marker for a map, idle, small,
readable from above, transparent background.
```

### D3 — Monsters
```
[STYLE PREFIX] Pixel-art monster sprite of a [MONSTER], side/¾ view, idle pose,
transparent background, centered, sized [TIER].
```
`[MONSTER]` / `[TIER]` (из сида): Slime, Forest Rat, Wild Boar (small) · Goblin Scout, Goblin Warrior, Dire Wolf (medium) · Orc Raider, Stone Golem, Necromancer Acolyte (large) · Drake Whelp (elite, big, unique glow).

### D4 — Animation sheets (опц.)
```
[STYLE PREFIX] Horizontal sprite sheet of a [CLASS], [ACTION] animation, [N] frames
evenly spaced on one row, consistent frame size, transparent background.
```
`[ACTION]` / `[N]`: idle/4 · attack/6 · skill cast/8 · hit/3 · death/6 · walk (4 directions)/6.

---

## Tips / порядок
- Начни с **Part A (3 компа)** — увидишь, бьётся ли стиль с ожиданием, и только потом дробишь на ассеты.
- Для ассетов критично: **прозрачный фон + без текста + ровные симметричные бордеры** (иначе 9-slice поедет).
- Один объект на кадр — не проси «сетку из 5 кнопок», проси кнопку; варианты делай отдельными прогонами с одним и тем же STYLE PREFIX (это держит стиль консистентным).
- Когда наберёшь пачку — кидай мне папку (напр. `troy-flutter/assets/ui/`, `assets/sprites/`), я разрежу/настрою 9-patch и соберу экраны во Flutter.
- Реальные поля данных для экранов (что именно выводим) — в `troy-docs/design/redesign-prompt.md`, дублировать в картинку их не нужно (текст не вшиваем).
```
