# LLM-Mutants: Analiza efektywności generowania operatorów mutacyjnych za pomocą dużych modeli językowych

**Kierunek**: Informatyka
**Specjalność**: Inżynieria Oprogramowania
**Numer albumu**: 1185432
**Autor:** Miraslau Douher
**Promotor:** dr. prof. Michał Mnich
**Uczelnia:** Uniwersytet Jagielloński
**Rok:** 2026

---

## Spis treści

- [Streszczenie](#streszczenie) (TO DO)

- [1 Wstęp](#rozdział-wstęp) (DONE)
  - [1.1 Temat i cel pracy](#temat-i-cel-pracy) (DONE)
  - [1.2 Budowa pracy](#budowa-pracy) (DONE)

- [2 Testowanie mutacyjne](#testowanie-mutacyjne) (TO DO)
  - [2.1 Czym jest mutant?](#czym-jest-mutant) (DONE)
  - [2.2 Zabicie mutanta i mutation score](#zabicie-mutanta-i-mutation-score) (DONE)
  - [2.3 Proces testowania mutacyjnego krok po kroku](#proces-testowania-mutacyjnego-krok-po-kroku) (TO DO)
  - [2.4 Koszty i problemy praktyczne](#koszty-i-problemy-praktyczne) (TO DO)
    - [2.4.1 Czas wykonania i narzut obliczeniowy](#czas-wykonania-i-narzut-obliczeniowy) (TO DO)
    - [2.4.2 Redukcja liczby mutantów (selektory, sampling)](#redukcja-liczby-mutantów-selektory-sampling) (TO DO)

- [3 Operatory mutacyjne w narzędziach klasycznych](#operatory-mutacyjne-w-narzędziach-klasycznych) (TO DO)
  - [3.1 Czym jest PIT i jak działa](#czym-jest-pit-i-jak-działa) (TO DO)
  - [3.2 Model generacji mutantów w PIT](#model-generacji-mutantów-w-pit) (TO DO)
  - [3.3 Katalog operatorów: typy i przykłady](#katalog-operatorów-typy-i-przykłady) (TO DO)
  - [3.4 Ograniczenia operatorów klasycznych](#ograniczenia-operatorów-klasycznych) (TO DO)
    - [3.4.1 Ograniczona różnorodność transformacji](#ograniczona-różnorodność-transformacji) (TO DO)
    - [3.4.2 Niedopasowanie do błędów z praktyki](#niedopasowanie-do-błędów-z-praktyki) (TO DO)

- [4 Duże modele językowe w inżynierii oprogramowania](#duże-modele-językowe-w-inżynierii-oprogramowania) (TO DO)
  - [4.1 Czym są LLM?](#czym-są-llm) (TO DO)
  - [4.2 LLM w pracy programisty: typowe zastosowania](#llm-w-pracy-programisty-typowe-zastosowania) (TO DO)
  - [4.3 LLM jako generator zmian w kodzie](#llm-jako-generator-zmian-w-kodzie) (TO DO)
  - [4.4 Ryzyka i ograniczenia LLM (z perspektywy jakości kodu)](#ryzyka-i-ograniczenia-llm-z-perspektywy-jakości-kodu) (TO DO)

- [5 Dane eksperymentalne i metryki](#dane-eksperymentalne-i-metryki) (TO DO)
  - [5.1 Zbiór rzeczywistych błędów](#zbiór-rzeczywistych-błędów) (TO DO)
  - [5.2 Rodzaje mutantów](#rodzaje-mutantów) (DONE)
    - [5.2.1 Compilable mutants](#compilable-mutants) (DONE)
    - [5.2.2 Duplicate mutants](#duplicate-mutants) (DONE)
    - [5.2.3 Equivalent mutants](#equivalent-mutants) (DONE)
  - [5.3 Metryki i kryteria oceny](#metryki-i-kryteria-oceny) (TO DO)
    - [5.3.1 LLM New Mutant Rate](#llm-new-mutant-rate) (TO DO)
    - [5.3.2 Real Bug Detection Rate](#real-bug-detection-rate) (TO DO)
    - [5.3.3 Average Ochiai Rate](#average-ochiai-rate) (TO DO)
    - [5.3.4 Coupling Rate](#coupling-rate) (TO DO)
    - [5.3.5 Average Mutant Generation Time](#average-mutant-generation-time) (TO DO)
    - [5.3.6 Cost per Useful Mutant](#cost-per-useful-mutant) (TO DO)
  - [5.4 Cel pracy i pytania badawcze](#cel-pracy-i-pytania-badawcze) (TO DO)

- [6 Założenia eksperymentu i metodyka](#założenia-eksperymentu-i-metodyka) (TO DO)
  - [6.1 Przebieg eksperymentu](#przebieg-eksperymentu) (TO DO)
  - [6.2 Materiał badawczy — zbiór danych i kryteria doboru](#materiał-badawczy--zbiór-danych-i-kryteria-doboru) (TO DO)
  - [6.3 Generacja mutantów — LLM i PIT](#generacja-mutantów--llm-i-pit) (TO DO)
  - [6.4 Weryfikacja mutantów i zbieranie wyników](#weryfikacja-mutantów-i-zbieranie-wyników) (TO DO)
  - [6.5 Definicja mutanta nowego względem PIT](#definicja-mutanta-nowego-względem-pit) (TO DO)

- [7 Analiza wyników i wnioski](#analiza-wyników-i-wnioski) (TO DO)
  - [7.1 Statystyki ogólne eksperymentu](#statystyki-ogólne-eksperymentu) (TO DO)
  - [7.2 RQ1 — Różnorodność i nowość operatorów LLM](#rq1--różnorodność-i-nowość-operatorów-llm) (TO DO)
  - [7.3 RQ2 — Podobieństwo mutantów do defektów rzeczywistych](#rq2--podobieństwo-mutantów-do-defektów-rzeczywistych) (TO DO)
  - [7.4 RQ3 — Koszty i wydajność podejścia](#rq3--koszty-i-wydajność-podejścia) (TO DO)
  - [7.5 Synteza: LLM vs PIT — kiedy które podejście ma sens](#synteza-llm-vs-pit--kiedy-które-podejście-ma-sens) (TO DO)
  - [7.6 Ograniczenia badania](#ograniczenia-badania) (TO DO)
  - [7.7 Kierunki dalszych badań](#kierunki-dalszych-badań) (TO DO)

- [Podsumowanie](#podsumowanie) (TO DO)

- [Bibliografia](#bibliografia) (TO DO)

## Streszczenie

> ✏️ **Wskazówka do pisania:** Streszczenie piszesz NA KOŃCU, gdy masz już wyniki.
> Napisz 8–12 zdań w następującej kolejności:
> (1) o czym jest praca, (2) jaki problem rozwiązujesz, (3) jak to sprawdzasz,
> (4) 2–3 najważniejsze wyniki liczbowe, (5) jedno zdanie wniosków.
> Bez detali technicznych. Ogólny opis „co i po co".

*[Do napisania jako ostatnie — po przeprowadzeniu eksperymentu i napisaniu pozostałych rozdziałów.]*

Praca dotyczy zastosowania dużych modeli językowych (LLM) do generowania operatorów mutacyjnych — reguł wprowadzania celowych błędów w kodzie źródłowym, służących do oceny jakości testów automatycznych. Klasyczne operatory mutacyjne, definiowane ręcznie w narzędziach takich jak PIT, stanowią ograniczony i statyczny katalog reguł, który może nie odzwierciedlać typów błędów rzeczywiście popełnianych przez programistów. Niniejsza praca weryfikuje, czy LLM są w stanie indukować nowe reguły mutacyjne wykraczające poza ten katalog oraz czy generowane przez nie mutanty są bliższe rzeczywistym defektom oprogramowania pod względem zachowania programu.

W ramach badania przeprowadzono jeden kompleksowy eksperyment na zbiorze błędów z repozytorium Defects4J: wygenerowano mutanty przy użyciu LLM oraz narzędzia PIT dla tych samych projektów Java, następnie każdy mutant poddano kompilacji i uruchomieniu testów, a zebrane dane przeanalizowano pod kątem trzech tez badawczych dotyczących nowości, realizmu i wydajności operatorów LLM.

*[Uzupełnić po eksperymencie: X% wygenerowanych operatorów LLM nie posiadało odpowiednika w katalogu PIT. Mediana podobieństwa testowego (proximity) mutantów LLM do rzeczywistych błędów wyniosła Y, wobec Z dla mutantów PIT. Wyniki sugerują, że …]*

**Słowa kluczowe:** testowanie mutacyjne, operatory mutacyjne, duże modele językowe, LLM, PIT, Defects4J, mutation score, proximity to real bugs.

---

## Rozdział Wstęp

### Temat i cel pracy

Rozwój dużych modeli językowych (ang. *Large Language Models*, LLM) oraz narzędzi opartych na tej technologii doprowadził do szerokiego stosowania automatycznego generowania kodu w produkcji oprogramowania.
Takie podejście przyspiesza pracę programistów chociaż wymaga bardziej dokładnej weryfikacji dla osiągnięcia wystarczająco wysokiego poziomu pewności co do jego poprawności, co wciąż jest warunkiem koniecznym bezpiecznego wdrożenia.
Jedną z najlepszych metod oceny jakości testów jest stosowanie testowania mutacyjnego, polegające na wprowadzaniu drobnych zmian w kodzie i sprawdzaniu, czy istniejące testy potrafią je wykryć.
Klasyczne narzędzia mutacyjne dysponują jednak tylko niewielkim katalogiem operatorów, co ogranicza przestrzeń defektów rzeczywiście popełnianych przez programistów.

Z drugiej strony, LLM trenowane na większości dostępnych w internecie zbiorach kodu oraz historii zgłoszeń bugów, posiadają bardziej szeroką wiedzę defektów popełnianych w rzeczywistym oprogramowaniu.
Dzięki temu możliwe jest wykorzystanie LLM do generowania bardziej nieoczekiwanych oraz realistycznych mutantów.
To pozwala wykraczać poza ograniczony zestaw reguł dostępnych w klasycznych mutacyjnych narzędziach, a tym samym pomoże zwiększyć jakość testów.
Co z kolei pozwala wzmocnić poziom zaufania do oprogramowania, w tym do automatycznie wygenerowanego kodu.

Celem niniejszej pracy jest analiza efektywności generowania operatorów mutacyjnych (mutantów) poprzez duże modele językowe w porównaniu do klasycznych operatorów.
W ramach badania zostaną przeanalizowane nowe operatory LLM, ich bliskości do rzeczywistych błędów oraz wydajności w porównaniu do klasycznych operatorów.

### Budowa pracy

Wygląd zawartości rozdziałów przedstawionych w pracy:

- **Rozdział 1** Temat i cel pracy wraz z zawartością poszczególnych rozdziałów.
- **Rozdział 2** Definicja testowania mutacyjnego, mutation score, rodzaje mutantów oraz opis procesu testowania mutacyjnego.
- **Rozdział 3** Klasyczne operatory mutacyjne na przykładzie narzędzia PIT, zasada działania, katalog operatorów klasycznych z grupy ALL.
- **Rozdział 4** Duże modele językowe w inżynierii oprogramowania, koncepcja LLM jako generatora zmian w kodzie oraz związane z tym ryzyka.
- **Rozdział 5** Rzeczywiste błędy jako podstawa eksperymentu — zbiór Defects4J 2.0, miary podobieństwa mutanta do defektu na podstawie profili testowych oraz kompletna definicja wszystkich metryk i kryteriów oceny stosowanych w badaniu. Następnie problem badawczy, cel pracy i pytania badawcze.
- **Rozdział 6** Metodyka eksperymentu: przebieg, kryteria selekcji błędów, generacja mutantów przez LLM i PIT, weryfikacja oraz definicja mutanta nowego względem PIT — wszystko na podstawie metryk zdefiniowanych w rozdziale 5.
- **Rozdział 7** Analiza wyników eksperymentu, dane liczbowe wraz z ich interpretacją, bezpośrednie odpowiedzi na tezy badawcze, porównanie LLM vs PIT, ograniczenia badania i kierunki dalszych badań.
- **Podsumowanie** Główne wnioski pracy.

## Testowanie mutacyjne

Testowanie mutacyjne to technika oceny tego nam dobrze nasze testy wykrywają defekty w kodzie.
Polega on na tym, że celowo robimy drobne zmiany w kodzie programu, a potem sprawdzamy, czy nasze testy są w stanie te zmiany wykryć.
Każda taka zmiana tworzy nową wersję kodu, zwaną mutantem, który jest następnie sprawdzany przez testy.
Dzięki temu możemy ocenić, jak dobrze nasze testy sprawdzają logikę oraz wymaganie programu i czy są w stanie wykryć potencjalne błędy w kodzie.

Ocena jakości testów automatycznych jednym z najważniejszych problemów inżynierii oprogramowania.
Najczęściej używanym sposobem oceny jest sprawdzenie tzw. pokrycie kodu (ang. *code coverage*), czyli jaki procent kodu jest wykonywany podczas testów.
Jednak problem polega na tym, że nawet jeśli kod jest wykonywany, to niekoniecznie znaczy to, że jest sprawdzany.
Test, który uruchamia metodę, ale nie sprawdza jej wyniku, może mieć 100% pokrycie kodu, ale nie dawać żadnej informacji o tym, czy program działa poprawnie i spełnia wymagania biznesowe.
Dlatego ważne jest sprawdzić, czy testy są w stanie wykryć błąd, gdy taki się pojawi.

Pytanie, które pokrycie kodu pomija, brzmi, *czy testy rzeczywiście wykryją błąd, gdy taki się pojawi?*
Odpowiedzi na nie udziela testowanie mutacyjne.
Zamiast mierzyć, ile kodu zostało uruchomione, sprawdza się, czy testy potrafią odróżnić poprawne zachowanie programu od zachowania błędnego.
Osiąga się to przez celowe wprowadzanie drobnych zmian w kodzie mutantów oraz obserwowanie, czy istniejący zestaw testów te zmiany wykrywa.
Jeżeli zmiana przechodzi niezauważona, jest to sygnał, że testy nie sprawdzają skutecznie tego fragmentu logiki.

Testowanie mutacyjne jest zatem narzędziem oceny "siły" testów, a nie tylko ich *zasięgu*.
Jego użyteczność wynika właśnie z tego, że zadaje pytanie z perspektywy błędu zamiast pytać "co zostało wykonane?", pyta "co zostałoby wykryte, gdyby coś poszło nie tak?".
Zanim jednak możliwe będzie przeprowadzenie takiej oceny, należy zdefiniować, czym dokładnie jest mutant i jak przebiega jego analiza.

Odpowiedź na to pytanie daje testowanie mutacyjne.
Zamiast sprawdzać, jaki procent kodu jest wykonywany, testowanie mutacyjne sprawdza, czy testy są w stanie odróżnić poprawne zachowanie programu od błędnego.
Co pozwala sprawdzić nie tylko poprawność testu, a też o ile dobrze przypadek testowy jest zdefiniowany.
Robi się to przez celowe wprowadzanie drobnych zmian w kodzie i sprawdzenie, czy testy te zmiany wykrywają.
Jeżeli zmiana nie zostanie wykryta, oznacza to, że testy nie są wystarczająco dobre.

Testowanie mutacyjne jest więc narzędziem, które pomaga ocenić, jak dobre są nasze testy, a nie tylko jaki jest ich zasięg.
Jego użyteczność wynika z tego, że pyta o to, co się stanie, gdy coś pójdzie nie tak, zamiast pytać, co zostało wykonane.
Aby móc przeprowadzić taką ocenę, trzeba najpierw zdefiniować, czym jest mutant i jak przebiega jego analiza.

### Czym jest mutant?

Mutant to specjalna wersja kodu, który powstaje przez wprowadzenie drobnej zmiany w oryginalnym kodzie.
Zmiana ta jest celowa i wynika z określonej reguły, która nazywa się operatorem mutacyjnym.
Definicja mutanta jest dość prosta, ale kryje w sobie kilka ważnych szczegółów.
- Po pierwsze, mutant różni się od oryginału tylko w jednym miejscu.
- Po drugie, zmiana jest celowa, a nie losowa. W klasycznym podejściu to określony operator mutacyjny.
- Po trzecie, mutant nie jest błędem, który występuje w systemie produkcyjnym, ale raczej sztuczną symulacją błędów, które mogą wystąpić w kodzie.
Z tego powodu symulacja ma być jak najbliżej podabna do prawdziwych błędów, żeby był sens używać testy mutacujne do oceniania jakości testów jednostowych.

Celem mutanta jest sprawdzenie, czy istniejące testy są w stanie wykryć błędy.
Typowe zmiany wprowadzane przez operatory mutacyjne to na przykład zamiana operatora `<` na `<=`, negacja warunku logicznego, usunięcie lub zastąpienia wywołania metody.
Każda z tych zmian symuluje inny rodzaj błędu i może pokazać słabość w zestawie testów.
Weryfikacja mutanta polega na uruchomieniu pełnego zestawu testów jednostkowych na zmutowanej wersji programu.
Jeśli co najmniej jeden test nie powiedzie się, mutant zostaje "zabity".
Jeśli wszystkie testy przejdą pomyślnie, mutant "przeżyje".
Przeżycie mutanta oznacza, że testy nie są wystarczająco dokładne w danym miejscu programu lub nawet niepoprawne.
Często jest to sygnałem, że testy nie sprawdzają odpowiednich wymagań kodu.
Wynik weryfikacji mutanta nie mówi nic o tym, czy kod jest poprawny, ale mówi, jak uważnie testy go obserwują.
Aby ocenić jakość testów, używa się metryki mutation score, która opisuje, jak mierzyć łączny wynik weryfikacji całego zbioru mutantów.

### Zabicie mutanta i mutation score

Gdy mutanty są wygenerowane, następuje ocena poprzez uruchomienie zbioru testów jednostkowych na zmodyfikowanym kodzie.
Na tym etapie sprawdzane jest, czy istniejące testy jednostkowe potrafią zidentyfikować, że w kodzie został wprowadzony defekt, który zmienia zachowanie programu.
Może to oznaczać, że mutant zawiera zarówno zmianę znaczącą, jak i prawie niewidoczną usterkę w kodzie.
Niezależnie od charakteru zmiany, jeżeli co najmniej jeden test zakończy się niepowodzeniem, oznacza to, że mutant został "zabity" (killed mutant).
Wskazuje to, że testy poprawnie reagują na modyfikacje w zachowaniu programu, które potencjalnie mogłyby być błędem w kodzie.

W innym przypadku, gdy testy jednostkowe nie wykryły zmian w kodzie, mutant jest klasyfikowany jako "przeżywający" (survived mutant).
Oznacza to, że testy nie wystarczająco pokrywają kod, albo nie sprawdzają odpowiednich wymagań lub zawierają błędy.
W każdym takim przypadku niewykrycia mutanta świadczy o słabości testów, co pozwala na estymację jakości zestawu testów oraz na wnioskowanie co do użycia produkcyjnego kodu, które te testy sprawdzają.

Dla liczbowej oceny efektywności zestawu testów w kontekście mutacyjnego testowania jest stosowana metryka - mutation score.
Metryka pozwala określić jaki procent mutantów, które udało się skompilować zostały zabite przez zbiór testów jednostkowych.

Dokładny wzór:
```
mutation score = liczba zabitych mutantów / liczba skompilowanych mutantów
```

Dla jasności można rozważyć przykład. Jeżeli podczas testowania wygenerowano 100 mutantów.
Spośród nich 20 nie skompilowało się i zostało wykluczonych ze zbioru mutantów.
Na pozostałych 80 mutantach wykonano testy oraz 60 spośród nich zostało zabitych, a 20 przeżyło.
W tym przypadku mutation score = 60 / 80 = 75%.
Ten wynik oznacza, że zestaw testów wychwytuje 75% symulowanych błędów.
Generalnie wyższy mutation score sugeruje lepszą skuteczność testów w wykrywaniu potencjalnych bugów.
Z kolei niższa wartość sugeruje, że testy mogą wymagać poprawy, ponieważ nie wykrywają symulowanych błędów w kodzie.

Trzeba jednak pamiętać, że mutation score nie jest jednoznacznym miernikiem jakości testów jednostkowych.
Należy odczytywać tę metrykę wyłącznie w kontekście wygenerowanych mutantów, od których całkiem zależą wyniki testowania mutacyjnego.
Na przykład duża liczba podobnych lub bardzo trywialnych mutantów może naprowadzić na błędne wyniki.
Do testów mutacyjnych trzeba podchodzić z ostrożnością, żeby poprawnie zinterpretować wyniki.

### Proces testowania mutacyjnego krok po kroku

> ✏️ **Wskazówka:** Lista numerowana — sekwencja od kodu źródłowego do raportu końcowego. Bez szczegółów implementacyjnych. Uwzględnij: generację mutantów → kompilację → uruchomienie testów → klasyfikację (killed/survived) → obliczenie mutation score. Opcjonalnie: prosty diagram przepływu.

*[Do napisania]*

---

### Koszty i problemy praktyczne

> ✏️ **Wskazówka:** Ta sekcja uzasadnia, dlaczego testowanie mutacyjne nie jest powszechnie stosowane w przemyśle. Każda podsekcja to osobny problem — połącz je na końcu krótkim akapitem podsumowującym.

#### Czas wykonania i narzut obliczeniowy

> ✏️ **Wskazówka:** Podaj rząd wielkości: dla projektu z N testami i M mutantami czas rośnie jak N×M. Przytoczyć można przykład z literatury lub własne obserwacje z Defects4J. Techniki przyspieszenia: równoległość, bytecode mutation (PIT).

*[Do napisania]*

#### Redukcja liczby mutantów (selektory, sampling)

> ✏️ **Wskazówka:** Dwa główne podejścia: (1) mutant sampling — losowe próbkowanie podzbioru mutantów; (2) selective mutation — ograniczenie do podzbioru operatorów. Krótko o badaniach pokazujących, że niewielki podzbiór operatorów wystarczy do uzyskania dobrego przybliżenia pełnego mutation score.

*[Do napisania]*

---

## Operatory mutacyjne w narzędziach klasycznych

> ✏️ **Wskazówka do rozdziału:** Rozdział skupia się wyłącznie na narzędziu PIT jako reprezentancie klasycznego podejścia do testowania mutacyjnego. Po przeczytaniu czytelnik powinien wiedzieć: czym jest PIT, jak generuje mutanty, jakie operatory zawiera katalog ALL i — co najważniejsze — jakie są jego ograniczenia. Ta ostatnia część jest bezpośrednim uzasadnieniem dla badania opisanego w rozdziale 6.

---

### Czym jest PIT i jak działa

> ✏️ **Wskazówka:** Krótki opis narzędzia: język Java, operuje na bytecode JVM (nie na kodzie źródłowym — to ważna właściwość), integracja z Maven/Gradle, generuje raporty HTML. Podkreśl, że PIT jest *de facto* standardem w testowaniu mutacyjnym dla Javy. 1–2 akapity.

*[Do napisania]*

---

### Model generacji mutantów w PIT

> ✏️ **Wskazówka:** Opisz jak PIT generuje mutanty: analiza bytecode → aplikacja reguły transformacji → zapis zmutowanej klasy. Nie wchodź w szczegóły JVM — wystarczy intuicja. Zaznacz, że operowanie na bytecode gwarantuje kompilację mutantów (co odróżnia PIT od generatorów tekstowych, np. LLM). Cecha istotna dla późniejszego porównania compile rate.

*[Do napisania]*

---

### Katalog operatorów: typy i przykłady

> ✏️ **Wskazówka:** Opisz kategorie operatorów w grupie ALL (zmiany warunków logicznych, operatorów arytmetycznych, wartości zwracanych, usunięcia wywołań). Dodaj tabelę z przykładami (wzór z oryginalnej pracy — tabela PIT operators). Każdą kategorię opisz jednym zdaniem. Cel: czytelnik musi wiedzieć co PIT potrafi, żeby rozumieć co to znaczy „NEW" operator w rozdziale 7.

| Operator PIT | Skrót | Przykład zmiany |
|---|---|---|
| Conditionals Boundary | CBM | `x < 5` → `x <= 5` |
| Negate Conditionals | NCM | `x == 0` → `x != 0` |
| Remove Conditionals | RCM | `if (cond)` → `if (true)` |
| Math | MTH | `a + b` → `a - b` |
| Increments | INR | `i++` → `i--` |
| Invert Negatives | INV | `return x` → `return -x` |
| Return Values | RTV | `return x` → `return 0` |
| Void Method Calls | VMC | `log.clear()` → *(usunięcie)* |
| Empty Returns | ERT | `return obj` → `return null` |
| False Returns | FRT | `return expr` → `return false` |
| True Returns | TRT | `return expr` → `return true` |
| Null Returns | NRT | `return obj` → `return null` |

*[Do uzupełnienia: ewentualnie rozszerzyć tabelę o dodatkowe operatory z grupy ALL po weryfikacji dokumentacji PIT]*

---

### Ograniczenia operatorów klasycznych

> ✏️ **Wskazówka:** To jest kluczowa sekcja uzasadniająca całe badanie. Pisz konkretnie — nie „PIT jest ograniczony", ale „PIT nie uwzględnia X, Y, Z". Zakończ wyraźnym stwierdzeniem: ta luka uzasadnia poszukiwanie innych źródeł reguł mutacyjnych.

#### Ograniczona różnorodność transformacji

> ✏️ **Wskazówka:** Katalog PIT ALL obejmuje ~12 operatorów — to skończony, statyczny zestaw reguł wybranych przez ekspertów. Porównaj z przestrzenią możliwych błędów: brakujące null-checki, błędy inicjalizacji, niepoprawna kolejność operacji, błędy obsługi wyjątków, problemy z współbieżnością — żadne z tych nie ma odpowiednika w ALL. Podaj liczby: ile operatorów ma PIT ALL vs ile klas błędów wyróżnia literatura (np. Defects4J taxonomy).

*[Do napisania]*

#### Niedopasowanie do błędów z praktyki

> ✏️ **Wskazówka:** Powołaj się na badania pokazujące, że operatory PIT nie odpowiadają rozkładowi rzeczywistych defektów (literatura: Andrews et al., Daran & Thévenod-Fosse, lub podobne). Wspomnij o koncepcji „realistic mutation operators" jako kierunku badań. To bezpośrednio prowadzi do pytania: czy LLM, trenowany na historii bugów, może generować realistyczniejsze mutanty?

*[Do napisania]*

---

## Duże modele językowe w inżynierii oprogramowania

> ✏️ **Wskazówka do rozdziału:** Rozdział wprowadza czytelnika w tematykę LLM z perspektywy inżynierii oprogramowania — nie z perspektywy teorii ML. Unikaj szczegółów architektury transformerów. Skup się na: czym są LLM w kontekście kodu, do czego są używane w SE, i — kluczowe dla pracy — jakie są ich możliwości i ograniczenia jako generatora zmian w kodzie.

---

### Czym są LLM?

> ✏️ **Wskazówka:** Dwa akapity: (1) intuicja — modele trenowane na ogromnych zbiorach tekstu (w tym kodu), modelują statystyczne zależności między tokenami; (2) kontekst do pracy — LLM „widział" miliardy linii kodu i historii bugów podczas treningu, co daje mu wiedzę o typowych wzorcach błędów. Wspomnij o kluczowych modelach: GPT-4, Claude, Gemini, CodeLlama. Odnieś się do Codex (Chen et al. 2021) jako pionierskiej pracy.

*[Do napisania]*

---

### LLM w pracy programisty: typowe zastosowania

> ✏️ **Wskazówka:** Lista 5–6 zastosowań z jednozdaniowym komentarzem każde: generowanie kodu (Copilot), APR (automatyczna naprawa błędów), code review, generowanie testów, analiza podatności, dokumentacja. Dla każdego podaj przykład narzędzia lub pracy naukowej. Cel: pokazać, że LLM są aktywnie stosowane w SE — to uzasadnia ich użycie w badaniu.

*[Do napisania]*

---

### LLM jako generator zmian w kodzie

> ✏️ **Wskazówka:** To jest bezpośrednie tło dla Twojego eksperymentu. Opisz koncepcję: LLM jako „generator hipotez mutacyjnych" — model dostaje kontekst kodu + instrukcję i zwraca zmodyfikowany fragment + opis reguły. Kluczowa zaleta: reguła jest indukcyjna (wynika z wzorców w danych), a nie ręcznie specyfikowana. Wspomnij o wcześniejszych pracach stosujących LLM do generowania mutantów (MutationGPT, ChatMut — jeśli dostępne w literaturze).

*[Do napisania]*

---

### Ryzyka i ograniczenia LLM (z perspektywy jakości kodu)

> ✏️ **Wskazówka:** Wyważ obraz — LLM mają istotne ograniczenia istotne dla Twojego badania. Omów: (1) niedeterminizm — różne wyniki dla tego samego wejścia, problemy z reprodukowalnością; (2) halucynacje — generowanie nieskompilowanego lub semantycznie niepoprawnego kodu; (3) brak gwarancji realizmu — wygenerowana zmiana może być arbitralna, nie symulować prawdziwego błędu; (4) zależność od jakości promptu. Zaznacz, że protokół eksperymentu (filtracja, walidacja kompilacji) adresuje te ograniczenia.

*[Do napisania]*

---

## Dane eksperymentalne i metryki

Zanim jednak przejdzie się do opisu eksperymentu, warto odpowiedzieć na pytanie: jak w ogóle ocenić, czy mutanty wygenerowane przez LLM są *lepsze* od klasycznych?
Odpowiedź wymaga punktu odniesienia, zbioru prawdziwych błędów, względem którego można mierzyć realizm mutantów, oraz precyzyjnych wskaźników porównawczych.
W niniejszym rozdziale najpierw zostanie przedstawiony zbiór defectów, a potem wyjaśnienie, jak mierzyć podobieństwo mutanta do rzeczywistego defektu na podstawie profili testowych oraz definicja zestawu metryk.

### Zbiór rzeczywistych błędów

W badaniach nad jakością oprogramowania często potrzebny jest zbiór udokumentowanych, rzeczywistych błędów, które faktycznie pojawiły się w kodzie produkcyjnym, zostały zgłoszone i naprawione przez programistów.
Takie zbiory nazywane są repozytoriami bugów (*bug benchmarks* lub *bug repositories*) i różnią się od zwykłych zestawów testów tym, że dla każdego błędu przechowują trzy elementy.
Pierwszym jest wersja kodu przed naprawą (*buggy version*), zawierająca defekt w oryginalnej postaci.
Drugim jest wersja kodu po naprawie (*fixed version*), w której defekt został usunięty.
Trzecim są testy wyzwalające (*triggering tests*), które nie przechodzą dla wersji z błędem, lecz przechodzą po jego naprawie i tym samym bezpośrednio wskazują na obecność defektu.
Dzięki tej strukturze możliwe jest precyzyjne odtwarzanie zachowania programu w obecności błędu i porównywanie go z zachowaniem wygenerowanego mutanta.
Warto podkreślić, że testy wyzwalające stanowią jedynie podzbiór wszystkich testów projektu, obejmujący wyłącznie te, które są bezpośrednio powiązane z danym defektem.

Źródłem danych w niniejszym badaniu jest  **Defects4J** [5], jako najszerzej stosowany benchmark dla Javy w badaniach nad jakością testów.

Defects4J 2.0 to zbiór błędów z projektów Java open-source.
Dla każdego błędu dostępna jest para wersji kodu (*buggy* i *fixed*) możliwa do pobrania narzędziem wiersza poleceń, lista zmodyfikowanych klas wskazująca dokładnie, które pliki uległy zmianie podczas naprawy, zestaw nazw testów wyzwalających oraz możliwość automatycznej kompilacji i uruchomienia testów bez żadnej ręcznej ingerencji.

| Projekt              | Dziedzina                 | Liczba błędów |
|----------------------|---------------------------|---------------|
| Apache Commons Math  | Biblioteka matematyczna   | 106           |
| Apache Commons Lang  | Narzędzia dla klas Java   | 65            |
| Jsoup                | Parser HTML               | 93            |
| Closure Compiler     | Kompilator JavaScript     | 133           |
| Mockito              | Biblioteka do mockowania  | 38            |
| JFreeChart           | Biblioteka wykresów       | 26            |
| Joda-Time            | Obsługa dat i czasu       | 27            |
| Apache Commons CLI   | Parsowanie argumentów CLI | 39            |
| Apache Commons Codec | Kodeki danych             | 18            |
| Apache Commons CSV   | Obsługa plików CSV        | 16            |
| Gson                 | Serializacja JSON         | 18            |
| JacksonCore          | Parsowanie JSON           | 26            |
| **Razem**            |                           | **605**       |

Wybrane projekty reprezentują szerokie spektrum dziedzin, od bibliotek narzędziowych (Commons Lang, Commons Math), przez parsery (Jsoup, Gson, JacksonCore), aż po kompilatory (Closure Compiler).
Różnorodność dziedzin zapewnia, że wyniki nie są specyficzne dla jednego rodzaju kodu i mogą stanowić podstawę wniosków ogólniejszej natury.
Ze względu na koszty wywołań interfejsu API modelu językowego i czas uruchomienia testów, spośród dostępnych błędów wybierana jest reprezentatywna próba spełniająca zdefiniowane kryteria selekcji.

### Rodzaje mutantów

Dla przeprowadzenia badania trzeba zdefiniować rodzaje mutantów, na podstawie których będą liczone metryki dla odpowiedzi na tezy badawcze.

#### Compilable mutants

Mutant kompilowany to wersja kodu, dla której po wprowadzeniu mutacji przechodzi poprawnie etap kompilacji.
Oznacza to brak błędów strukturalnych, syntaktycznych, niezgodności typów oraz brakujących symboli, które uniemożliwiałyby uruchomienie testów na zmodyfikowanym kodzie.
W badaniu wszystkie wygenerowane mutanty, jak klasyczne tak i wygenerowane przez LLM, są poddawane próbie kompilacji w konfiguracji projektu.
Mutanty niekompilowane nie będą uczestniczyć w analizie, ponieważ jest niemożliwe uruchomić testy na tych mutantach.

Metryka jest zdefiniowana jako liczba mutantów, które można skompilować, podzielona przez całkowitą liczbę wygenerowanych mutantów.
```
Compilability Mutation Rate (CMR) = liczba mutantów, które można skompilować / liczba wygenerowanych mutantów
```

Ta metryka będzie używana do obliczenia liczby mutantów możliwych do użycia w testowaniu, ponieważ LLM nie może gwarantować poprawnej generacji mutantów.
Będzie to potrzebne do oceniania stabilności generowania mutantów przez LLM, a także do porównania z klasycznymi mutantami, które charakteryzują się bardzo wysoką kompilowalnością lub 100% dla niektórych klasycznych narzędzi.

#### Duplicate mutants

Mutant zduplikowany to mutant, który syntaktycznie jest identyczne z innym mutantem albo z oryginalnym kodem.
Takie mutanty nie wprowadzają nowego zachowania i nie wnoszą nowych danych do analizy, ponieważ ich efekt został już uwzględniony.
Przed obliczaniem metryk usuwa się je ze zbioru, aby nie zawyżały wyników niektórych metryk.

Algorytm identyfikacji duplikatów polega na porównaniu reprezentacji kodu wygenerowanego mutanta po normalizacji z oryginalnym kodem oraz juź istniejącymi mutantami.
Jeżeli dwie reprezentacje mutantów są identyczne względem siebie, oba mutanty traktowane są jako duplikaty tej samej modyfikacji.
Jeżeli mutant jest identyczny z oryginałem, oznacza się go jako duplikat.
Po ich usunięciu pozostaje zbiór mutantów unikalnych, który stanowi podstawę do obliczania dalszych metryk.

```
Duplication Mutation Rate (DMR) = liczba mutantów zduplikowanych / liczba mutantów kompilowalnych
```

Wskaźnik ten pokazuje, jaki odsetek mutantów kompilowanych stanowią duplikaty.

#### Equivalent mutants

Mutant ekwiwalentny to mutant, który mimo różnic syntaktycznych zachowuje się w taki sam sposób jak oryginalny kod.
Oznacza to, że żaden test nie jest w stanie wykryć wprowadzonej zmiany, ponieważ nie prowadzi ona do obserwowalnej różnicy w zachowaniu kodu.
Nie istnieje uniwersalny algorytm rozpoznanie duplikatów, bo ten problem jest nierozstrzygalny w ogólnym przypadku, dlatego w analizie będą stosowane przybliżone metryki oparte na wynikach testów.
Za mutanty ekwiwalentne uznaje się mutanty kompilowane i niezduplikowane, które przeżywają cały dostępny zestaw testów.
Podejście daje wyniki przybliżone, bo mutanty mogą przeżywać testy z powodu ich niedostatecznego pokrycia, a nie faktycznej ekwiwalentności semantycznej.
Choć takie podejście nie daje dokładnych wyników, ale pozwala porównać efektywność generacji mutantów, co w naszym przypadku jest wystarczające.

```
Equivalent Mutation Rate (EMR) = liczba mutantów przeżywających / (liczbę mutantów kompilowalnych - liczbę duplikatów)
```

### Metryki i kryteria oceny

Ocena wygenerowanych mutantów prowadzona na podstawie trzech kluczowych metryk: różnorodności operatorów względem narzędzi klasycznych, podobieństwa mutantów do rzeczywistych defektów oraz jakości i kosztu procesu generowania.

#### LLM New Mutant Rate

*LLM New Mutant Rate* (LNMR) mierzy, jaka część użytecznych mutantów LLM nie ma odpowiednika wśród mutantów klasycznych.
Wskaźnik pozwala ocenić, czy model językowy generuje typy zmian w kodzie nieobecne w klasycznym katalogu operatorów mutacyjnych.
Mutant LLM uznaje się za nowy, gdy spełnia jednocześnie dwa warunki: nie powtarza żadnej zmiany wprowadzonej przez klasyczny generator w tej samej lokalizacji kodu (brak odpowiednika syntaktycznego) oraz wywołuje inny zestaw nieprzechodzących testów niż każdy mutant klasyczny (brak odpowiednika w profilu testowym).

```
LNMR = liczba użytecznych mutantów LLM bez odpowiednika wśród mutantów klasycznych / liczba wszystkich użytecznych mutantów LLM
```

Wysoka wartość wskaźnika oznacza, że LLM generuje mutanty nieobecne w katalogu klasycznym; niska, że generowane zmiany w znacznej mierze pokrywają się z istniejącymi operatorami klasycznymi.

#### Real Bug Detection Rate

*Real Bug Detection Rate* (RBDR) mierzy, jaka część defektów ze zbioru analizowanych defektów jest pokryta przez co najmniej jeden wygenerowany mutant pod względem zachowania programu.
Podstawą oceny jest porównanie dwóch zestawów testów.
Profilu niepowodzeń mutanta, czyli zbioru testów, które nie przeszły po wprowadzeniu mutacji.
Profilu defektu, czyli zbioru testów, które nie przechodzą dla wersji programu z błędem, lecz przechodzą po jego naprawie.
Mutant uznaje się za powiązany z defektem, jeśli powoduje niepowodzenie przynajmniej jednego testu wchodzącego w skład profilu tego defektu.
Przykładowo, jeśli dany defekt jest wykrywany przez testy T1 i T2, a istnieje mutant powodujący niepowodzenie testu T1, defekt ten uznaje się za wykryty.

```
RBDR = liczba defektów wykrytych przez co najmniej jeden mutant / liczba wszystkich analizowanych defektów
```

Wysoka wartość RBDR oznacza, że dla wielu rzeczywistych defektów istnieją mutanty wywołujące niepowodzenie tych samych testów, a zatem wygenerowane mutanty mogą skutecznie odzwierciedlać rzeczywiste błędy i być użyteczne w testowaniu.

#### Average Ochiai Rate

*Average Ochiai Rate* (AOR) mierzy, jak bardzo profil niepowodzeń mutanta pokrywa się z profilem danego defektu.
Im więcej testów wyzwalających defekt pojawia się wśród testów, które nie przeszły po wprowadzeniu mutacji, tym wyższa wartość wskaźnika.
Obliczenie przebiega trójstopniowo: najpierw dla każdej pary mutant–defekt wyznacza się wartość współczynnika Ochiai, następnie uśrednia się ją po wszystkich mutantach przypisanych do danego defektu, a na końcu uśrednia się wyniki po wszystkich defektach, uzyskując jedną globalną wartość dla porównywanego podejścia.

```
Ochiai(mutant, defekt) = liczba wspólnych testów nieprzechodzących / pierwiastek z (liczba testów nieprzechodzących mutanta × liczba testów wykrywających defekt)

AOR = średnia wartość Ochiai uśredniona po wszystkich defektach
```

W odróżnieniu od RBDR, który odpowiada binarnie na pytanie, czy mutant w ogóle pokrywa dany defekt, AOR wyraża stopień tego pokrycia.
Wyższa wartość oznacza, że mutanty wywołują niepowodzenie większej części testów charakterystycznych dla rzeczywistego błędu.

#### Coupling Rate

*Coupling Rate* (CR) mierzy, jaki odsetek użytecznych mutantów jest połączony z odpowiadającym defektem, to znaczy powoduje niepowodzenie przynajmniej jednego testu wyzwalającego.
W odróżnieniu od RBDR, który ocenia pokrycie od strony defektów, CR przyjmuje perspektywę mutantów i odpowiada na pytanie, ile spośród nich rzeczywiście dotyka obszaru kodu związanego z danym defektem.
Oblicza się go jako stosunek liczby mutantów posiadających niepuste przecięcie z testami wyzwalającymi do łącznej liczby użytecznych mutantów.

```
CR = liczba mutantów powiązanych z co najmniej jednym testem wyzwalającym / liczba użytecznych mutantów
```

RBDR, AOR i CR uzupełniają się wzajemnie i interpretuje się je łącznie.
Niski wynik któregokolwiek z nich może wynikać z niedostatecznego pokrycia testowego w otoczeniu defektu, a nie ze słabości samych mutantów.

#### Average Mutant Generation Time

*Average Mutant Generation Time* (AMGT) opisuje koszt czasowy wytworzenia jednego mutanta.
Dla LLM jest to czas od wysłania zapytania do interfejsu API do uzyskania pełnej odpowiedzi lub generacji lokalnie w przypadków lokalnych modeli.
Dla klasycznych mutantów jest to łączny czas przebiegu narzędzia podzielony przez liczbę wygenerowanych mutantów.

```
AMGT = łączny czas generacji / liczba wszystkich wygenerowanych mutantów
```

AMGT umożliwia bezpośrednie porównanie szybkości obu podejść w tej samej skali, niezależnie od rozmiarów eksperymentu.

#### Cost per Useful Mutant

*Cost per Useful Mutant* (CPUM) łączy czas generacji do liczby mutantów pozwalających na ocenianie testów (kompilowalnych i niezduplikowanych).
Uwzględnia tym samym straty ponoszone na generację mutantów.
W przeciwieństwie do AMGT, który mierzy koszt każdego wygenerowanego mutanta, CPUM odzwierciedla efektywny koszt produkcji mutantów użytecznych.

```
CPUM = łączny czas generacji / liczba mutantów kompilowalnych i niezduplikowanych
```

### Cel pracy i pytania badawcze

Celem niniejszej pracy jest weryfikacja, czy duże modele językowe (*Large Language Models*, LLM) są w stanie generować operatory mutacyjne różnorodniejsze i bliższe rzeczywistym defektom oprogramowania niż operatory dostępne w klasycznym generatorze mutantów, a także ocena kosztów i ograniczeń podejścia opartego na LLM.

Badanie odpowiada na trzy pytania badawcze:

**RQ1 - Jaki odsetek mutantów LLM nie ma odpowiednika wśród mutantów klasycznych?**

Pytanie dotyczy różnorodności: czy LLM w ogóle wykracza poza znany katalog klasycznych operatorów mutacyjnych.
Odpowiada na nie wskaźnik *LLM New Mutant Rate* (LNMR), który mierzy proporcję użytecznych mutantów LLM nieposiadających odpowiednika ani pod względem syntaktycznym, ani pod względem profilu testowego wśród mutantów klasycznych.
Wysoka wartość LNMR oznacza, że LLM generuje typy zmian niedostępne w katalogu klasycznym, co jest warunkiem koniecznym do uzasadnienia stosowania LLM jako uzupełnienia narzędzi klasycznych.

**RQ2 - Czy mutanty LLM są bliższe rzeczywistym defektom pod względem zachowania programu niż mutanty klasyczne?**

Pytanie dotyczy realizmu: czy mutanty LLM wywołują niepowodzenia testów podobne do tych, które wywołuje rzeczywisty błąd.
Odpowiadają na nie trzy wskaźniki. *Real Bug Detection Rate* (RBDR) mierzy, jaki odsetek analizowanych defektów jest pokryty przez co najmniej jeden mutant w zakresie profilu testowego.
*Average Ochiai Rate* (AOR) wyraża stopień pokrycia profilu defektu przez profil mutanta jako ciągłą miarę podobieństwa.
*Coupling Rate* (CR) mierzy, jaki odsetek wszystkich użytecznych mutantów powoduje niepowodzenie przynajmniej jednego testu wyzwalającego.
Łączna analiza RBDR, AOR i CR pozwala ocenić, które z podejść generuje mutanty lepiej imitujące realistyczne defekty oprogramowania.

**RQ3 - Jak LLM wypada w porównaniu z klasycznym generatorem pod względem jakości i kosztu generowania mutantów?**

Pytanie dotyczy efektywności: ile kosztuje uzyskanie mutanta zdatnego do testowania i jak duży jest odsetek mutantów odrzuconych w trakcie filtracji.
Odpowiadają na nie wskaźniki jakości procesu: *Compilability Mutation Rate* (CMR), *Duplication Mutation Rate* (DMR) i *Equivalent Mutation Rate* (EMR) opisują kolejno odsetek mutantów, które przeszły kompilację, odsetek duplikatów syntaktycznych oraz odsetek mutantów przeżywających pełny zestaw testów.
Wskaźniki kosztowe: *Average Mutant Generation Time* (AMGT) i *Cost per Useful Mutant* (CPUM), mierzą odpowiednio średni czas wytworzenia jednego mutanta i efektywny koszt uzyskania jednego mutanta zdatnego do testowania z uwzględnieniem strat na etapie filtracji.

Poniższa tabela zbiera wszystkie wskaźniki w formie zestawienia:

| Metryka                        | Skrót | Co mierzy                                                                    | Powiązane RQ |
|--------------------------------|-------|------------------------------------------------------------------------------|--------------|
| LLM New Mutant Rate            | LNMR  | Odsetek użytecznych mutantów LLM bez odpowiednika wśród mutantów klasycznych | RQ1          |
| Real Bug Detection Rate        | RBDR  | Odsetek defektów pokrytych przez co najmniej jeden mutant                    | RQ2          |
| Average Ochiai Rate            | AOR   | Stopień pokrycia profilu defektu przez profil niepowodzeń mutanta            | RQ2          |
| Coupling Rate                  | CR    | Odsetek mutantów z niepustym przecięciem z testami wyzwalającymi             | RQ2          |
| Compilability Mutation Rate    | CMR   | Odsetek wygenerowanych mutantów, które przeszły kompilację                   | RQ3          |
| Duplication Mutation Rate      | DMR   | Odsetek duplikatów syntaktycznych wśród kompilowalnych mutantów              | RQ3          |
| Equivalent Mutation Rate       | EMR   | Odsetek mutantów przeżywających pełny zestaw testów                          | RQ3          |
| Average Mutant Generation Time | AMGT  | Średni czas wytworzenia jednego mutanta                                      | RQ3          |
| Cost per Useful Mutant         | CPUM  | Efektywny koszt uzyskania jednego mutanta zdatnego do testowania             | RQ3          |

Pytania badawcze są wzajemnie uzupełniające: RQ1 bada różnorodność, RQ2 bada realizm, RQ3 bada koszt.
Pełna ocena podejścia LLM wymaga uwzględnienia wszystkich trzech wymiarów: wysoka różnorodność i realizm przy akceptowalnym koszcie uzasadniałyby stosowanie LLM jako uzupełnienia klasycznych generatorów mutantów.

## Założenia eksperymentu i metodyka

Niniejszy rozdział opisuje, w jaki sposób przeprowadzono badanie empiryczne: jakie dane wybrano, jak generowano mutanty przez model językowy i przez PIT, jak weryfikowano ich poprawność oraz jak definiuje się mutanta nowego względem PIT. Wszystkie wskaźniki oceny zostały zdefiniowane w rozdziale 5 — tutaj podano wyłącznie procedury operacyjne służące do ich wyznaczenia.

---

### Przebieg eksperymentu

Eksperyment składa się z pięciu etapów wykonywanych kolejno dla każdego analizowanego błędu.

**Etap 1 — Dobór błędów.** Ze zbioru Defects4J 2.0 wybierane są błędy spełniające kryteria opisane w sekcji 7.2. Wynik: lista par *projekt + numer błędu*.

**Etap 2 — Generacja mutantów.** Dla każdego błędu wygenerowane są mutanty dwiema metodami: przez model językowy (LLM) i przez narzędzie PIT — obie na tej samej wersji kodu. Szczegóły opisano w sekcji 7.3.

**Etap 3 — Weryfikacja i zebranie wyników.** Każdy mutant LLM jest kompilowany; skompilowane mutanty obu źródeł przechodzą pełny przebieg testów. Profil niepowodzeń każdego mutanta jest porównywany z profilem oryginalnego błędu. Szczegóły opisano w sekcji 7.4.

**Etap 4 — Identyfikacja nowych mutantów.** Każdy skompilowany mutant LLM jest porównywany z mutantami PIT na podstawie dwóch filtrów: syntaktycznego i testowego. Mutanty, które nie mają odpowiednika w PIT według obu kryteriów, uznawane są za nowe. Definicja opisana jest w sekcji 7.5.

**Etap 5 — Obliczenie wskaźników i analiza.** Na podstawie zgromadzonych danych obliczane są wskaźniki zdefiniowane w sekcji 7.6. Wyniki zestawiane są osobno dla mutantów LLM i PIT i analizowane w odniesieniu do pytań badawczych RQ1–RQ3.

---

### Materiał badawczy — zbiór danych i kryteria doboru

Podstawą badania jest zbiór **Defects4J 2.0** — powszechnie stosowany w badaniach nad testowaniem oprogramowania zestaw rzeczywistych błędów z projektów open-source pisanych w Javie. Każdy błąd jest opatrzony wersją kodu sprzed naprawy (*buggy*), wersją po naprawie (*fixed*), pełnym zestawem testów regresyjnych i zestawem testów wyzwalających — odróżniających kod błędny od poprawionego. Dzięki temu można zmierzyć, czy wygenerowany mutant zachowuje się podobnie do prawdziwego defektu.

Ze względu na koszty generacji przez model językowy i czas potrzebny na uruchomienie testów, z pełnego zbioru wybierana jest ograniczona liczba błędów z kilku projektów. Finalna lista przedstawiona jest w poniższej tabeli.

| Projekt | Dziedzina | Liczba analizowanych błędów |
|---|---|---|
| Lang | Narzędzia języka Java | [do uzupełnienia] |
| Math | Matematyka numeryczna | [do uzupełnienia] |
| Chart | Wizualizacja danych | [do uzupełnienia] |
| Closure | Kompilator JavaScript | [do uzupełnienia] |
| Mockito | Biblioteka do testów | [do uzupełnienia] |
| **Razem** | — | **[do uzupełnienia]** |

Aby błąd mógł zostać uwzględniony w badaniu, musi spełniać wszystkie cztery warunki:

1. **Kod wersji naprawionej kompiluje się bez błędów** — warunek konieczny do generowania mutantów.
2. **Istnieje co najmniej jeden test wyzwalający** — bez niego nie można mierzyć podobieństwa mutanta do błędu.
3. **Pełny przebieg testów zajmuje mniej niż 10 minut** — przy wielu tysiącach mutantów dłuższe testy czyniłyby eksperyment nierealistycznym.
4. **Błąd dotyczy co najwyżej trzech plików Java** — upraszcza kontekst przekazywany modelowi i zapewnia spójność analizy.

---

### Generacja mutantów — LLM i PIT

Dla każdego wybranego błędu mutanty generowane są dwiema metodami na tej samej wersji kodu (*fixed*). Dane wyjściowe obu metod zapisywane są w ujednoliconym formacie — każdy mutant rejestruje: identyfikator, źródło (LLM lub PIT), projekt i numer błędu, plik i lokalizację w kodzie, treść zmiany w formacie diff, wynik kompilacji (z przyczyną błędu w przypadku niepowodzenia), listę nieprzechodzących testów, czy mutant został zabity oraz czas weryfikacji.

**Generacja przez model językowy.** Do modelu przekazywane jest polecenie (*prompt*) złożone z: (1) instrukcji — model ma generować subtelne zmiany w jednej linii kodu naśladujące realistyczne błędy programistyczne; (2) pełnej metody Java z miejscem naprawy; (3) kilku przykładów rzeczywistych błędów z niezależnego zbioru, ilustrujących różne typy zmian; (4) oczekiwanej liczby mutantów proporcjonalnej do długości metody. Model zwraca listę propozycji w formacie JSON: numer linii, linia przed zmianą, linia po zmianie, jednozdaniowy opis reguły. Parametry generacji (temperatura, ustawienia losowości) są ustalane raz i stosowane do wszystkich wywołań.

**Generacja przez PIT.** PIT uruchamiany jest z pełnym zestawem operatorów (grupa ALL, 29 operatorów) na tych samych klasach, które były kontekstem dla modelu językowego — zapewnia to porównywalność obu podejść. PIT generuje wyłącznie mutanty skompilowane poprawnie (działa na poziomie kodu bajtowego). Wyniki konwertowane są do tego samego formatu rekordu co mutanty LLM.

---

### Weryfikacja mutantów i zbieranie wyników

Przed uruchomieniem testów każda propozycja mutanta LLM przechodzi trzy etapy filtracji:

1. **Parsowanie odpowiedzi** — sprawdzenie, czy JSON zawiera wszystkie wymagane pola; odpowiedzi niekompletne są odrzucane i rejestrowane.
2. **Usunięcie duplikatów syntaktycznych** — jeśli dwa mutanty wprowadzają identyczną zmianę w tej samej linii tego samego pliku, jeden z nich jest pomijany jeszcze przed kompilacją.
3. **Kompilacja** — zmiana jest aplikowana do kodu i projekt jest kompilowany; mutanty, których kod nie kompiluje się, są odrzucane z zapisem przyczyny błędu (niezgodność typów, brakująca metoda, błąd składniowy itp.). Po kompilacji kod jest natychmiast przywracany.

Dla każdego mutanta, który przeszedł kompilację (LLM i PIT), wykonywana jest identyczna procedura:

1. Przygotowywana jest izolowana kopia robocza projektu (wersja *fixed*).
2. Do kopii wprowadzana jest zmiana mutanta.
3. Uruchamiany jest pełny zestaw testów — zapisywana jest lista testów, które nie przeszły (*profil niepowodzeń mutanta*).
4. Oddzielnie gromadzony jest profil niepowodzeń oryginalnego błędu.
5. Na podstawie obu profili obliczany jest wskaźnik Ochiai (szczegóły w sekcji 7.6).
6. Kopia robocza jest usuwana — kolejny mutant weryfikowany jest w czystym środowisku.

Każde uruchomienie testów ma określony limit czasu; jego przekroczenie rejestrowane jest osobno jako oddzielna kategoria odrzucenia.

---

### Definicja mutanta nowego względem PIT

Zamiast grupować mutanty LLM w klastry i porównywać grupy z katalogiem PIT, stosuje się prostszą i przejrzystą definicję opartą na dwóch filtrach stosowanych do każdego mutanta z osobna.

**Mutant LLM uznaje się za nowy względem PIT, jeżeli spełnia oba poniższe warunki jednocześnie:**

1. **Filtr syntaktyczny** — mutant nie odpowiada żadnemu mutantowi PIT wygenerowanemu dla tego samego błędu na poziomie transformacji kodu: żaden mutant PIT nie wprowadza identycznej zmiany (ta sama linia, ta sama modyfikacja) w tym samym pliku.

2. **Filtr testowy** — mutant nie wykazuje tego samego profilu testów nieprzechodzących, co którykolwiek mutant PIT wygenerowany dla tego samego błędu: żaden mutant PIT nie powoduje niepowodzenia dokładnie tego samego zestawu testów.

Mutant spełniający oba warunki nie ma odpowiednika w PIT ani syntaktycznie, ani pod względem profilu testowego — jest to operacyjna i weryfikowalna definicja nowości, niezależna od arbitralnych progów klasyfikacji. Mutanty, które spełniają tylko jeden z warunków, są traktowane jako *częściowo pokryte przez PIT* i analizowane osobno.

---

## Analiza wyników i wnioski

Niniejszy rozdział łączy wyniki eksperymentu z ich interpretacją i bezpośrednimi odpowiedziami na pytania badawcze. Dla każdego pytania (RQ1–RQ3) przedstawiono dane liczbowe, omówiono ich znaczenie, a następnie sformułowano jednoznaczną odpowiedź. Rozdział zamykają synteza porównawcza LLM vs PIT, ograniczenia badania oraz kierunki dalszych prac.

---

### Statystyki ogólne eksperymentu

*[Do uzupełnienia po eksperymencie]*

| Statystyka | Wartość |
|---|---|
| Liczba projektów | |
| Liczba analizowanych błędów (N) | |
| Liczba mutantów LLM łącznie (A_LLM) | |
| Liczba mutantów PIT łącznie (A_PIT) | |
| Mutanty LLM — skompilowane (C_LLM) | |
| Mutanty PIT — skompilowane (C_PIT) | |
| Mutanty LLM — unikalne po dedup. (C_LLM − D_LLM) | |
| Mutanty PIT — unikalne po dedup. (C_PIT − D_PIT) | |
| Mutanty LLM — zabite | |
| Mutanty PIT — zabite | |
| Liczba wyznaczonych operatorów LLM | |
| Łączny czas eksperymentu | |

*[Komentarz: jedno lub dwa zdania — czy skala eksperymentu odpowiada założeniom z rozdziału 7 i czy wystąpiły jakiekolwiek odstępstwa.]*

---

### RQ1 — Różnorodność i nowość operatorów LLM

**Pytanie:** Jaki odsetek operatorów mutacyjnych indukowanych przez LLM nie ma odpowiednika w katalogu PIT ALL?

**Hipoteza:** LLM indukuje reguły mutacyjne wykraczające poza statyczny katalog 12 operatorów PIT ALL — spodziewamy się, że co najmniej połowa operatorów zostanie sklasyfikowana jako NEW lub PARTIAL.

*[Do uzupełnienia po eksperymencie]*

| Etykieta | Liczba operatorów | % wszystkich operatorów LLM |
|---|---|---|
| NEW (brak odpowiednika w PIT ALL) | | |
| PARTIAL (częściowe pokrycie przez PIT) | | |
| EXISTING (pełny odpowiednik w PIT ALL) | | |
| **Razem** | | **100%** |

Przykłady operatorów sklasyfikowanych jako NEW:

| Nazwa operatora LLM | Opis reguły | Przykładowy diff | Liczba mutantów w klastrze |
|---|---|---|---|
| *[np. NULL_CHECK_REMOVAL]* | *[usunięcie warunku sprawdzającego null przed użyciem referencji]* | `if (x != null) { ... }` → `{ ... }` | |
| *[np. EXCEPTION_SWALLOW]* | *[zamiana bloku catch rzucającego wyjątek na pusty blok]* | `catch (E e) { throw e; }` → `catch (E e) {}` | |

> ✏️ **Wskazówka do interpretacji:** (1) Czy wyniki potwierdzają hipotezę? (2) Co oznacza wysoki/niski odsetek NEW — czy LLM generuje sensowne nowe błędy, czy egzotyczne zmiany bez praktycznego znaczenia? (3) Czy operatory PARTIAL poszerzają zakres znanych operatorów, czy jedynie duplikują je częściowo? (4) Odnieś się do literatury (MutationGPT, ChatMut) jeśli dostępne.

*[Interpretacja: do napisania po eksperymencie]*

**Odpowiedź na RQ1:** LLM indukuje X% operatorów sklasyfikowanych jako NEW i Y% jako PARTIAL, co oznacza, że [łącznie / w przeważającej mierze] podejście LLM wykracza poza statyczny katalog PIT. Spośród operatorów NEW najczęściej reprezentowane były błędy dotyczące *[obsługi wyjątków / inicjalizacji / logiki warunkowej z efektami ubocznymi]* — typów defektów niemających odpowiednika wśród operatorów PIT ALL. Dla projektów, w których priorytetem jest symulacja realistycznych defektów domenowych, warto uzupełnić PIT o wywołania LLM.

---

### RQ2 — Podobieństwo mutantów do defektów rzeczywistych

**Pytanie:** Czy mutanty LLM są bliższe rzeczywistym defektom z Defects4J pod względem zachowania programu niż mutanty PIT — mierzone wskaźnikami RBDR, Ochiai i Coupling Rate?

**Hipoteza:** Mutanty LLM, jako pochodne wiedzy o historii bugów, wykazują wyższy średni współczynnik Ochiai i wyższe RBDR niż mutanty PIT.

*[Do uzupełnienia po eksperymencie]*

| Statystyka | LLM | PIT |
|---|---|---|
| RBDR (Real Bug Detection Rate) | | |
| Coupling Rate | | |
| Mediana Ochiai | | |
| Średnia Ochiai | | |
| Odchylenie standardowe Ochiai | | |
| Q1 / Q3 Ochiai | | |
| Odsetek mutantów z Ochiai > 0.5 | | |
| Test Mann-Whitney U (p-value) | | |
| Mutation score | | |

> ✏️ **Wskazówka do interpretacji:** (1) Czy mediana Ochiai LLM > PIT? Czy różnica jest istotna statystycznie? (2) Czy wysoki mutation score PIT wynika z trywialnych mutantów, a nie z wyższego realizmu? (3) Dla których projektów LLM wypada lepiej? (4) Przywołaj RBDR = 40,1% dla PIT z literatury [1] i porównaj z wynikami własnymi.

*[Interpretacja: do napisania po eksperymencie]*

**Odpowiedź na RQ2:** Mutanty LLM osiągają RBDR = X% wobec Y% dla PIT oraz medianę Ochiai A wobec B (test Mann-Whitney: p = …), co oznacza, że LLM [jest / nie jest] statystycznie bliżej rzeczywistych defektów Defects4J. Coupling Rate dla LLM wynosi C% wobec D% dla PIT. Wyższy mutation score PIT wynika prawdopodobnie z obecności mutantów trywialnych, co nie przekłada się na wyższy realizm. Jeśli celem jest ocena siły testów względem typowych błędów programistycznych, mutanty LLM dostarczają bardziej informatywnego sygnału niż ogólna miara mutation score.

---

### RQ3 — Koszty i wydajność podejścia

**Pytanie:** Jak LLM wypada w porównaniu z PIT pod względem wskaźnika kompilowalności, odsetka duplikatów i czasu generacji mutantów?

**Hipoteza:** LLM generuje mutanty drożej (czas, koszt API) i z większym odpadkiem (niższy compile rate, więcej duplikatów) niż deterministyczny PIT.

*[Do uzupełnienia po eksperymencie]*

| Metryka | LLM | PIT |
|---|---|---|
| Compilability Rate (CR) | | 100% |
| Duplicate Rate (DR) | | |
| Średni czas generacji mutanta [s] | | |
| Koszt jednego użytecznego mutanta [s] | | |
| Koszt API na jeden użyteczny mutant [USD] | | N/A |

Rozkład przyczyn błędów kompilacji mutantów LLM:

| Przyczyna błędu kompilacji | Liczba | % błędnych |
|---|---|---|
| Niezgodność typów | | |
| Odwołanie do nieistniejącej metody/pola | | |
| Błąd składniowy | | |
| Inny | | |

> ✏️ **Wskazówka do interpretacji:** (1) Co dominuje wśród przyczyn błędów kompilacji i co to mówi o jakości promptu? (2) Czy wysoki DR LLM oznacza problem z promptem, czy cechę modelu? (3) Czy LLM jest X-razy droższy od PIT per użyteczny mutant? Kiedy ta różnica ma znaczenie praktyczne?

*[Interpretacja: do napisania po eksperymencie]*

**Odpowiedź na RQ3:** LLM osiąga Compilability Rate = X% (wobec 100% dla PIT) i Duplicate Rate = Y%. Koszt jednego użytecznego mutanta LLM jest Z-krotnie wyższy niż dla PIT. Główną przyczyną odpadku kompilacji były *[niezgodność typów / odwołania do nieistniejących metod]* — łącznie N% błędów kompilacji. Koszty te są *[akceptowalne / uzasadnione / dyskwalifikujące]* dla projektów o małej do średniej liczbie analizowanych błędów, gdzie priorytetem jest realizm mutantów. Redukcja odpadku przez rozszerzenie promptu o informacje o typach lub fine-tuning modelu może znacząco obniżyć efektywny koszt podejścia LLM.

---

### Synteza: LLM vs PIT — kiedy które podejście ma sens

*[Do napisania po eksperymencie]*

| Kryterium | LLM | PIT |
|---|---|---|
| Realizm mutantów (Ochiai, RBDR) | | |
| Różnorodność operatorów | | |
| Compile rate | | |
| Czas i koszt generacji | | |
| Deterministyczność | | |
| Łatwość integracji (Maven/Gradle) | | |

**PIT** jest lepszym wyborem gdy priorytetem jest szybka, deterministyczna ocena ogólnej siły testów przy zerowym koszcie API i pełnej powtarzalności wyników.

**LLM** jest uzasadnionym uzupełnieniem PIT gdy priorytetem jest wykrywalność realistycznych defektów domenowych i dostępny jest budżet na wywołania API — szczególnie dla klas kodu obsługujących wyjątki i inicjalizację obiektów.

**Oba łącznie** — najbardziej obiecujące podejście praktyczne: PIT jako szybka warstwa bazowa, LLM jako warstwa uzupełniająca dla klas kodu o niskim Ochiai lub braku wykrycia przez PIT.

**Rekomendacja:** *[np. „LLM jest uzasadnionym uzupełnieniem PIT dla projektów, w których priorytetem jest symulacja realistycznych defektów i gdzie budżet API jest dostępny. PIT pozostaje lepszym wyborem dla szybkiej oceny ogólnej siły testów."]*

---

### Ograniczenia badania

**Ograniczona generalizowalność (język i zbiór danych).** Eksperyment przeprowadzono wyłącznie na projektach Java z Defects4J 2.0. Wyniki mogą nie być w pełni przenoszalne na inne języki programowania (Python, C#, Kotlin) ani na projekty spoza tego benchmarku. Przyszłe badania powinny objąć przynajmniej jeden dodatkowy benchmark.

**Jeden model LLM.** Użyto modelu GPT-4o-mini. Inne modele (Claude 3, DeepSeek, CodeLlama) mogą generować inne rozkłady operatorów i inny compile rate. Wybór modelu był podyktowany kosztami API i dostępnością — nie jest dowodem przewagi GPT-4o-mini nad innymi modelami.

**Heurystyczna klasyfikacja NEW/PARTIAL/EXISTING.** Progi 30% i 80% pokrycia (sekcja 7.8) są arbitralne — kalibrowane na próbie pilotażowej, lecz nie wynikają z teorii. Zmiana progów może wpłynąć na odsetek operatorów NEW.

**Przybliżona ekwiwalentność.** Mutanty przeżywające traktowane są jako proxy dla mutantów ekwiwalentnych. Część z nich to mutanty słabe — niewychwycone przez niedostateczne testy, a nie faktycznie ekwiwalentne. To może zawyżać szacowany Equivalent Mutation Rate.

**Niedeterminizm LLM.** Te same dane wejściowe dają różne mutanty w różnych uruchomieniach. Archiwizacja odpowiedzi API pozwala odtworzyć wyniki, ale nie eliminuje ryzyka, że inne uruchomienie dałoby inny rozkład operatorów.

---

### Kierunki dalszych badań

Na podstawie wyników i ograniczeń zidentyfikowanych w niniejszej pracy można wskazać następujące kierunki przyszłych badań:

**Replikacja na różnych językach i zbiorach danych.** Eksperyment ograniczony do Javy i Defects4J 2.0 powinien być powtórzony dla Pythona (BugsInPy) lub JavaScript, aby zbadać, czy nowość operatorów LLM jest cechą specyficzną dla Javy, czy zjawiskiem ogólnym.

**Porównanie wielu modeli LLM.** Użycie GPT-4o-mini, Claude 3 Haiku i modeli open-source (CodeLlama, DeepSeek-Coder) przy tym samym protokole pozwoli ocenić, czy różnorodność i realizm operatorów zależą od konkretnego modelu, czy są powtarzalną właściwością podejścia LLM jako klasy.

**Poprawa compile rate przez inżynierię promptu i fine-tuning.** Rozszerzenie promptu o informację o typach i sygnaturach metod lub fine-tuning na zbiorze par (kod, skompilowany mutant) może znacząco podnieść CR i obniżyć efektywny koszt generacji.

**Automatyczna detekcja ekwiwalentności.** Przybliżona miara ekwiwalentności przez survived mutants jest niewystarczająca. Przyszłe prace mogą stosować symbolic execution lub SMT solvers do precyzyjniejszego wykrywania ekwiwalentnych mutantów.

**Hybrydowe podejście PIT + LLM.** Najbardziej obiecującym kierunkiem praktycznym jest automatyczny selektor: PIT jako szybka i deterministyczna warstwa bazowa, LLM jako warstwa uzupełniająca dla klas kodu o niskim Ochiai lub braku wykrycia przez PIT.

---

## Podsumowanie

Niniejsza praca dotyczyła zastosowania dużych modeli językowych do generowania operatorów mutacyjnych — reguł wprowadzania celowych błędów w kodzie źródłowym, służących do oceny jakości testów automatycznych. Klasyczne operatory mutacyjne definiowane w narzędziach takich jak PIT stanowią ograniczony i statyczny katalog reguł, który może nie odzwierciedlać typów błędów rzeczywiście popełnianych przez programistów.

W pracy postawiono trzy pytania badawcze: (RQ1) czy LLM generuje operatory mutacyjne nieobecne w katalogu PIT ALL; (RQ2) czy mutanty LLM są bliższe rzeczywistym defektom z Defects4J pod względem zachowania programu niż mutanty PIT; (RQ3) jakie są koszty i wydajność podejścia LLM w porównaniu z PIT. Eksperyment przeprowadzono na zbiorze 605 błędów z 12 projektów Java należących do benchmarku Defects4J 2.0 — uznanego standardu w badaniach nad jakością testów.

Wyniki eksperymentu wskazują, że:
- *[RQ1: X% operatorów LLM nie ma odpowiednika w katalogu PIT ALL — co potwierdza / częściowo potwierdza hipotezę o różnorodności.]*
- *[RQ2: Mutanty LLM osiągają RBDR = X% wobec Y% dla PIT oraz medianę Ochiai A wobec B — co oznacza, że LLM generuje / nie generuje realistyczniejsze mutanty.]*
- *[RQ3: LLM osiąga Compilability Rate = X% i jest Z-krotnie droższy od PIT per użyteczny mutant — co czyni podejście akceptowalnym / kosztownym dla projektów o małej do średniej liczbie bugów.]*

Wyniki sugerują, że podejście oparte na LLM stanowi wartościowe uzupełnienie klasycznych narzędzi mutacyjnych, a nie ich zastąpienie. PIT pozostaje szybki, deterministyczny i bezkosztowy, natomiast LLM dostarcza bogatszego i bardziej realistycznego zestawu operatorów — kosztem wyższego nakładu obliczeniowego i finansowego. Praktycznym wnioskiem jest rekomendacja hybrydowego podejścia: PIT jako szybka warstwa bazowa, LLM jako warstwa uzupełniająca dla obszarów kodu słabo wykrywanych przez klasyczne operatory.

*[Uzupełnić po eksperymencie: ostateczne sformułowanie wniosków z konkretnymi wartościami liczbowymi.]*

---

## Bibliografia

[1] PIT mutators documentation.
URL: https://pitest.org/quickstart/mutators/

[2] Michał Mnich Testowanie mutacyjne - optymalizacja procesu i praktyczne zastosowania.
URL: https://bip.pwr.edu.pl/fcp/qGBUKOQtTKlQhbx08SlkFTxYCEi8pMgQGS39TCVdbWCECWR1pXhs_W3dN/4/public/bip/doktoraty/mnich_m/rozprawa_doktorska_micha__mnich.pdf

[3] Are mutants a valid substitute for real faults in software testing?
URL: https://dada.cs.washington.edu/research/tr/2014/02/UW-CSE-14-02-02.PDF

[4] Real bug detection rate.
URL: https://homes.cs.washington.edu/~rjust/publ/defects4j_issta_2014.pdf

[5] Defects4J:
URL: https://github.com/rjust/defects4j

TO DO
