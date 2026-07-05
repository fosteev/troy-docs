# Промт: визуальный редизайн экрана боя (troy-flutter)

> Готовый self-contained промт для делегирования (GLM/codex) или прямой реализации.
> Только presentation-слой. НОЛЬ game-authoritative расчётов на клиенте — правило
> из `troy-flutter/CLAUDE.md` в силе.

## Контекст

Экран боя `lib/features/battle/presentation/pages/battle_page.dart` уже работает:
real-time, server-authoritative, WS-only. `BattleBloc` отдаёт `BattleActive` со
снапшотом `BattleState` (см. domain-сущности) — клиент только рисует и шлёт
интенты (`SkillPressed` / `FleePressed`). Сейчас вёрстка функциональная и
текстовая: `Column` = панель моба сверху → текстовый лог в центре → панель игрока
→ скиллы. Никаких «моделек» нет.

Надо переделать в **визуальный бой**: моделька игрока и моделька босса на
анимированном фоне, всплывающие цифры урона над модельками, короткий флеш модели
при получении урона, скиллы снизу.

## Что рисуем (layout)

`_ActiveBattle` перевести с `Column` на **`Stack`** со слоями (снизу вверх):

1. **Фон** — как на экране авторизации: переиспользовать `SpriteSheetAnimator`
   с `assets/images/login_background_sprite.png` (параметры — из
   `login_page.dart:65`: `columns:4, rows:8, frameCount:29, fps:10, fit: cover`),
   `Positioned.fill`.
2. **Градиент-оверлей** для читаемости — тот же 4-стоповый градиент, что в
   `login_page.dart` (тёмный низ `#15161c`), `Positioned.fill`.
3. **Модельки бойцов**:
   - **Босс** — верхняя треть, по центру/чуть выше.
   - **Игрок** — нижняя треть, над баром скиллов, чуть левее.
   Каждая моделька = виджет `_CombatantModel` (см. ниже).
4. **Слой всплывающих цифр урона** (`_DamageNumbersLayer`) — поверх бойцов,
   `IgnorePointer`, `Positioned.fill`.
5. **Нижний UI**: ресурс-бар игрока (`_ResourceBar`) + `_SkillBar` + `_FleeButton`
   (переиспользовать существующие, просто перенести вниз стека).

**Центральный текстовый лог убрать** из активного боя. Класс `_CombatLog` и
`_BattleLogSheet` НЕ удалять — `_BattleLogSheet` (полный «Журнал боя») по-прежнему
открывается с экрана результата (`_BattleResult`), эту кнопку и логику не трогаем.

## Моделька игрока

Класс-спрайт по эталону `lib/features/profile/presentation/widgets/equipment_panel.dart:122`:

```dart
CharacterClass.warrior => SpriteSheetAnimator(
  assetPath: 'assets/images/sprites/war1/war1_idle.png',
  columns: 4, rows: 6, frameCount: 19, fps: 10),
CharacterClass.mage => SpriteSheetAnimator(
  assetPath: 'assets/images/sprites/mage1/mage1_idle.png',
  columns: 4, rows: 6, frameCount: 19, fps: 10),
```

**Проблема:** `BattleRoute` сейчас принимает только `monsterId`/`spawnId`, класс не
знает. `BattlePlayer` тоже не несёт класс — только `resourceType`.
**Решение (primary):** прокинуть `CharacterClass` в `BattleRoute` — `map_page.dart`
уже держит `active.characterClass` (строки ~194/280), передать при создании
`BattleRoute(...)` (строка 81). Fallback, если не хочется трогать роут: вывести
класс из `resourceType` (`rage → warrior`, `mana → mage`) — сейчас 1:1, но это
семантический хак; primary-путь чище.

## Моделька босса — СЕАМ ПОД АССЕТЫ (спрайтов мобов пока нет)

Реального арта мобов в проекте нет, а `BattleMonster` несёт только
`name/level/hp/effects/cast`. Задача — **заложить абстракцию**, чтобы позже
подключить:
- отдельный **idle-спрайт на каждого моба**,
- отдельный **спрайт-анимацию на каждый скилл моба**.

Сделать резолвер (напр. `lib/features/battle/presentation/widgets/monster_sprite.dart`):

```dart
/// Маппинг моба → спрайт. Пока ассетов нет — возвращает null, рисуем плейсхолдер.
/// Когда появятся спрайты: класть в assets/images/sprites/monsters/<key>/idle.png
/// и добавлять запись сюда. Ключ — по monster name (позже по monsterId/типу с бэка).
class MonsterSprite {
  static SpriteSheetConfig? idleFor(String monsterName) => null; // TODO: реальные ассеты

  /// Спрайт под скилл моба (по skillCode из лога/каста). Пока null → без анимации скилла.
  static SpriteSheetConfig? skillFor(String skillCode) => null; // TODO
}
```

