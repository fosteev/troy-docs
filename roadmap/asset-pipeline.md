# Asset Pipeline — конвейер генерации картинок и спрайтов

Roadmap по настройке воспроизводимого конвейера: промт → пиксель-арт → спрайт-лист →
S3 → JSON в БД. Цель — чтобы новый класс/моб/предмет получал полный визуал за
минуты скриптом, а не за вечер руками.

Связанные документы: [content-generation.md](../game-design/content-generation.md)
(секции 5–6 — промты и текущий ручной пайплайн), [pixel-art-design.md](../game-design/pixel-art-design.md)
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

- [x] **Шаг 0** — проба стиля warrior; итоги в `troy-assets/styles/README.md`
- [x] **Шаг 1** — инструментарий: `styles/class.yaml` (референс промтов с плейсхолдерами), манифест `assets/classes/<code>.yaml`, `tools/gen.mjs` (state, бюджет, dry-run) + `tools/publish.mjs`
- [~] **Шаг 2** — классы: `knight` полностью перегенерирован по замечаниям 30.08 (иконка 512, walk сверху, attackIdle без взмахов, attack замах→удар, спокойный idle, 2 скилла с иконкой+кастом) и залит в dev; ждёт проверки на устройстве, дальше — остальные классы по тому же манифесту
- [ ] **Шаг 3** — мобы: иконка карты → idle/attack → скиллы
- [ ] **Шаг 4** — предметы и оружие: иконки инвентаря
- [ ] **Шаг 5** — hi-res: арены, фоны экранов, портреты (Nano Banana 2)
- [ ] **Шаг 6** — замена старых ассетов, QA на устройстве, документация

---

## Шаг 0 — ключи и проба стиля (гейт)

**Цель:** за $2–3 понять, в каком нативном размере и стиле спрайты выглядят
правильно на телефоне, и зафиксировать параметры до массовой генерации.

1. Завести ключ Retro Diffusion (`retrodiffusion.ai/app/devtools`), пополнить **$10** —
   хватит на Шаги 0–1 и 1–2 класса (Шаг 0 ≈ $2); остальное докидывать после гейта.
   Подключить их MCP в Claude Code (`https://mcp.retrodiffusion.ai/mcp`, Bearer key) —
   дальше всё до Шага 1 можно делать прямо из сессии.
2. Завести Gemini API key (AI Studio) — понадобится только в Шаге 5, но сразу.
3. Сгенерить воина (описание из `character-generation-prompt.md`, **без слов
   «pixel art» в промте** — стиль задаёт `prompt_style`):
   - `rd_pro__fantasy` в **64, 96, 128 px**, `remove_bg: true`, фон в промте
     «on a plain white background», `input_palette` = наша палитра, seed фикс;
   - `rd_pro__default` те же размеры — сравнить, какой стиль ближе к
     Octopath/Darkest Dungeon;
   - иконку класса `rd_plus__skill_icon` 64px и портрет `portrait:rd_flux` 96px (id из `GET /v1/styles/selector`).
4. Один кадр прогнать через `rd_advanced_animation__idle` (frames 8) и
   `rd_advanced_animation__attack` (frames 6) — проверить, что анимация не
   разваливает персонажа.
5. Собрать лист (пока руками/ImageMagick), залить через админку, посмотреть в батле
   и на карте **на устройстве** рядом с текущим `war1`.

**Решения на выходе (записать в `troy-assets/styles/README.md`):**
- нативный размер персонажа (ожидаю 96 или 128 для батла; карта — тот же лист,
  клиент масштабирует) и мобов/боссов (боссы ×1.5–2);
- `upscale_output_factor` для хранения (native ×1 и масштаб на клиенте — идеал; если
  клиент завязан на пиксельные размеры листа — хранить ×4 nearest);
- style id для персонажей / мобов / иконок / портретов;
- палитра: строгая (`input_palette`) или только референсом.

**Гейт:** если ни один вариант не выглядит лучше текущего hi-res — стоп, пересмотр
решения «нативный пиксель» до Шага 1.

## Шаг 1 — инструментарий

**Цель:** три команды, которыми делается любой ассет.

