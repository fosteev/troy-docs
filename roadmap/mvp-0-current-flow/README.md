# MVP-0 — Current Flow Stabilization

> **Статус: сделано.** Шаг 1 (`character` → Clean Architecture + финал flow) и [backend-тест-фундамент](./backend-tests.md) влиты в `main`. Ниже — исходная спека и промт, по которым это делалось.

Цель: закрыть текущий пользовательский путь от auth до карты без сломанных переходов, временных заглушек и визуального рассинхрона.

## Продуктовый результат

Пользователь после логина всегда попадает в корректное состояние:

- нет персонажей → создание персонажа;
- есть персонажи, активный выбран → карта;
- есть персонажи, активный не выбран → выбор персонажа;
- из профиля можно сменить активного персонажа.

## Backend

- [x] Проверить, что `GET /characters` возвращает `isActive`.
- [x] Проверить, что `POST /characters` делает созданного персонажа активным.
- [x] Проверить, что `POST /characters/:id/select` снимает active flag с остальных персонажей пользователя.
- [x] Ошибки должны возвращаться в едином API envelope.

## Flutter

- [x] Закрыть текущий WIP выбора персонажа.
- [x] После выбора персонажа не показывать пустой loading screen, а обновлять список и состояние выбранной карточки.
- [x] Не давать выбирать уже активного персонажа.
- [x] После создания персонажа вести пользователя на карту.
- [x] Подключить map sprite для Mage.
- [x] Маркер игрока на карте должен зависеть от класса активного персонажа.
- [x] Убрать `flutter analyze` warning в router imports.
- [x] Проверить back/logout behavior на экранах создания и выбора персонажа.

## Assets

- [x] Warrior:
  - `war1_idle.png`
  - `war1_face_icon.png`
  - `war1_map_walk.png`
- [x] Mage:
  - `mage1_idle.png`
  - `mage1_face_icon.png`
  - `mage1_map_walk.png`

## Definition of Done

- [x] `flutter analyze` проходит без issues.
- [x] Новый пользователь создает персонажа и попадает на карту.
- [x] Пользователь с несколькими персонажами выбирает активного и видит правильный sprite на карте.
- [x] Повторный запуск приложения сохраняет auth state и active character flow.

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила (архитектура, тесты, делегирование) — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy/troy-flutter (Flutter, ветка refactor/clean-arch-foundation).

Прочитай:
- раздел "Architecture rules (MUST follow)" в CLAUDE.md;
- эталонную фичу auth целиком: lib/features/auth/** (domain/data/presentation, DI в lib/app/di/injection.dart);
- troy-docs/roadmap/mvp-0-current-flow/README.md и troy-docs/roadmap/README.md (секция "Зафиксированные решения").

Задача A — мигрировать фичу character на тот же шаблон, что и auth:
- domain/entities/character.dart — freezed-модель Character (поля из CharacterSummaryDto: id, name, class, level, isActive);
- domain/repositories/character_repository.dart — абстрактный интерфейс, методы возвращают Future<Either<Failure, T>>;
- data/datasources/character_remote_datasource.dart — обёртка над ApiClient.characters, говорит DTO, кидает на транспорте;
- data/mappers/character_mapper.dart — CharacterSummaryDto → domain Character;
- data/repositories/character_repository_impl.dart — _guard → mapErrorToFailure, маппинг DTO→entity;
- presentation/bloc/character_bloc.dart — на result.fold(), без парсинга DioException;
- presentation/pages/** — bloc через GetIt.I<CharacterBloc>(), ошибки через context.showErrorSnackBar, экраны на AppScaffold + AppBarCloseAction; страницы оперируют domain Character, а не DTO;
- DI: datasource → repository(as интерфейс) → CharacterBloc(factory); удалить старый CharacterRepository и character_model.dart, если заменены.

Задача B — доделать MVP-0 (спека выше), с учётом зафиксированных решений:
- успешный select И create → context.router.replaceAll([const HomeShellRoute()]) (всегда на карту);
- нельзя выбрать уже активного: onTap = null при character.isActive;
- во время select — спиннер на тапнутой карточке, список персонажей не пропадает (не полноэкранный лоадер);
- удалить мёртвый стейт CharacterReady, если он больше не эмитится;
- маркер игрока на карте зависит от класса активного персонажа (player_map_marker / map_page).

Задача C — тесты (эталон + покрытие), стек flutter_test + mocktail (без bloc_test):
- создай ЭТАЛОННЫЕ тесты для уже готовой фичи auth (test/features/auth/...): auth_repository_impl (datasource замокан: успех → Right, ошибки → нужный Failure) и auth_bloc (события → последовательность стейтов). Это образец для всех будущих фич;
- по тому же образцу покрой character: character_repository_impl, character_bloc, character_mapper.

DoD: flutter analyze — без issues; flutter test — зелёный (auth + character покрыты на слоях data+bloc+mappers); вручную проходит «создание персонажа → карта» и «выбор персонажа → карта»; повторный запуск сохраняет auth + активного персонажа. Коммить на текущей ветке отдельным коммитом. Отметить фазу [x] в troy-docs/roadmap/README.md.
```
