# MVP-3 — Profile, Inventory, Equipment

Цель: игрок должен видеть прогресс персонажа и усиливать его через предметы.

## Продуктовый результат

После боев игрок получает предметы, открывает инвентарь, экипирует предмет и видит изменение характеристик.

## Backend

- Endpoint профиля активного персонажа.
- Endpoint инвентаря.
- Equip/unequip endpoint.
- Проверка слотов экипировки.
- Проверка class restrictions, если они есть у предмета.
- Computed stats должны учитывать:
  - base stats;
  - level growth;
  - free attribute points;
  - equipment bonuses.

## Flutter

- Экран профиля персонажа:
  - имя;
  - класс;
  - уровень;
  - XP progress;
  - основные статы;
  - computed stats.
- Экран инвентаря:
  - список предметов;
  - rarity;
  - slot;
  - equipped state.
- Экран экипировки:
  - текущие слоты;
  - equip/unequip action;
  - визуальная обратная связь после изменения статов.

## Связанные документы

- [database-schema.md](../technical/database-schema.md)
- [stats-and-formulas.md](../game-design/stats-and-formulas.md)
- [leveling.md](../game-design/leveling.md)

## Definition of Done

- Полученный в бою предмет появляется в инвентаре.
- Предмет можно экипировать и снять.
- Экипировка меняет computed stats.
- UI не требует restart для отображения изменений.

## Редизайн (Шаг 4Б)

Первая реализация собрала профиль и мешок в один Hero-экран (`features/profile/`, один скролл, инвентарь в самом низу; `features/inventory/` — пустые заглушки). Аудит того, что есть, и интерактивный прототип нового инвентаря — [design/prototypes/inventory-redesign.html](../design/prototypes/inventory-redesign.html) (открыть в браузере). Промт шага — «Шаг 4Б» в [execution-plan.md](./execution-plan.md).

Что меняется (только Flutter, бэкенд не трогаем):

| Было | Станет |
|---|---|
| Мешок — секция в конце Hero-скролла | Отдельный экран Inventory (BACKPACK в nav bar); Hero — профиль, кукла со спрайтом, статы |
| Золото в футере мешка | Золото в app bar инвентаря |
| Кукла только на Hero | На Inventory — компактная полоса 6 слотов над мешком; тап по слоту подсвечивает подходящие предметы |
| «12 / 40 slots» текстом | Сегментированный бар вместимости, warning при ≥ 90 % |
| Тап по слоту = мгновенный unequip | Slot sheet: что надето, Unequip, «Swap for» — подходящие предметы из мешка, тап = equip |
| Item sheet: чипы бонусов, Equip | Бонусы строками с дельтой против надетого в этот слот; Equip / Unequip |
| После equip — молча новый снапшот | Тост с дифом computedStats («PHYS ATK +7») |
| Ячейка: glyph + количество | + метка слота, NEW (локальный набор «виденных»), ▲ если апгрейд к надетому |
| Фильтры | + сортировка rarity / newest / type |

Зафиксированные решения:

- **Empty state** — пустой мешок это просто dashed-сетка, без текста и CTA.
- **Sell** — нет и не планируется в инвентаре.
- **Discard / Use** — в UI появляются только вместе с эндпоинтами (gaps #2, #3 в [inventory-backend-gaps.md](./inventory-backend-gaps.md)); мёртвые кнопки не шипим.
- **Domain остаётся в `profile`** (`InventoryItem`, `HeroSnapshot`, `HeroCubit`), `features/inventory/` — presentation поверх того же cubit. Один снапшот на оба экрана.
- **Углы** — приложение остаётся на `tokens.radius*`; sharp pixel-рамки из прототипа — отдельный шаг по всей дизайн-системе.
- **Навигация** — HERO четвёртым табом (по прототипу) или действием в app bar инвентаря; решить в шаге и записать здесь.

Статус: не начат.