- `tools/gen.ts` — обёртка над `POST /v1/inferences` (async для анимаций и батчей,
  retry ×1 при фейле — они авто-рефандятся). Читает манифест, пишет png в `out/`,
  дописывает в манифест `seed`, `balance_cost`, пути. Всегда сначала `check_cost`.
  Подкоманды:
  - `icon <manifest>` — иконка (класс/скилл/моб/предмет);
  - `keyframe <manifest>` — ключевая поза (RD Pro + `reference_images` из манифеста);
  - `anim <manifest> <idle|walk|attack|attackIdle|skill:<code>>` — по ключевому
    кадру: паддинг до квадрата с запасом ≥3px, проверка «native, не апскейл»,
    `return_spritesheet: true`;
  - `scene <manifest>` — Nano Banana 2 (Шаг 5).
- `tools/pack.ts` — кадры → лист по контракту (кадры слева направо, сверху вниз).
  Сетка: 8 кадров → 4×2, 6 → 3×2 (или 4×2 c `frameCount: 6`); пишет
  `{ columns, rows, frameCount, fps }` в манифест. Кодирует **lossless webp с альфой
  сам** — `uploadSprite` кладёт готовый webp как есть, а png может перекодировать в
  lossy q82, что мылит пиксели.
- `tools/publish.ts` — `POST /admin/uploads/sprite|icon` → URL → `PUT
  /admin/classes/:id` (или monsters/items) с JSON спрайта. Идемпотентно: если в
  манифесте уже есть URL и хэш файла не изменился — пропуск.
- Проверки в коде, не глазами: альфа-канал реально есть (vision-модели видят
  композит), размеры листа = columns×frame, `frameCount ≤ columns×rows`.
- Тесты: `pack` (сетка/frameCount/размеры) и парсер манифеста — Jest, как в бэкенде.

**DoD:** воин из Шага 0 проходит `gen keyframe → gen anim idle → pack → publish`
одной цепочкой и отображается в приложении.

## Шаг 2 — классы

Порядок на класс (манифест `assets/classes/<code>.yaml`):

1. **Ключевая поза** — RD Pro, описание из `imagePrompt` LLM-генерации
   (content-generation.md §5), `remove_bg`, палитра. Итерировать seed'ом до
   попадания; **этот png — референс для всего остального по классу.**
2. **Анимации** по ключевому кадру: `idle` (8 кадров), `walk` (8), `attack` (6),
   `attackIdle` (8, промт «combat stance, weapon raised, slight sway»). Это 4 листа
   → `spriteIdle / spriteWalk / spriteAttack / spriteAttackIdle`.
3. **Скиллы** (6 на класс): `spriteAttack` каждого — `rd_advanced_animation__custom_action`
   с описанием каста из `designNote`; иконка — `rd_plus__skill_icon` 64px с
   референсом ключевой позы (чтобы цвета класса совпали).
4. **Иконка класса** (`iconUrl`) — `rd_plus__skill_icon` / эмблема класса 64px.
5. **Портрет** (face icon для экрана выбора) — решается в Шаге 0: RD `portrait`
   96–128px или hi-res из Шага 5.

Консистентность: всегда `reference_images: [keyframe]`, тот же `input_palette`,
описание персонажа копируется дословно из манифеста, меняется только строка позы.

**DoD:** все активные классы с полным набором слотов, старые `war1`/`mage1` из
`troy-flutter/assets` больше не используются в батле (карта/логин — Шаг 6).

## Шаг 3 — мобы

То же, что классы, но короче: `iconUrl` (маркер на карте — 32–48px, один
доминирующий акцентный цвет, читаемый на карте; золото — только вторичный),
`spriteIdle` (8), `spriteAttack` (6), `spriteAttack` на скиллы. Боссы —
`isElite`: размер ×1.5–2 от обычного моба, стиль `rd_pro__horror`/`fantasy` по
описанию.

Пачкой: 10 мобов MVP из seed'а по `content-balance.md`. Сначала все ключевые позы
(один проход ревью «выглядят как одна игра»), потом анимации.

