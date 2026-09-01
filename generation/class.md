# Генерация нового класса — от идеи до игры

Полный порядок. Эталон прохождения: `warrior` (арт как dev-класс `knight`) и `mage` — по их
карточкам и манифестам можно сверять каждый шаг. Один класс ≈ **$2.5** кредитов Retro Diffusion
и ~час работы с проверками глазами.

## Что понадобится

- **RD-ключ**: `source ~/.config/troy/rd.env` (кладёт `RD_API_KEY`; баланс: `curl -s -H "X-RD-Token: $RD_API_KEY" https://api.retrodiffusion.ai/v1/inferences/credits`).
- **Backend поднят** (api-gateway :3000 + game-core + NATS) и креды админки: `ADMIN_EMAIL` / `ADMIN_PASSWORD` (dev: `admin@troy.dev` / `12345`).
- Репо `troy-assets` (инструменты) и `troy-docs` (карточки).

## Шаг 1. Карточка класса (дизайн)

`troy-docs/classes/_template.md` → скопировать в `classes/<code>.md`, заполнить все `{…}`.
Правила и бюджеты — в самом шаблоне (старт статов Σ22, рост Σ6.5, кап 10, 4 скилла на слоты 1/3/6/10,
бюджеты CD/cost/base по слотам). Таблицу статов 1–10 считает python-сниппет в конце шаблона — не руками.

Обязательные тексты (позже уедут в БД, пока RU; EN — этап локализации в MVP-5):
- описание класса → `CharacterClass.description` (экран выбора, ≤ 220 символов);
- описание каждого скилла → `ClassSkill.description` (тултип, ≤ 500, 1–2 предложения с числом эффекта).

Карточка — источник правды: числа меняются сначала в ней, потом в seed/манифесте, не наоборот.

## Шаг 2. Манифест для генерации

`troy-assets/assets/classes/<code>.yaml` — переносится из карточки (раздел «Поля манифеста»).
Пример со всеми полями — `mage.yaml`. Содержит **только описание** (внешность/движения/скиллы);
промты собирает шаблон `troy-assets/styles/class.yaml` — его не трогать (единый вид игры).

Ключевые поля: `code`, `name`, `cloneFrom` (донор статов, напр. `warrior`) или `stats`, `subject`
(внешность + цветовая схема, без ракурса/фона/слов «pixel art»), `emblem`, `portrait`, `weaponRest`,
`weaponCarry`, `topdownDetail`, `attackMotion`; на каждый скилл: `description`, `db:` (все поля
`ClassSkill` — по нему publish создаст скилл в БД), `icon`, `cast`.

Если классу нужны цвета, которых нет в палитре (проверить `troy-assets/palette/troy-dark-gold.png`,
29 цветов) — добавить в `tools/palette.mjs` и перегенерить (`node tools/palette.mjs`), как делали
navy/cyan под мага.

## Шаг 3. Генерация (по шагам, с проверкой глазами)

```bash
cd troy-assets && source ~/.config/troy/rd.env
node tools/gen.mjs assets/classes/<code>.yaml --dry          # план и цена (~$2.5), бесплатно
# 1) фронт + иконка + портрет (~$0.25) → смотреть out/<code>/
node tools/gen.mjs assets/classes/<code>.yaml keyframeFront icon portrait
# 2) профиль вправо (из фронта) и вид сверху (~$0.36) → смотреть
node tools/gen.mjs assets/classes/<code>.yaml keyframeSide keyframeTop
# 3) анимации и скиллы (~$1.9)
node tools/gen.mjs assets/classes/<code>.yaml anim:idle anim:attackIdle anim:attack anim:walk \
    skill:<code1> skill:<code2> skill:<code3> skill:<code4>
```

- Состояние — `assets/classes/<code>.state.json`: файлы, финальные промты, seed, task id, цены.
  Переделать одну цель — добавить её с `--force`; другой вариант — `--seed=N`.
- Бюджет-предохранитель: `--budget=<$>` (по умолчанию 2).
- Просмотр: файлы в `out/<code>/`; листы — сеткой 4×2 (8 кадров) / 3×2 (6), кадр = холст.

### Приёмка (из ревью 30.08 — проверять каждую)

| Ассет | Критерий |
|---|---|
| keyframeFront | вся фигура с ногами, поля до края, палитра держится |
| keyframeSide | профиль/3-4 **вправо**, то же снаряжение и цвета, спокойная стойка |
| keyframeTop + walk | **строго на север, от зрителя**: видны затылок/спина, лица не видно; ноги шагают |
| idle | дыхание едва заметное, оружие неподвижно |
| attackIdle | стоит в стойке, оружием НЕ машет |
| attack | явный замах → удар с проносом (у кастера: жест → выброс), не «туда-сюда» |
| иконка класса | эмблема читается на 32 px, итог 512 (128 ×4) |
| иконки скиллов | предмет + один цветовой акцент, читается на 32 px |
| касты скиллов | уникальная анимация по `cast`, возврат в стойку |

## Шаг 4. Заливка в БД

```bash
ADMIN_API_URL=http://localhost:3000 ADMIN_EMAIL=… ADMIN_PASSWORD=… \
  node tools/publish.mjs assets/classes/<code>.yaml
```

Publish: создаёт/обновляет класс по `code` (статы — из `cloneFrom`/`stats`, описание класса — из
манифеста при создании), заливает иконку 512 и 4 листа в S3 (dev: MinIO), создаёт **недостающие
скиллы из `db:`-блоков** с иконкой/кастом/описанием, у существующих обновляет только визуал и
`description` (числа существующих правятся в админке). Идемпотентен: повторный запуск дозальёт
только изменившееся (кэш по хэшу файла).

Параллельно: те же 4 скилла добавить в `troy-backend/prisma/seed.ts` (свежая БД должна
воспроизводиться); **на dev seed не гонять** — он чистит kills/inventory.

## Шаг 5. Финализация

1. Скопировать итоговые промты из `<code>.state.json` в карточку (раздел 7) — дамп-однострочник
   есть в `classes/warrior.md`.
2. Проверка на устройстве: выбор персонажа (иконка, описание), карта (маркер walk, направление),
   бой (стойка/атака/касты, тултипы скиллов).
3. `isActive: true` (в админке или манифесте + publish).
4. Коммиты: `troy-docs` (карточка), `troy-assets` (манифест + state + `out/<code>/`),
   `troy-backend` (seed).

## Грабли (уже собраны кровью)

- В промты **нельзя** писать «pixel art» и «transparent» (стиль задаёт `prompt_style`, прозрачность — `remove_bg`); фон всегда «on a plain white background».
- «facing up» модель рисует **лицом к зрителю** — для вида сверху формулировка только «walks AWAY from the viewer… the face is NOT visible».
- `reference_images` держит стиль, но **не поворачивает** персонажа; поворот вправо — `rd_pro__edit` c фронтом как `input_image`; вид сверху — `rd_pro__topdown` текстом + фронт как reference (edit для top не работает).
- Синие цвета палитры могут «утащить» сталь — чинится `tools/fix-top.mjs` (перекраска + чистый даунскейл).
- Node fetch с keep-alive рвёт соединение на больших телах — уже починено в `tools/rd.mjs` (`Connection: close`); если увидел `ECONNRESET` в новом скрипте — ходи через `rd.mjs`.
- Полный список — `troy-assets/styles/README.md` и `roadmap/assets/pitfalls.md`.
