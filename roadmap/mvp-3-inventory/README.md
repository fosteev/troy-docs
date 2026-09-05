# MVP-3 — Profile, Inventory, Equipment

> **Статус: в работе.** Клиент: Hero-экран (профиль + кукла + мешок одним скроллом) на реальном API, тесты зелёные. Бэкенд: профиль, инвентарь, equip/unequip, очки атрибутов — есть; открыты [backend-gaps.md](./backend-gaps.md) #1 и #3; #2 (зелья), #4 (class restrictions) и #5 (стак) решены 05.09 и вынесены в [items/](../items/README.md). Следующий шаг — гэпы бэкенда и визуальный отклик на смену статов (промт внизу), затем [redesign.md](./redesign.md).

Цель: игрок должен видеть прогресс персонажа и усиливать его через предметы.

## Продуктовый результат

После боев игрок получает предметы, открывает инвентарь, экипирует предмет и видит изменение характеристик.

## Backend

- [x] Endpoint профиля активного персонажа.
- [x] Endpoint инвентаря.
- [x] Equip/unequip endpoint.
- [x] Проверка слотов экипировки.
- Class restrictions — решено 05.09, реализация в теме [items/](../items/README.md) (SCRUM-17).
- [x] Computed stats должны учитывать:
  - [x] base stats;
  - [x] level growth;
  - [x] free attribute points;
  - [x] equipment bonuses.

## Flutter

- [x] Экран профиля персонажа:
  - [x] имя;
  - [x] класс;
  - [x] уровень;
  - [x] XP progress;
  - [x] основные статы;
  - [x] computed stats.
- [x] Экран инвентаря:
  - [x] список предметов;
  - [x] rarity;
  - [x] slot;
  - [x] equipped state.
- [x] Экран экипировки:
  - [x] текущие слоты;
  - [x] equip/unequip action;
  - [ ] визуальная обратная связь после изменения статов.

## Связанные документы

- [backend-gaps.md](./backend-gaps.md) — чего не хватает от бэкенда
- [redesign.md](./redesign.md) — мешок отдельным экраном (следующий шаг)
- [database-schema.md](../../technical/database-schema.md)
- [stats-and-formulas.md](../../game-design/stats-and-formulas.md)
- [leveling.md](../../game-design/leveling.md)

## Definition of Done

- [x] Полученный в бою предмет появляется в инвентаре.
- [x] Предмет можно экипировать и снять.
- [x] Экипировка меняет computed stats.
- [x] UI не требует restart для отображения изменений.

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила (архитектура, тесты, делегирование) — в [roadmap/README.md](../README.md). Редизайн мешка — отдельная сессия по промту в [redesign.md](./redesign.md).

```
Работаем в /Users/fost/Projects/troy (backend troy-backend + клиент troy-flutter + админка troy-admin).

Задача: закрыть бэкенд-гэпы MVP-3 и визуальный отклик на смену статов. Профиль,
инвентарь и equip/unequip уже работают на реальном API — это доработка, а не
стройка с нуля.

Прочитай:
- troy-docs/roadmap/mvp-3-inventory/README.md (статус и чек-листы) и
  backend-gaps.md (аудит, гэпы #1–#6);
- troy-docs/technical/database-schema.md, troy-docs/game-design/stats-and-formulas.md;
- troy/CLAUDE.md (backend), раздел "Architecture rules" в troy-flutter/CLAUDE.md
  (эталон — фича auth).

Порядок:
1. Решения по гэпам #2, #4, #5 уже приняты (05.09) и записаны в
   troy-docs/roadmap/items/README.md — не переспрашивать: зелья и class
   restrictions делаются в теме items (SCRUM-19, SCRUM-17), стак экипировки —
   «quantity = копии, isEquipped = одна надета», без миграции. Открыт только
   гэп #6 (иконки: глифы по type/slot или iconUrl) — спросить одним вопросом.
2. Гэп #1 — Item.description: колонка + миграция (накатывать `migrate deploy`,
   НЕ `migrate dev` — дропнет active_spawns), seed, отдача в /inventory и
   /character/me, поле в форме предмета в админке, показ в item-sheet клиента.
3. Гэп #3 — выбросить предмет: DELETE /inventory/:itemId (?quantity=), контракт +
   NATS-паттерн; кнопка в UI появляется только вместе с эндпоинтом.
4. Гэпы #2 и #4 — вне MVP-3 (тема items, SCRUM-19 / SCRUM-17), здесь не трогать.
5. Flutter: визуальная обратная связь после equip/unequip — тост с дифом
   computedStats («PHYS ATK +7»), решение зафиксировано в redesign.md.

Тесты — часть DoD: backend unit на тронутые пути (discard,
пересчёт computed stats), Flutter — repository_impl + bloc + маппер по эталону auth.

Проверка: `npx nx run-many -t test` в troy-backend; `flutter analyze && flutter test`
в troy-flutter; `npx tsc -b --noEmit` в troy-admin, если её трогали.

Ветка main, коммиты без подписей ассистента. По завершении: отметить закрытые
пункты здесь и в backend-gaps.md, обновить баннер статуса фазы и таблицу в
troy-docs/roadmap/README.md.
```
