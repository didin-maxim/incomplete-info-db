# Интерактивы для Кнопа 2011, занятие 3

Этот файл фиксирует кандидатов на будущий интерактивный слой. Сами `interactive`-поля в карточки этого прохода не добавлялись.

## Сильные кандидаты

- `three-coins-unknown-sign-two-weighings`: малый интерактив `single_counterfeit_unknown_direction`; полезен как учебный режим для неизвестного знака и таблицы невозможных пар исходов.
- `four-labeled-weights-one-defective-two-weighings`: интерактив для подписанных гирь с известными номиналами и неизвестным направлением дефекта; нужен учет номинальных сумм.
- `thirteen-labeled-weights-one-defective-three-weighings`: плановая версия с таблицей “судеб” гирь; хороший кандидат для будущего слоя ternary/linear signatures.
- `ten-row-fakes-on-right-two-weighings`: интерактив на скрытую границу в ряду; пользователь выбирает взвешивания, движок хранит монотонный суффикс легких монет.
- `ten-weights-adjacent-labels-swapped-two-weighings`: интерактив на девять соседних обменов этикеток; нужен режим подписанных масс.
- `nine-circle-two-adjacent-light-two-weighings` и `nine-circle-three-consecutive-light-two-weighings`: общий интерактив `constrained_light_counterfeit_sets` с круговой раскладкой и скрытым соседним блоком.
- `nine-coins-one-sticking-balance-three-weighings`: отдельный тип для двух внешне одинаковых весов, одни из которых всегда показывают равенство; важен режим противника.
- `five-coins-two-equal-fakes-find-genuine`: интерактив “найти хотя бы одну настоящую”, где цель не полная идентификация фальшивых.

## Более осторожные кандидаты

- `lost-weight-among-nine-two-weighings`: возможен интерактив на пропавший объект и переиндексацию оставшихся гирь по размеру, но сначала стоит проверить полную таблицу вторых взвешиваний.
- `nine-circle-arithmetic-progression-find-heaviest-two-weighings`: интерактив не про фальшивку, а про скрытый циклический сдвиг числовых весов; лучше делать после появления общего типа для структурных скрытых состояний.

## Вероятностный слой

- Естественные кандидаты для будущих вероятностных задач: `ten-row-fakes-on-right-two-weighings`, `nine-circle-two-adjacent-light-two-weighings`, `nine-circle-three-consecutive-light-two-weighings` и `nine-circle-arithmetic-progression-find-heaviest-two-weighings`. У них конечное равномерное пространство состояний из 9 случаев, поэтому можно обсуждать ожидаемую длину адаптивной стратегии или максимизацию ожидаемого успеха при одном взвешивании.
- `nine-coins-one-sticking-balance-three-weighings` также подходит для вероятностного слоя, если задать априорное распределение на фальшивую монету и на то, какие весы заедают; это уже не голая вероятность, а сравнение стратегий при ненадежном приборе.
- Probability-only карточки из занятия 3 в этом проходе не добавлялись.
