# MVP-3 — Profile, Inventory, Equipment

> **Статус: в работе.** Клиент: Hero-экран (профиль + кукла + мешок одним скроллом) на реальном API, тесты зелёные. Бэкенд: профиль, инвентарь, equip/unequip, очки атрибутов — есть; [backend-gaps.md](./backend-gaps.md) #1, #3 и #7 закрыты бэкендом 05.09 (сессия 1, SCRUM-15/16 — тесты и сборка зелёные), клиентская часть — SCRUM-75 (сессия 2); #2 (зелья), #4 (class restrictions) и #5 (стак) решены 05.09 и вынесены в [items/](../items/README.md). План закрытия гэпов и отклика на статы — [description-discard.md](./description-discard.md) (сессия 1 сделана; сессия 2 Flutter — SCRUM-75/49, промт внутри), затем [redesign.md](./redesign.md).

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
- [description-discard.md](./description-discard.md) — roadmap связки SCRUM-15/16/49: описание предмета, discard, тост со статами (05.09)
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

> Промты сессий живут в roadmap связки — [description-discard.md](./description-discard.md), раздел «Промты»: **сессия 1** (troy-backend + troy-admin, SCRUM-15/16) и **сессия 2** (troy-flutter, SCRUM-75 (клиент 15/16) + SCRUM-49). Между ними пользователь перегенерирует Dart-клиент (`./tools/generate_openapi.sh`). Редизайн мешка — отдельная сессия по промту в [redesign.md](./redesign.md). Общие правила — в [roadmap/README.md](../README.md).
