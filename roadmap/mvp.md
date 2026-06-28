# MVP Roadmap

MVP — это минимальная версия, в которой игрок может пройти полный игровой цикл:

```
Регистрация / логин
→ создание или выбор персонажа
→ выход на карту
→ поиск моба рядом
→ бой
→ получение опыта и лута
→ усиление персонажа
→ повтор цикла
```

Все задачи ниже должны оцениваться через этот цикл. Если задача не приближает playable loop, она не входит в MVP.

## Фазы

| Фаза | Цель | Детали |
|---|---|---|
| MVP-0 | Стабилизировать текущий клиентский flow | [current-flow.md](./current-flow.md) |
| MVP-1 | Сделать карту игровой, а не декоративной | [playable-map.md](./playable-map.md) |
| MVP-2 | Довести бой до полного server-driven loop | [battle-loop.md](./battle-loop.md) |
| MVP-3 | Добавить профиль, инвентарь и экипировку | [inventory-profile.md](./inventory-profile.md) |
| MVP-4 | Наполнить игру контентом и балансом | [content-balance.md](./content-balance.md) |
| MVP-5 | Подготовить MVP к реальному тестированию | [hardening.md](./hardening.md) |

## Scope MVP

Входит:

- Email auth: регистрация, логин, refresh token.
- До 8 персонажей на аккаунт.
- Warrior и Mage.
- Активный персонаж.
- Карта с реальной геопозицией игрока.
- Отображение ближайших мобов.
- Проверка дистанции до моба перед боем.
- Реальный бой с backend state.
- XP, level progression, loot.
- Инвентарь и экипировка.
- Базовый профиль персонажа.
- Seed-контент для одной тестовой зоны.

Не входит:

- Rogue.
- PvP.
- Торговля.
- Гильдии.
- Квесты.
- Социальные механики.
- Продвинутый procedural spawning.
- Production-grade moderation/admin panel.

## Источники требований

- Game loop: [overview.md](../game-design/overview.md)
- Классы: [classes.md](../game-design/classes.md)
- Статы и формулы: [stats-and-formulas.md](../game-design/stats-and-formulas.md)
- Leveling: [leveling.md](../game-design/leveling.md)
- Бой: [combat.md](../game-design/combat.md)
- Выбор персонажа: [character-selection.md](../game-design/character-selection.md)
- Auth: [auth.md](../technical/auth.md)
- Геолокация: [geolocation.md](../technical/geolocation.md)
- База данных: [database-schema.md](../technical/database-schema.md)

## Definition of Done для MVP

- Новый пользователь может зарегистрироваться и войти.
- Если персонажей нет, пользователь обязан создать персонажа.
- Если персонажи есть, пользователь может выбрать активного.
- На карте используется реальная позиция устройства.
- Мобы приходят с backend, а не захардкожены на клиенте.
- Бой нельзя начать вне допустимого радиуса.
- Победа в бою меняет состояние персонажа: XP, level при необходимости, loot.
- Игрок видит полученный лут и может экипировать предмет.
- Экипировка меняет computed stats.
- App restart не ломает auth и active character state.
- Backend и Flutter проходят базовую статическую проверку.

## Текущий приоритет

Сначала закрыть MVP-0. Сейчас главный риск не в backend, а в незавершенном Flutter flow выбора персонажа и в рассинхроне sprite/assets для Warrior/Mage.
