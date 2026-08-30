# Asset Pipeline — конвейер генерации картинок и спрайтов

Roadmap по настройке воспроизводимого конвейера: промт → пиксель-арт → спрайт-лист →
S3 → JSON в БД. Цель — чтобы новый класс/моб/предмет получал полный визуал за
минуты скриптом, а не за вечер руками.

Связанные документы: [content-generation.md](../../game-design/content-generation.md)
(секции 5–6 — промты и текущий ручной пайплайн), [pixel-art-design.md](../../game-design/pixel-art-design.md)
(палитра, арт-дирекшн), [monster-visuals-prompt.md](./monster-visuals-prompt.md).

---

## Зафиксированные решения

- **Инструменты.** Основной — **Retro Diffusion API** (честная пиксель-сетка, альфа
  через `remove_bg`, палитра через `input_palette`, референсы для консистентности,
  анимации по стартовому кадру, MCP для Claude Code). Вторичный — **Nano Banana 2**
  (`gemini-3.1-flash-image`, прямой Gemini API) для hi-res: фоны арен, экраны
  логина, концепты. OpenRouter / LM Studio / локальная диффузия — не используем
  (анализ в чате 2026-08-29: OpenRouter не дешевле и без pixel-специфики, LM Studio
  картинки не генерит, Draw Things + LoRA — часы настройки без API).
- **Стиль.** Переход с hi-res «псевдо-пикселей» (текущие `war1`/`mage1`, кадры
  784×448) на **нативный пиксель + целочисленный апскейл**. Это то, что описано в
  `pixel-art-design.md` («visible clean pixels, no anti-aliasing»). Старые ассеты
  перегенерируются, чтобы в игре не было двух стилей.
- **Один источник правды на ассет — манифест** (`assets/<type>/<code>.yaml`):
  промт, style id, seed, размер, референсы, пути к выходам, URL в S3. Ассет без
  манифеста не считается сделанным — его нельзя воспроизвести.
- **Клиент уже готов к пикселям**: батл рендерит спрайты с `FilterQuality.none`
  (`battle_page.dart`), формат листа `ClassSpriteSheet { url, columns, rows,
  frameCount, fps, skipFrames? }` не меняем.
- **Бюджет.** Всё prepaid, без подписок. Ориентир на полный MVP-контент (5 классов,
  10 мобов, ~50 иконок) — **$40–60** на RD + **<$10** на Nano Banana. Перед каждой
  пачкой — `check_cost: true` (бесплатный dry-run).

## Где живёт

Новый сиблинг `troy/troy-assets/` (отдельный git-репо, как admin/):

```
troy-assets/
├── palette/troy-dark-gold.png     # палитра из pixel-art-design.md для input_palette
├── styles/                        # промт-префиксы и style id по типам ассетов
├── assets/
│   ├── classes/<code>.yaml        # манифесты
│   ├── monsters/<code>.yaml
│   └── items/<code>.yaml
├── out/                           # сгенерённое (png native, sheets, webp) — в git
└── tools/                         # CLI (Node/TS — стек как у бэкенда)
    ├── gen.ts        # icon | keyframe | anim | scene   → out/
    ├── pack.ts       # кадры → спрайт-лист по сетке контракта → lossless webp
    └── publish.ts    # upload в admin API + PATCH JSON спрайта в сущность
```

`out/` коммитим: png небольшие (нативные 64–256px), а воспроизводимость важнее
чистоты репо.

---

## Статус

Подробно по шагам — [steps.md](./steps.md), грабли — [pitfalls.md](./pitfalls.md), выполненный промт по визуалу мобов — [monster-visuals-prompt.md](./monster-visuals-prompt.md).

- [x] **Шаг 0** — проба стиля warrior; итоги в `troy-assets/styles/README.md`
- [x] **Шаг 1** — инструментарий: `styles/class.yaml` (референс промтов с плейсхолдерами), манифест `assets/classes/<code>.yaml`, `tools/gen.mjs` (state, бюджет, dry-run) + `tools/publish.mjs`
- [~] **Шаг 2** — классы: `knight` полностью перегенерирован по замечаниям 30.08 (иконка 512, walk сверху, attackIdle без взмахов, attack замах→удар, спокойный idle, 2 скилла с иконкой+кастом) и залит в dev; ждёт проверки на устройстве, дальше — остальные классы по тому же манифесту
- [ ] **Шаг 3** — мобы: иконка карты → idle/attack → скиллы
- [ ] **Шаг 4** — предметы и оружие: иконки инвентаря
- [ ] **Шаг 5** — hi-res: арены, фоны экранов, портреты (Nano Banana 2)
- [ ] **Шаг 6** — замена старых ассетов, QA на устройстве, документация

