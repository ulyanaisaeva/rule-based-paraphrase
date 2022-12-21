## Перефразирование текстов на основе правил

Пайплайн для перефразирования текстов при помощи правиловых замен. Правила покрывают различные виды грамматической эквивалентности, по схеме одно правило-один модуль. 

### Актуальный список модулей

| Модуль (правило) | Класс | Пример | Ограничения (что правилом не обрабатывается) | Обратный модуль (если есть) |
| --- | --- | --- | --- | --- |
| Причастие → относительная клауза | PartToRelativeModule | Эксперты раскрыли простые способы, позволяющие избежать неприятностей в аэропорту → Эксперты раскрыли простые способы, которые позволяют избежать неприятностей в аэропорту. | Причастный оборот перед вершиной | --- |
| Деепричастие → финитный глагол | ConverbToConjuctionModule  | Кубрик скончался в 1999 году, оставив после себя несколько незаконченных проектов. → Кубрик скончался в 1999 году и оставил после себя несколько незаконченных проектов.  | --- | --- |
| Финитный глагол → деепричастие | FintoConv | В Анси мужчина после окончания матча Франция-Хорватия скончался, сломал шею и спрыгнул с моста. → В Анси мужчина после окончания матча Франция-Хорватия, скончавшись, сломав шею, спрыгнул с моста. | Обрабатываются только конъюнкты глагола | ConvToFin |
| Относительная клауза → причастный оборот | ReltoPart | Было установлено, что он принадлежал сотруднику, который к тому моменту окончил командировку по срочному трудовому договору. → Было установлено, что он принадлежал сотруднику,  к тому моменту окончившему  командировку по срочному трудовому договору. | Обрабатываются только следующие случаи: 1) "который" - подлежащее в относительной клаузе (nsubj и nsubj:pass); 2) "который" зависит от предлогов "на" и "в" (в таком случае происходит перефразирование в обстоятельство с "где" или "куда" | PartToRel |
