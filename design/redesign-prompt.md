# Troy — Redesign Prompt (Claude Design / Figma Make)

> Готовый промт для редизайна мобильного Flutter-клиента Troy.
> Скармливай **целиком** для единой дизайн-системы, либо по одной секции `### Screen` за раз.
> Источники: `game-design/pixel-art-design.md` (визуал), `troy-flutter/CLAUDE.md` (API-контракты, реальные поля), `game-design/stats-and-formulas.md` (статы).

---

## MASTER PROMPT — paste this block first

You are designing a high-fidelity mobile UI for **Troy**, a geolocation RPG (think Pokémon GO meets a dark-fantasy turn-based RPG). Players walk in the real world, encounter monsters on a map, fight them in turn-based combat, collect loot, equip gear, and level up.

**Platform & format**
- Mobile, **portrait only**, target iPhone 15 / Pixel 8 (≈390×844 logical px). Design at 1x logical, respect safe areas (notch + home indicator).
- Implementation target is **Flutter** — use flat layers, no OS-specific chrome, components must be buildable as Flutter widgets.
- All UI copy is **English**, Latin script only.

**Art direction — Dark Fantasy Pixel Art**
- Mid-resolution pixel art: visible pixels but readable on mobile (not minimalist 8-bit, not hi-res). No anti-aliasing on pixel-art elements — clean hard pixels.
- Mood: grim but noble fantasy. Dark stone/ruins backdrops, warm gold/amber accents add heroism. Atmospheric, never depressing.
- **Sharp corners** on pixel-art framed elements (buttons, cards, panels) — no soft rounded corners on the game chrome. Subtle 2–3px pixel borders in aged-bronze/gold.
- Decorative touches: thin gold border lines, optional pixel ornaments in panel corners, divider lines with a small pixel diamond/dot centered.

**Design tokens — colors**
| Role | HEX |
|---|---|
| Background (primary) | `#0D0D0F` |
| Background (secondary, blue-tinted) | `#1A1A2E` |
| Accent (primary gold) | `#D4A827` |
| Accent (bright gold, highlight) | `#F0C040` |
| Text (primary, off-white) | `#E0DDD5` |
| Text (secondary, muted) | `#8A8578` |
| Border / aged bronze | `#8B7430` |
| Input field bg | `#0F0F15` @ ~80% opacity |
| HP bar | `#8B2020` |
| Mana bar | `#1E3A6E` |
| Rage bar | `#A04010` |
| XP bar | `#2E6B30` |
| Rarity — Common / grey | `#606060` |
| Rarity — Uncommon / green | `#3FA04A` |
| Rarity — Rare / blue | `#3F6BA0` |
| Rarity — Epic / purple | `#6B3FA0` |
| Rarity — Legendary / gold | `#D4A827` |
| Damage text (normal) | `#FF4030` |
| Crit damage text | `#FFD700` |

**Typography**
- Game title / big headers: pixel medieval-serif, gold with faint glow/shadow, angular pixel serifs ("carved in stone" look).
- UI text (buttons, labels): clean pixel sans-serif, high contrast on dark bg.
- Numbers (damage, stats): **monospace pixel** font so digits don't jump on value change.

**Component primitives**
- **Primary button (CTA):** rectangular, 2–3px gold pixel border, dark-gold→lighter gold gradient fill, light text, sharp corners. Pressed = brighter fill + 1–2px inset/“pushed” offset. Disabled = grey border/text, darker fill.
- **Secondary button:** thin gold border, transparent/semi-transparent fill, gold text.
- **Input:** rectangular, 1px gold pixel border, near-black semi-transparent fill, muted-grey placeholder. Focus = bright-gold border + faint glow.
- **Card (character/item):** dark semi-transparent fill, pixel border, top→bottom subtle gradient. **Active/selected = bright gold border**, inactive = muted bronze border.
- **Panel/container:** semi-transparent black with faint stone-texture noise, thin gold borders.
- **Stat bars:** segmented pixel fill, colored per resource (HP/Mana/Rage/XP above), thin dark frame, optional numeric label overlaid in mono.

