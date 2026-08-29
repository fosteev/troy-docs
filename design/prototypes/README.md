# Прототипы боевого экрана

Одностраничные HTML-макеты для быстрого взгляда на вёрстку без сборки Flutter.
Каждый файл самодостаточен: стили инлайном, картинки — data-URI, внешний только
шрифт с Google Fonts. Открывается двойным кликом.

## battle-screen-current.html

Реплика **текущего** боевого экрана (`troy-flutter/lib/features/battle/presentation/pages/battle_page.dart`,
состояние после Шага 3Б / P1). Снята с кода, а не со скриншота:

- логический пиксель Flutter = CSS-пиксель, поэтому экран 390 × 844 и все боксы
  (карточки бойцов, высоты кнопок, отступы) совпадают числом;
- цвета — `RealmWalkerTheme.fallback` и `ColorScheme.dark` из `app/theme/`;
- шрифт — Jersey 10, тот же, что в приложении (`assets/fonts/Jersey_10`);
- спрайты — по одному кадру из реальных листов приложения;
- иконки скиллов — `assets/war1/war1_skill_*.png` этого же репозитория, стоимости
  и кулдауны из `troy-backend/prisma/seed.ts` (Heavy Strike 25 / 4 с,
  Shield Slam 35 / 8 с).

Переключатели справа показывают состояния P1: каст моба с телеграфом, HP < 25 %
с виньеткой, радиальный кулдаун, нехватку ресурса, оверлей переподключения.
Кнопки «проиграть» повторяют тайминги `BattleChoreographer` (700 / 950 / 1200 мс),
отказ ack и канал побега.

**Чего нет:** анимации спрайт-листов (везде один кадр, поэтому не виден hit-stop),
фолбэка кнопки на имя скилла (он рисуется, когда у скилла нет иконки),
настоящих кривых твинов.

### Как обновить кадры спрайтов

```python
from PIL import Image
im = Image.open('troy-flutter/assets/images/sprites/war1/war1_idle.webp')
cols, rows, frame = 4, 6, 0                      # см. class_fallback_sprites.dart
fw, fh = im.width // cols, im.height // rows
c, r = frame % cols, frame // cols
tile = im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
tile = tile.crop(tile.getbbox())                 # срезать прозрачные поля
tile.resize((300, round(300 * tile.height / tile.width))).save('player.webp', quality=82)
```

Дальше — `base64.b64encode(...)` и подстановка в `src="data:image/webp;base64,…"`.
