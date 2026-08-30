# Asset pipeline · грабли

Часть [assets/README.md](./README.md).

## Собраны из доков RD и нашего бэкенда

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