## Шаг 4 — предметы и оружие

- Иконки 32–64px, **по одному предмету на запрос** (не паковать в лист — RD не
  гарантирует размер элемента в сетке). `rd_plus__item_sheet` / `rd_pro__inventory_items`
  — только для вдохновения и вариантов («9 different swords» одним `num_images: 9`).
- **Рамка редкости не рисуется в иконке** — её рисует клиент (цвета из
  pixel-art-design.md). Иконка — только предмет на прозрачном фоне.
- Манифест на предмет: `type/slot`, описание, seed. Для семейств (меч I/II/III) —
  один референс, `strength` img2img 0.4–0.6 для вариаций.

## Шаг 5 — hi-res (Nano Banana 2)

Здесь честный пиксель не нужен, а нужна композиция:
- **арены батла** по зонам (`rd_pro` даёт максимум 256px — мало для полноэкранного
  фона); стиль-префикс «pixel-art background», после — прогон через `pixel_correction`/`k_centroid_downscale` RD
  (бесплатные тулзы) или SpriteCook grid-snap, чтобы фон не спорил со спрайтами;
- фоны экранов логина/регистрации (сейчас `login_background_sprite.webp`);
- портреты, если Шаг 0 показал, что RD-портреты слишком мелкие.

Nano Banana не отдаёт альфу — для этих ассетов она и не нужна (полноэкранные фоны).
Если понадобится вырезка — chroma-key `#00FF00` + белая обводка 2–3px + HSV, но лучше
такие вещи делать в RD.

## Шаг 6 — замена, QA, документация

- Перегенерить `login_knight`, `register_human`, `mage1`, `war1` в новом стиле;
  бандл-ассеты Flutter обновить, S3 — через `publish`.
- Проверка на устройстве: батл, карта (маркер + мобы), выбор персонажа, инвентарь.
  Чек-лист: нет полупрозрачных ореолов на краях, кадры не «плавают» по вертикали,
  палитра совпадает между классами, иконки читаются на 32px.
- `content-generation.md` §6 — заменить ручной пайплайн ссылкой на этот документ и
  команды `gen/pack/publish`; в `troy-assets/README.md` — «как добавить новый
  класс/моба/предмет» на 10 строк.
- Итог по деньгам: суммировать `balance_cost` из манифестов, сравнить с бюджетом.

---

## Грабли (собраны из доков RD и нашего бэкенда)

- В промт RD **никогда** не писать «pixel art» и «transparent background» — первое
  делает стиль, второе — `remove_bg`. Фон в промте указывать всегда и контрастный
  («plain white background»), иначе уезжает в серый и портит вырезку.
- `input_image` для анимаций — **нативного размера** (не апскейл) и равен
  width/height запроса; опаковые пиксели не ближе 3px к краю → сначала паддинг.
- `input_image` для img2img — RGB без альфы; анимации наследуют фон стартового
  кадра (прозрачный → прозрачный GIF/лист).
- `uploadSprite`: png/webp, до 8192×8192 (`MAX_SPRITE_DIMENSION`), снимает сплошной **белый**
  фон; готовый webp кладёт без перекодирования — поэтому шлём lossless webp сами.
- `uploadIcon`: png/jpeg/webp, всегда перекодирует в webp — для пиксельных иконок
  тоже лучше слать webp.
- Анимации в RD падают чаще стиллов: `async: true`, один retry с теми же параметрами.
- `check_cost: true` перед любой пачкой; `GET /v1/status` перед bulk-прогоном.
- Async: POST отвечает `{ status: "accepted", task_id }`, результат — `GET /v1/inferences/tasks/{id}` → `{ status: "succeeded", result: { base64_images, balance_cost } }`; список задач — `GET /v1/inferences/tasks` (спасает, если потерял id). Ретраить по таймауту поллинга нельзя — это дубль и двойная оплата.
- Анимации приходят уже сеткой (8 → 4×2, 6 → 3×2, кадр = размер запроса) — ложатся в `ClassSpriteSheet` без перепаковки.

---

## Промт для запуска Шага 0 (свежая сессия)