**Constraints**
- Every tappable target ≥ 44×44 logical px.
- Don't over-decorate: dark field, thin frames, minimal chrome outside content.
- Maintain one consistent pixel resolution across all elements (no mixing pixel scales).

For each screen below, design a polished, production-ready frame. Use realistic placeholder data exactly as specified (these are the real backend fields). Show realistic states (loading skeleton + empty/error noted where relevant).

---

### Screen 1 — Main Map (primary hub) ⭐

The home screen. A real-world map with a dark pixel-art overlay.

**Map canvas**
- OpenStreetMap-style streets/buildings, but darkened and stylized like aged parchment / dark stone. Streets faintly visible.
- **Player marker (center):** pixel hero sprite (¾ top-down), animated idle, soft glowing circle beneath.
- **Monster markers:** pixel monster sprites that appear within view radius. Each shows a small **level badge** and a reddish marker / skull icon for aggressive ones. Subtle "breathing" bounce.
- Mini-compass top-right corner.

**Top HUD overlay (player status bar)**
- Character name + level.
- **HP bar** (red `#8B2020`).
- Class resource bar: **Mana** (blue) for Mage / **Rage** (orange) for Warrior.
- Small avatar/portrait chip.

**Monster tap → bottom sheet** (design this state too)
- Monster sprite, name, **level**, and stats: `hp`, `atk`, `def`, `expReward` (XP), `goldReward` (gold), distance to player (e.g. "42 m away").
- Primary CTA **"FIGHT"** (enabled only when within 100 m — show a disabled state "Get closer — 100 m" when too far).

**Bottom navigation bar:** 4 pixel-icon tabs — **Map** (active), **Inventory**, **Profile**, **Settings**.

Use sample monsters: "Goblin" lvl 3 (hp 50, atk 8, def 3, +25 XP, +10 gold); "Skeleton" lvl 5; "Dire Wolf" lvl 7.

---

### Screen 2 — Combat / Battle ⭐

Turn-based fight, fullscreen. Pixel arena background (forest/ruins/cave) with subtle ambient animation (drifting dust/leaves).

**Layout (top → bottom)**
- **Top:** monster — large pixel sprite, **HP bar above it**, name + level (e.g. "Goblin — Lvl 3").
- **Center:** animation zone — pixel hit flashes, skill sparks, **floating damage numbers** (white normal, **yellow crit**, red incoming) that rise & fade.
- **Bottom:** player hero pixel sprite.

**Combat HUD (bottom quarter)**
- Player **HP bar** (red) + resource bar (**Mana** blue / **Rage** orange) with mono numeric labels.
- **Skill bar:** horizontal row of 4–6 square skill buttons, each a pixel skill icon in a frame. States: available (bright, highlighted), cooldown (darkened + countdown number overlay), insufficient resource (greyed/inactive).
- Small **flee** button (running-figure icon) in a corner.

**Also design two result overlays:**
- **VICTORY:** screen dims, central gold glow, "VICTORY" in glowing gold pixel letters. Rewards: `+25 XP` with a progress bar, loot icons (show a Rare blue-bordered item drop). CTA **"Continue"**.
- **DEFEAT:** screen dims with red tint, "DEFEATED" red pixel letters, `-5% XP`, incapacitated timer. CTA **"Return to Map"**.
- (Optional) **LEVEL UP** flash overlay: gold burst, "LEVEL UP!", new level + "+2 attribute points".

---

### Screen 3 — Player Profile ⭐

Dark sectioned panel.

**Top:** large pixel character portrait (bust), nickname, class, **level**, and an **XP bar** (green `#2E6B30`) toward next level.

**Center — Equipment:** pixel hero figure with equipment slots arranged around it. The character can wear **at most 6 items — exactly one per slot** (no duplicate slots, no extra accessory/ring slots). Always render all 6 slots:

| # | Slot | Max equipped |
|---|---|---|
| 1 | HEAD | 1 |
| 2 | BODY | 1 |
| 3 | WEAPON | 1 |
| 4 | SHIELD | 1 |
| 5 | BOOTS | 1 |
| 6 | ACCESSORY | 1 |

