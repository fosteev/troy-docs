# MVP-3 · Редизайн инвентаря

> **Статус: не начат.** Только Flutter, новых эндпоинтов не требует. Делается после основной части [MVP-3](./README.md).

Первая реализация собрала профиль и мешок в один Hero-экран (`features/profile/`, один скролл, инвентарь в самом низу; `features/inventory/` — пустые заглушки). Аудит того, что есть, и интерактивный прототип нового инвентаря — [design/prototypes/inventory-redesign.html](../../design/prototypes/inventory-redesign.html) (открыть в браузере). Промт — в конце этого документа.

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
- **Discard / Use** — в UI появляются только вместе с эндпоинтами (gaps #2, #3 в [backend-gaps.md](./backend-gaps.md)); мёртвые кнопки не шипим.
- **Domain остаётся в `profile`** (`InventoryItem`, `HeroSnapshot`, `HeroCubit`), `features/inventory/` — presentation поверх того же cubit. Один снапшот на оба экрана.
- **Углы** — приложение остаётся на `tokens.radius*`; sharp pixel-рамки из прототипа — отдельный шаг по всей дизайн-системе.
- **Навигация** — HERO четвёртым табом (по прототипу) или действием в app bar инвентаря; решить в шаге и записать здесь.


## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy/troy-flutter.

Прочитай:
- troy-docs/design/prototypes/inventory-redesign.html — открой в браузере, прокликай 5 экранов; заметки под каждым телефоном и таблица «What it costs» — это ТЗ;
- troy-docs/roadmap/mvp-3-inventory/redesign.md (этот документ, решения выше) + README.md и backend-gaps.md рядом;
- lib/features/profile/** — текущий Hero-экран (HeroCubit, HeroSnapshot, InventorySection, EquipmentPanel, ItemInspectSheet, ItemGlyphIcon);
- lib/features/map/presentation/widgets/map_nav_bar.dart — текущий bottom nav (BACKPACK · MAP · MENU);
- "Architecture rules" в troy-flutter/CLAUDE.md.

Структура:
- features/inventory/ — presentation-фича (InventoryPage + виджеты). Domain (InventoryItem, HeroSnapshot, HeroSlot) остаётся в features/profile/domain, InventoryPage работает поверх того же HeroCubit — это осознанно: один снапшот на оба экрана, без цикла зависимостей между фичами. Пустые .gitkeep в inventory/domain и inventory/data удалить.
- Общие вещи (ItemGlyphIcon, RarityColors, EquipSlot, ItemCell, DashedBox) → lib/shared/widgets/ (или оставить в profile, если тянет только inventory — решить по факту использования).
- HeroCubit — один инстанс на HomeShell (провайдить выше обоих экранов), load() один раз, оба экрана слушают.

Навигация:
- BACKPACK в nav bar → InventoryPage. Hero (профиль, полная кукла со спрайтом, атрибуты, derived) — четвёртый таб HERO по прототипу. Если четыре таба ломают текущий бар с большим центральным MAP — HERO действием в app bar инвентаря. Выбрать одно, зафиксировать в redesign.md.
- Из HeroPage секцию InventorySection убрать; EquipmentPanel там остаётся.

InventoryPage (экран 1 прототипа):
- App bar: заголовок + золото (справа). Футер с золотом убрать.
- Полоса куклы: 6 EquipSlot ~48px с подписями слотов. Тап по слоту → slot sheet (ниже) + подсветка в сетке предметов, подходящих в этот слот (остальные dim, не скрывать).
- Вместимость: сегментированный бар used/40 (capacity — константа HeroSnapshot.capacity), при >= 90% — tokens warning.
- Чипы фильтра как сейчас + sort-чип: rarity ↓ (default) / newest / type. Accessory фильтруем по slot == ring.
- Сетка 4 колонки, min 12 ячеек, добивка dashed (как сейчас). Бейджи ячейки: quantity (как сейчас), метка слота (3 буквы, низ-лево), NEW (верх-лево), ▲ апгрейд (низ-право, success) если slot != null и суммарный бонус > суммарного бонуса надетого в этот слот (или слот пуст).
- NEW: локальный набор «виденных» itemId (SharedPreferences); предмет перестаёт быть NEW после открытия его карточки или equip. Бэкенд acquiredAt не ждём.
- Пустой мешок — просто dashed-сетка, без текста и CTA. Loading — тот же каркас (dashed ячейки), без центрального спиннера.

Item sheet (экраны 2 и 4):
- Шапка как сейчас (glyph, имя цветом rarity, «Rarity · Type · Slot ×N»). Описание — только если item.description != null.
- Бонусы — строками: label | значение | дельта против надетого в этот слот (▲ +N success / ▼ -N error / — muted). Строка «VS. EQUIPPED <имя>» над таблицей, если в слоте что-то есть. Для уже надетого — без дельты, кнопка UNEQUIP вместо EQUIP.
- Consumable: строка эффекта и кнопка USE со степпером — ТОЛЬКО когда закрыт gap #2; до этого sheet информационный. Discard — ТОЛЬКО когда закрыт gap #3.
- Equip/Unequip → закрыть sheet → тост с дифом computedStats старого и нового снапшота (например «PHYS ATK +7 · ARMOR -2»), а не суммой бонусов предмета. Тост — shared виджет, если его ещё нет.

Slot sheet (экран 3):
- Тап по слоту куклы (и в InventoryPage, и в EquipmentPanel на Hero) → sheet: что надето (glyph, имя, чипы бонусов) + UNEQUIP; ниже «SWAP FOR» — горизонтальный список предметов мешка с подходящим slot, отсортирован по rarity, с ▲ у апгрейдов; тап = equip (бэкенд сам снимает предыдущее). Пустой слот — без блока «Equipped», сразу список. Мгновенный unequip по тапу на слот убрать.
- Во время мутации (HeroCubit._mutationInFlight) — кнопки sheet disabled, тап по ячейкам игнорируется; после ответа sheet закрывается.

Тексты — в assets/translations/en.json и ru.json (ключи hero.* / inventory.*), без хардкода.

Тесты (flutter_test + mocktail, по эталону auth):
- unit: сортировка/фильтр/подсветка по слоту, эвристика апгрейда, диф computedStats для тоста, NEW-набор;
- widget-smoke InventoryPage: сетка рендерит bag без надетых, чип фильтрует, тап по слоту открывает slot sheet со «SWAP FOR» только подходящих, тап по предмету открывает item sheet с дельтой;
- HeroCubit: существующие тесты не ломаем; если cubit поднимается на уровень shell — тест на один load для обоих экранов.

DoD: BACKPACK открывает отдельный экран инвентаря по прототипу; Hero без мешка; equip из slot sheet и из item sheet работает против реального бэкенда, после equip/unequip тост с дифом статов; NEW/▲/бейдж слота на ячейках; пустой мешок = dashed-сетка; нет кнопок без эндпоинта; flutter analyze чисто; flutter test зелёный. Коммит. Отметить шаг [x] в troy-docs/roadmap/README.md и обновить статус в redesign.md (что реализовано, что отложено).
```
