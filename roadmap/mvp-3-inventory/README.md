# MVP-3 — Profile, Inventory, Equipment

> **Статус: в работе.** Клиент: Hero-экран (профиль + кукла + мешок одним скроллом) на реальном API, тесты зелёные. Бэкенд: профиль, инвентарь, equip/unequip, очки атрибутов — есть; открыты [backend-gaps.md](./backend-gaps.md) #1–#3, class restrictions (#4) не решены. Следующий шаг — [redesign.md](./redesign.md).

Цель: игрок должен видеть прогресс персонажа и усиливать его через предметы.

## Продуктовый результат

После боев игрок получает предметы, открывает инвентарь, экипирует предмет и видит изменение характеристик.

## Backend

- [x] Endpoint профиля активного персонажа.
- [x] Endpoint инвентаря.
- [x] Equip/unequip endpoint.
- [x] Проверка слотов экипировки.
- [ ] Проверка class restrictions, если они есть у предмета.
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

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила (архитектура, тесты, делегирование) — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy (Flutter + backend).

Прочитай:
- troy-docs/roadmap/mvp-3-inventory/README.md, troy-docs/game-design/stats-and-formulas.md, leveling.md;
- "Architecture rules" в troy-flutter/CLAUDE.md, эталон auth;
- заглушки lib/features/profile/** и lib/features/inventory/**.

Backend (troy-backend) — проверить/добить:
- профиль активного персонажа; инвентарь; equip/unequip; проверка слотов и class restrictions;
- computed stats = base + level growth + free attribute points + equipment bonuses.

Flutter — две фичи profile и inventory по стандарту (domain/data/presentation):
- profile: entity Player + computed stats, repo (Either), ProfileBloc, экран (имя, класс, уровень, XP progress, статы, computed);
- inventory: entity InventoryItem, repo (Either), InventoryBloc, экраны (список с rarity/slot/equipped, equip/unequip, визуальный отклик на смену статов).

Тесты (по эталону auth): profile + inventory repository_impl, блоки, мапперы; backend — тест на equip/unequip и пересчёт computed stats.

DoD: полученный в бою предмет появляется в инвентаре; equip/unequip работает; экипировка меняет computed stats; UI обновляется без рестарта; flutter analyze чисто; flutter test зелёный; backend тесты зелёные. Коммит. Отметить фазу [x] в troy-docs/roadmap/README.md.
```