Empty slots = pixel outline (HEAD and ACCESSORY have no item content yet — show them empty). Filled slots = item icon with a rarity-colored border. Tapping a filled slot can unequip.

**Bottom — Stats (two columns):**
- Attributes: **STR, INT, STA, AGI, SPI** with values.
- Derived: **HP / MaxHP, Mana or Rage, Armor, Magic Resist, Phys Attack, Magic Attack, Attack Speed, Crit %**.
- If unspent attribute points exist, show a **"+"** button next to allocatable attributes and a "2 points to spend" banner.

Sample: nickname "Aldric", class Warrior, level 7, 1340/2000 XP. STR 18, STA 22, AGI 9, INT 5, SPI 6. HP 280/280, Rage 0/100, Armor 64, Phys ATK 46.

---

### Screen 4 — Inventory ⭐

**Item grid:** classic pixel-art icon grid, 4–5 columns, each cell a pixel-framed slot. **Rarity-colored borders**: grey (Common), green (Uncommon), blue (Rare), purple (Epic), gold (Legendary). Equipped items get a small "E" / gold checkmark corner badge.

**Item tap → tooltip panel** (design this): dark popup with item name (colored by rarity), type, stat bonuses (`atkBonus`, `defBonus`, `hpBonus`), short flavor description, and **"Equip" / "Unequip"** button.

Group or tab by slot type (Weapon / Armor / Accessory / Consumable). Show an empty-state ("Your bag is empty — go hunt") variant.

Sample items: "Iron Sword" (Weapon, Common, +5 ATK), "Forest Cloak" (Body, Uncommon, +3 DEF +10 HP, equipped), "Ember Ring" (Accessory, Rare, +4 ATK +2 crit).

---

### Screen 5 — Character Selection (entry)

Background: dark stone hall with torches, faint flame flicker.

- **Vertical scroll list of character cards.** Each card: pixel idle sprite + **name + class + level**. The **active character** has a bright gold border; others muted. Tapping a non-active card selects it (show a per-card spinner during select — never a fullscreen loader); active card is not tappable.
- **"Create Character"** card at the end of the list, styled as a stone slab with a "+" symbol.

Sample: "Aldric" Warrior Lvl 7 (active), "Lysa" Mage Lvl 4.

*(Optional companion: Character Creation — two large full-body class portraits, Warrior (steel/red, sword+shield) vs Mage (blue/purple robe, glowing staff), class description on select, name field styled as a scroll, CTA "Forge Hero".)*

---

### Screen 6 — Login / Auth (entry)

- **Background:** full-screen dark pixel scene — stone ruins / dark forest / mountains on the horizon, with subtle parallax or floating embers/fireflies. Optional dark hero silhouette with gold weapon/armor highlights.
- **Logo:** "TROY" large gold pixel letters with carved-stone texture + faint glow, upper third, thin decorative divider beneath.
- **Form (lower-center, semi-transparent dark panel):**
  - Tabs at top: **LOGIN / REGISTER** (switch in place, no screen change).
  - Email field (envelope icon), Password field (lock icon).
  - Primary CTA **"ENTER REALM"**.
  - Secondary link: "New adventurer? Sign up".
- Note: registration is a 3-step email-code flow — also sketch a **6-digit code entry** state (6 pixel-framed digit boxes, "Verify" CTA, resend timer).

---

## Notes for whoever runs this
- Палитра взята из `pixel-art-design.md` (aspirational dark-gold), а не из текущего `realm_walker_theme.dart` (он сейчас нейтрально-тёмный) — редизайн целится в dark-fantasy визуал.
- Данные в каждой секции — реальные поля API из `troy-flutter/CLAUDE.md`, не выдуманные. При генерации можно подставлять другие значения, но имена полей сохраняем.
- Если Claude design тянет лучше по одному экрану — гони секции по очереди, мастер-блок добавляй первым каждый раз для консистентной дизайн-системы.