```
Работаем в /Users/fost/Projects/troy (multi-root: troy-backend, troy-flutter, admin, troy-docs).
Задача — Шаг 0 из troy-docs/roadmap/asset-pipeline.md: проба стиля для конвейера
пиксель-арта на Retro Diffusion. Это гейт: по итогу пользователь глазами на телефоне
выбирает размер/стиль, массовую генерацию НЕ начинать.

Прочитай перед работой:
- troy-docs/roadmap/asset-pipeline.md целиком (решения, Шаг 0, раздел «Грабли»);
- troy-docs/game-design/content-generation.md §5–6 и character-generation-prompt.md
  (описание воина, negative prompt — в RD он не работает, описываем что хотим);
- troy-docs/game-design/pixel-art-design.md — палитра (hex в таблице);
- troy-backend/libs/shared/contracts/src/lib/contracts.ts → ClassSpriteSheet;
- troy-backend/apps/api-gateway/src/app/storage/storage.service.ts → uploadSprite/uploadIcon;
- справочник RD API: `gh api repos/Retro-Diffusion/api-examples/contents/llms.txt --jq .content | base64 -d`
  (сайт доков может отдавать 403 — бери из репо).

Предусловия — проверь и остановись, если нет:
- RD_API_KEY в окружении (или MCP retrodiffusion подключён в Claude Code);
- баланс RD ≥ $5 (GET /v1/inferences/credits).
Бюджет шага — $3. Перед КАЖДЫМ запросом check_cost: true; веди сумму, при $3 — стоп.

Сделай:
1. Создай сиблинг troy/troy-assets (git init, ветка main) со структурой из roadmap —
   только то, что нужно для пробы: palette/, styles/, assets/classes/, out/probe/, tools/.
2. palette/troy-dark-gold.png — палитра из pixel-art-design.md (фон, акценты, HP/mana/rage,
   редкости), сгенерируй скриптом (sharp/ImageMagick), не руками.
3. Воин по описанию из character-generation-prompt.md, промт БЕЗ слов «pixel art» и
   «transparent», фон в промте «on a plain white background», remove_bg: true,
   input_palette — палитра, seed фиксированный (один на все варианты):
   - rd_pro__fantasy в 64, 96, 128 px;
   - rd_pro__default в 96 px;
   - иконка класса rd_plus__skill_icon 64 px, портрет portrait:rd_flux 96 px.
4. Лучший на твой взгляд кадр (обоснуй) → rd_advanced_animation__idle (frames 8) и
   rd_advanced_animation__attack (frames 6), return_spritesheet: true, async: true,
   один retry при фейле. Стартовый кадр — нативный размер, паддинг до опаковых
   пикселей ≥ 3px от края.
5. Каждый выход проверь кодом, не глазами: альфа-канал есть, размеры совпадают с
   запросом, у листа columns×frameWidth = width.
6. Листы idle/attack собери в контракт ClassSpriteSheet (4 колонки, кадры слева
   направо/сверху вниз) и закодируй в lossless webp с альфой сам (uploadSprite готовый
   webp кладёт как есть, png может перекодировать в lossy). Рядом положи JSON
   { columns, rows, frameCount, fps: 10 } для админки.
7. Манифест assets/classes/warrior.yaml: промты, style id, seed, размеры, стоимость
   каждого запроса, пути к файлам.
8. Заливка: если в env есть ADMIN_API_URL и ADMIN_TOKEN — POST /admin/uploads/sprite и
   /admin/uploads/icon, затем PUT /admin/classes/:id с JSON спрайтов у класса warrior.
   Иначе — не заливай, просто укажи в отчёте, какие файлы куда загрузить через админку.
9. Коммит в troy-assets (main).

Правила: бэкенд/фронт не запускать и не перезапускать — только давать команды.
Молчи между tool-call, текст — только если проблема или смена курса.

Отчёт в конце (коротко): таблица вариантов (стиль × размер × файл × цена), итоговая
сумма, что проверить на устройстве и какие 4 решения из Шага 0 нужно принять
(нативный размер, upscale_output_factor, style id по типам, палитра строгая/референс).
Дальше Шага 0 не идти.
```