Плейсхолдер босса, пока `idleFor` == null: **НЕ рисовать никакого нового арта и
никаких `CustomPaint`-силуэтов**. Заглушка = переиспользовать существующий
класс-спрайт как стенд-ин, напр. `mage1_idle` (`assets/images/sprites/mage1/mage1_idle.png`,
`columns:4, rows:6, frameCount:19, fps:10`), при желании отзеркалить по X
(`scaleX: -1`), чтобы «смотрел» на игрока. Это временный стенд-ин — как только
`idleFor(monsterName)` начнёт возвращать конфиг, автоматически рисуется реальный
моб без правок вёрстки. Зарегистрировать в `pubspec.yaml` будущую директорию
`assets/images/sprites/monsters/` (создать `.gitkeep`), чтобы дроп реальных
ассетов не требовал правки pubspec-структуры.

Скилл-спрайт моба (`skillFor`) — только **сеам**, полноценную анимационную
систему сейчас НЕ строить: точка вызова есть (при касте/скилл-логе моба), реализация
= no-op пока ассетов нет. Пометить `// TODO` и оставить на будущее.

## `_CombatantModel` (общий виджет бойца)

Один виджет и для игрока, и для босса:
- спрайт (класс-idle для игрока / плейсхолдер или `MonsterSprite.idleFor` для моба);
- **HP-бар** + `name`/`level` (для моба; игроку — можно только HP);
- ряд эффектов (`_EffectsRow` — переиспользовать) и каст-бар (`_CastBar`) при `cast != null`;
- **флеш при уроне** — короткая подсветка модели (см. ниже).

## Всплывающие цифры урона + флеш — ядро задачи

**Источник истины — combat-log из снапшота.** `BattleActive` несёт `recentLog`
(хвост, cap 12) — список `BattleLogEntry { at, kind, source, skillCode?, amount? }`.
- `kind`: `hit | crit | miss | skill | effect | dot`
- `source`: `player | monster` — **кто нанёс** (не кто получил!)
  - `source == player` → урон **по боссу** → цифра над боссом, флеш босса.
  - `source == monster` → урон **по игроку** → цифра над игроком, флеш игрока.

**Детекция новых событий:** обернуть слой моделек/цифр в `StatefulWidget` +
`BlocListener<BattleBloc, BattleState>`. На каждый новый `BattleActive` вычислять
**дельту** `recentLog` относительно уже отрисованного, используя `at`
(elapsed-ms) как watermark: спавнить цифры только для entries с `at > lastRenderedAt`,
затем обновлять `lastRenderedAt`. На **первом** снапшоте (инициализация) цифры НЕ
спавнить — только запомнить watermark (иначе на входе в бой полетит пачка).

**`_FloatingDamage`** (StatefulWidget, свой `AnimationController`): всплывает вверх
~40–60px и гаснет за ~700–900ms, затем сам удаляется из списка слоя. Горизонтальный
джиттер ±несколько px, чтобы серии хитов не накладывались. Стиль по `kind`:
- `hit` — обычная (белая/жёлтая),
- `crit` — крупнее + красная, лёгкий «поп» scale,
- `miss` — серое «MISS» (по `amount == null`/kind),
- `dot` — тиковый цвет (напр. фиолетовый), можно мельче,
- `heal` (через `effect`/heal) — зелёная с `+`.
Цвета вынести в маленькую локальную палитру по образцу
`presentation/theme/rarity_colors.dart` (единственный разрешённый хардкод цветов).

**Флеш:** при попадании по бойцу — короткая (120–180ms) подсветка его модели
(`ColorFiltered`/наложение полупрозрачного цвета через короткий контроллер, либо
`TweenAnimationBuilder`). Реализовать как триггер внутри `_CombatantModel` (напр.
через `key` + вызов из слоя, или счётчик попаданий в модель, который она слушает).

## Ограничения / правила

- Только `features/battle/presentation` (+ pubspec assets, + `BattleRoute` param,
  + правка вызова роута в `map_page`). Никаких новых domain/data, `BattleBloc` и
  маппер не трогать — `recentLog` уже там.
- НОЛЬ игровой математики: цифры/флеш — чистая презентация из серверного лога.
- Локали `battle.*`, `TextStyles`, тема — переиспользовать; новые строки (напр.
  «MISS») добавить в en/ru.
- Не ломать экран результата (`_BattleResult`), «Журнал боя», flee-hold, каст-бар,
  эффекты, ресурс-бар.

## DoD / тесты (flutter_test + mocktail, без golden)

- Деривация цифр из дельты лога: два последовательных `BattleActive`, N новых
  `hit`-entries → N `_FloatingDamage` над корректной целью (player-source → босс,
  monster-source → игрок).
- Первый снапшот не спавнит цифры (watermark инициализируется молча).
- `MonsterSprite.idleFor` == null сейчас → рисуется плейсхолдер (не крашится).
- Класс-спрайт игрока: warrior → war1, mage → mage1.
- Smoke-render активного боя без overflow.
- `flutter analyze` чисто, весь набор зелёный.
```
