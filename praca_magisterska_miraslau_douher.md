# LLM-Mutants: Analiza efektywności generowania operatorów mutacyjnych za pomocą dużych modeli językowych

**Kierunek**: Informatyka
**Specjalność**: Inżynieria Oprogramowania
**Numer albumu**: 1185432
**Autor**: Miraslau Douher
**Promotor:** dr. prof. Michał Mnich
**Uczelnia:** Uniwersytet Jagielloński
**Rok:** 2026

---

## Spis treści

- [Streszczenie](#streszczenie) (TO DO)

- [1 Wstęp](#rozdział-wstęp) (DONE)
  - [1.1 Temat i cel pracy](#temat-i-cel-pracy) (DONE)
  - [1.2 Budowa pracy](#budowa-pracy) (DONE)

- [2 Testowanie mutacyjne](#testowanie-mutacyjne) (DONE)
  - [2.1 Czym jest mutant?](#czym-jest-mutant) (DONE)
  - [2.2 Zabicie mutanta i mutation score](#zabicie-mutanta-i-mutation-score) (DONE)
  - [2.3 Proces testowania mutacyjnego krok po kroku](#proces-testowania-mutacyjnego-krok-po-kroku) (DONE)
  - [2.4 Koszty i problemy praktyczne](#koszty-i-problemy-praktyczne) (DONE)

- [3 Operatory mutacyjne w narzędziach klasycznych](#operatory-mutacyjne-w-narzędziach-klasycznych) (DONE)
  - [3.1 Czym jest PIT](#czym-jest-pit) (DONE)
  - [3.2 Katalog operatorów klasycznych](#katalog-operatorów-klasycznych) (DONE)
    - [3.2.1 Mutanty projektowe](#mutanty-projektowe) (DONE)
    - [3.2.2 Mutanty integracyjne](#mutanty-integracyjne) (DONE)
    - [3.2.3 Mutanty obiektowe](#mutanty-obiektowe) (DONE)
    - [3.2.4 Mutanty wykonywane na gramatyce](#mutanty-wykonywane-na-gramatyce) (DONE)
  - [3.3 Ograniczenia operatorów klasycznych](#ograniczenia-operatorów-klasycznych) (DONE)

- [4 LLM w testowaniu mutacyjnym](#llm-w-testowaniu-mutacyjnym) (DONE)
  - [4.1 Czym są LLM?](#czym-są-llm) (DONE)
  - [4.2 Zastosowania LLM jako generatora mutantów](#zastosowania-llm-jako-generatora-mutantów) (DONE)
  - [4.3 Zalety i ograniczenia LLM w testowaniu mutacyjnym](#zalety-i-ograniczenia-llm-w-testowaniu-mutacyjnym) (DONE)

- [5 Dane eksperymentalne i metryki](#dane-eksperymentalne-i-metryki) (DONE)
  - [5.1 Zbiór rzeczywistych błędów](#zbiór-rzeczywistych-błędów) (DONE)
  - [5.2 Rodzaje mutantów](#rodzaje-mutantów) (DONE)
    - [5.2.1 Compilable mutants](#compilable-mutants) (DONE)
    - [5.2.2 Duplicate mutants](#duplicate-mutants) (DONE)
    - [5.2.3 Equivalent mutants](#equivalent-mutants) (DONE)
  - [5.3 Metryki i kryteria oceny](#metryki-i-kryteria-oceny) (DONE)
    - [5.3.1 LLM New Mutant Rate](#llm-new-mutant-rate) (DONE)
    - [5.3.2 Real Bug Detection Rate](#real-bug-detection-rate) (DONE)
    - [5.3.3 Average Ochiai Rate](#average-ochiai-rate) (DONE)
    - [5.3.4 Coupling Rate](#coupling-rate) (DONE)
    - [5.3.5 Average Mutant Generation Time](#average-mutant-generation-time) (DONE)
    - [5.3.6 Cost per Useful Mutant](#cost-per-useful-mutant) (DONE)
  - [5.4 Cel pracy i pytania badawcze](#cel-pracy-i-pytania-badawcze) (DONE)

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
Takie podejście przyspiesza pracę programistów, chociaż wymaga dokładniejszej weryfikacji dla osiągnięcia wystarczająco wysokiego poziomu pewności co do poprawności wygenerowanego kodu, co wciąż jest warunkiem koniecznym bezpiecznego wdrożenia.
Jedną z najlepszych metod oceny jakości testów jest stosowanie testowania mutacyjnego, polegające na wprowadzaniu drobnych zmian w kodzie i sprawdzaniu, czy istniejące testy potrafią je wykryć.
Klasyczne narzędzia mutacyjne dysponują jednak tylko niewielkim katalogiem operatorów, co ogranicza przestrzeń defektów rzeczywiście popełnianych przez programistów.

Z drugiej strony LLM, trenowane na większości dostępnych w internecie zbiorach kodu oraz historii bugów, posiadają szerszą wiedzę o defektach popełnianych w produkcyjnym oprogramowaniu.
Dzięki temu możliwe jest wykorzystanie LLM do generowania bardziej nieoczekiwanych oraz realistycznych mutantów.
Pozwala to wykraczać poza ograniczony zestaw reguł dostępnych w klasycznych narzędziach mutacyjnych, a tym samym zwiększać jakość testów.
Z kolei pozwala to wzmocnić poziom zaufania do oprogramowania, w tym do automatycznie wygenerowanego kodu.

Celem niniejszej pracy jest analiza efektywności generowania operatorów mutacyjnych przy użyciu LLM w porównaniu z operatorami klasycznymi.
W ramach badania zostaną przeanalizowane nowe operatory LLM, ich bliskość do rzeczywistych błędów oraz ich wydajność w porównaniu z operatorami klasycznymi.

### Budowa pracy

Wygląd zawartości rozdziałów przedstawionych w pracy:

- **Rozdział 1** Temat i cel pracy wraz z zawartością poszczególnych rozdziałów.
- **Rozdział 2** Definicja testowania mutacyjnego, mutation score, rodzaje mutantów oraz opis procesu testowania mutacyjnego.
- **Rozdział 3** Klasyczne operatory mutacyjne na przykładzie narzędzia PIT, zasada działania, katalog operatorów klasycznych z grupy ALL.
- **Rozdział 4** Duże modele językowe w inżynierii oprogramowania, testowaniu mutacyjnym, rola LLM jako generatora mutantów i zmian w kodzie oraz związane z tym ryzyka.
- **Rozdział 5** Rzeczywiste błędy jako podstawa eksperymentu - zbiór Defects4J 3.0.1, miary podobieństwa mutanta do defektu na podstawie profili testowych oraz kompletna definicja wszystkich metryk i kryteriów oceny stosowanych w badaniu. Następnie problem badawczy, cel pracy i pytania badawcze.
- **Rozdział 6** Metodyka eksperymentu: przebieg, kryteria selekcji błędów, generacja mutantów przez LLM i PIT, weryfikacja oraz definicja mutanta nowego względem PIT — wszystko na podstawie metryk zdefiniowanych w rozdziale 5.
- **Rozdział 7** Analiza wyników eksperymentu, dane liczbowe wraz z ich interpretacją, bezpośrednie odpowiedzi na tezy badawcze, porównanie LLM vs PIT, ograniczenia badania i kierunki dalszych badań.
- **Podsumowanie** Główne wnioski pracy.

## Testowanie mutacyjne

Testowanie mutacyjne to technika oceny tego, jak dobrze testy wykrywają defekty w kodzie.
Polega ona na celowym wprowadzaniu drobnych zmian w kodzie programu, a następnie na sprawdzaniu, czy testy są w stanie te zmiany wykryć.
Każda taka zmiana tworzy nową wersję kodu, zwaną mutantem, który jest następnie sprawdzany przez testy.
Dzięki temu można ocenić, jak dobrze testy sprawdzają logikę oraz wymagania programu i czy są w stanie wykryć potencjalne błędy w kodzie.

Ocena jakości testów automatycznych jest jednym z najważniejszych problemów inżynierii oprogramowania.
Najczęściej używanym sposobem oceny jest sprawdzenie tzw. pokrycia kodu (ang. *code coverage*), czyli tego, jaki procent kodu jest wykonywany podczas testów.
Jednak problem polega na tym, że nawet jeśli kod jest wykonywany, to niekoniecznie oznacza, że jest sprawdzany.
Test, który uruchamia metodę, ale nie sprawdza jej wyniku, może mieć 100% pokrycie kodu, ale nie dawać żadnej informacji o tym, czy program działa poprawnie i spełnia wymagania biznesowe.
Dlatego ważne jest sprawdzenie, czy testy są w stanie wykryć błąd, gdy taki się pojawi.

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
Pozwala to ocenić nie tylko poprawność testu, ale również to, jak dobrze dany przypadek testowy został zdefiniowany.
Robi się to przez celowe wprowadzanie drobnych zmian w kodzie i sprawdzenie, czy testy te zmiany wykrywają.
Jeżeli zmiana nie zostanie wykryta, oznacza to, że testy nie są wystarczająco dobre.

Testowanie mutacyjne jest więc narzędziem, które pomaga ocenić, jak dobre są nasze testy, a nie tylko jaki jest ich zasięg.
Jego użyteczność wynika z tego, że pyta o to, co się stanie, gdy coś pójdzie nie tak, zamiast pytać, co zostało wykonane.
Aby móc przeprowadzić taką ocenę, trzeba najpierw zdefiniować, czym jest mutant i jak przebiega jego analiza.

### Czym jest mutant?

Mutant to specjalna wersja kodu, który powstaje przez wprowadzenie drobnej zmiany w oryginalnym kodzie.
Zmiana ta jest celowa i wynika z określonej reguły, która nazywa się operatorem mutacyjnym.
Definicja mutanta jest stosunkowo prosta, ale kryje w sobie kilka ważnych szczegółów.
- Po pierwsze, mutant różni się od oryginału tylko w jednym miejscu.
- Po drugie, zmiana jest celowa, a nie losowa. W klasycznym podejściu to określony operator mutacyjny.
- Po trzecie, mutant nie jest błędem, który występuje w systemie produkcyjnym, ale raczej sztuczną symulacją błędów, które mogą wystąpić w kodzie.
Z tego powodu symulacja ma być jak najbardziej podobna do prawdziwych błędów, żeby stosowanie testów mutacyjnych do oceniania jakości testów jednostkowych było efektywne.

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
Oznacza to, że testy niewystarczająco pokrywają kod albo nie sprawdzają odpowiednich wymagań, lub też zawierają błędy.
W każdym takim przypadku niewykrycie mutanta świadczy o słabości testów, co pozwala na estymację jakości zestawu testów oraz na wnioskowanie jakości kodu sprawdzanego przez te testy.

Dla liczbowej oceny efektywności zestawu testów w kontekście mutacyjnego testowania stosuje się metrykę mutation score.
Metryka ta pozwala określić, jaki procent mutantów, które udało się skompilować, został zabity przez zbiór testów jednostkowych.

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
Należy odczytywać tę metrykę wyłącznie w kontekście wygenerowanych mutantów, od których całkowicie zależą wyniki testowania mutacyjnego.
Na przykład duża liczba podobnych lub bardzo trywialnych mutantów może prowadzić do błędnych wniosków.
Do testów mutacyjnych trzeba podchodzić z ostrożnością, żeby poprawnie zinterpretować wyniki.

### Proces testowania mutacyjnego krok po kroku

Proces testowania mutacyjnego został po raz pierwszy opisany w 1978 roku przez DeMillo [5].
W praktyce cały proces składa się z kolejnych etapów, w których każdy następny krok jest uzależniony od wyniku etapu poprzedniego [2], [4].
Na początku generuje się tak zwany zbiór mutantów, po czym sprawdza się, czy są one poprawne pod względem technicznym, żeby można było uruchomić na nich testy.
Następnie przeprowadza się analizę wyników oraz interpretację danych, takich jak "mutation score" i inne ustalone metryki, w celu oceny jakości testów.

![Process Testowania Mutacyjnego](images/proces-testowania-mutacyjnego.png)

1. Na początku wybierany jest fragment kodu, który będzie analizowany. 
2. Generowany jest zbiór mutantów w celu symulowania potencjalnych błędów w kodzie.
3. Dla każdego wygenerowanego mutantu sprawdzana jest poprawność techniczna, najczęściej poprzez kompilację, tak aby do dalszego etapu trafiały jedynie mutanty możliwe do uruchomienia.
4. Dla mutantów, które przeszły ten etap, wykonywany jest zbiór testów w celu sprawdzenia, czy wprowadzona zmiana powoduje obserwowalną zmianę zachowania kodu.
5. Po zakończeniu testów mutant zostaje sklasyfikowany jako zabity, jeżeli co najmniej jeden test zakończy się niepowodzeniem, albo jako przeżywający, jeżeli cały zestaw testów przejdzie.
6. Kolejnym krokiem oblicza się mutation score, czyli procent zabitych mutantów, które przeszły etap sprawdzenia technicznego.
7. Na samym końcu przeprowadzana jest interpretacja wyników w celu oceny jakości testów oraz wskazania potencjalnych obszarów kodu, które wymagają poprawy/uzupełnienia testów.

### Koszty i problemy praktyczne

Największą przeszkodą w stosowaniu testowania mutacyjnego w praktyce jest wysoki koszt obliczeniowy oraz czasowy związany z generowaniem, kompilacją oraz uruchamianiem dużej liczby mutantów.
Każdy mutant wymaga osobnego sprawdzenia, dlatego łączny koszt analizy rośnie bardzo szybko.
Jeżeli projekt zawiera N testów oraz wygenerowano dla niego M mutantów, to liczba uruchomień rośnie w przybliżeniu proporcjonalnie do iloczynu N i M, co wprowadza znaczący narzut infrastrukturalny oraz czasowy.
Z tego powodu testowanie mutacyjne, mimo bardzo wartościowej informacji o jakości testów, jest w projektach produkcyjnych stosowane rzadko albo ograniczane tylko do najbardziej krytycznych modułów.

Jednym z podstawowych sposobów ograniczania tego kosztu jest zmniejszenie liczby analizowanych mutantów.
W literaturze [4] opisuje się mutant sampling (losowy wybór reprezentatywnego podzbioru mutantów) oraz selective mutation (ograniczenie analizy do operatorów uznawanych za najbardziej informatywne).
Takie podejście pozwala skrócić czas wykonania przy zachowaniu bardzo przybliżonej do oryginału oceny mutation score.
Dodatkowo współczesne narzędzia starają się przyspieszać analizę przez równoległość, ograniczanie liczby uruchamianych testów oraz mutację na poziomie bajtkodu JVM, co wykorzystuje między innymi PIT [1], [2].

Częściowym sposobem ograniczenia tego problemu może być także generowanie mutantów przy użyciu LLM.
W przeciwieństwie do klasycznych operatorów mutacyjnych, opartych na szerokim katalogu operatorów, LLM mogą potencjalnie generować mniejszą liczbę mutantów oraz bardziej zbliżonych do rzeczywistych błędów w kodzie.
W takim przypadku redukcja liczby kandydatów może obniżyć koszt dalszej kompilacji i uruchamiania testów.
Dodatkową zaletą jest to, że istnieją już małe, kwantyzowane LLM osiągające dobre wyniki w benchmarkach, dla których koszt obliczeniowy oraz czas pojedynczej generacji mogą być relatywnie niskie.
Oznacza to, że przy odpowiednio dobranym modelu i strategii selekcji mutantów podejście LLM może częściowo poprawić praktyczną opłacalność testowania mutacyjnego, zwiększając dostępność tego podejścia dla szerszego zakresu projektów produkcyjnych.

---

## Operatory mutacyjne w narzędziach klasycznych

Głównym celem operatorów mutacyjnych jest symulowanie typowych błędów w kodzie.
Klasyczne operatory mutacyjne to zbiór zdefiniowanych reguł transformacji kodu, których celem jest tworzenie sztucznych błędów o przewidywalnym charakterze.
Ich największą zaletą jest powtarzalność, ponieważ każdy operator opisuje jasno określony wzorzec zmiany, co pozwala na stosunkowo łatwą automatyzację oraz pełną kontrolę nad procesem generacji mutantów.
W tym rozdziale przedstawiono klasyczne operatory, realizowane za pomocą narzędzia PIT [1], jako rozpowszechnione i dobrze udokumentowane rozwiązanie.

### Czym jest PIT

PIT jest narzędziem do testowania mutacyjnego dla projektów napisanych w Javie.
W niniejszej pracy stanowi ono reprezentatywne źródło klasycznych operatorów mutacyjnych, ponieważ udostępnia zarówno publiczną dokumentację z definicjami operatorów, jak i otwarty kod źródłowy.
Pozwala to jednoznacznie określić, jakie mutanty są generowane, co będzie potrzebne w dalszej analizie.
Z dokumentacji PIT wynika, że grupa "ALL", która będzie stosowana w badaniu, obejmuje 29 operatorów mutacyjnych.
Katalog "ALL" reprezentuje zakres klasycznych operatorów mutacyjnych, co jest istotne dla wyznaczenia listy klasycznych mutantów oraz porównania ich z mutantami generowanymi przez LLM.

### Katalog operatorów klasycznych

W klasyfikacji operatorów mutacyjnych wykorzystano klasyfikację przedstawioną przez Ammanna i Offutta [4].
Na tej podstawie operatory PIT z grupy "ALL" uporządkowano według czterech rodzin, aby zdefiniować uporządkowaną listę klasycznych mutantów do porównania z mutantami wygenerowanymi przez LLM.

#### Mutanty projektowe

Mutanty projektowe stanowią zbiór modyfikacji kodu źródłowego, które symulują proste lokalne błędy w logice.
Obejmują one operacje arytmetyczne, inkrementacje, operatory relacyjne, operatory bitowe oraz literały występujące w obrębie jednej metody.

- `Conditionals Boundary` - służy do testowania poprawności warunków granicznych. Działa przez zamianę `<` na `<=`, `<=` na `<`, `>` na `>=` oraz `>=` na `>`.
- `Increments` - sprawdza poprawność aktualizacji zmiennych lokalnych. Działa przez zamianę inkrementacji na dekrementacje i odwrotnie.
- `Invert Negatives` - bada poprawność użycia znaku wartości numerycznych. Działa przez usunięcie negacji albo odwrócenie znaku zmiennej, ale nie mutuje ujemnych literałów.
- `Math` - odpowiada za mutacje operatorów arytmetycznych, bitowych i przesunięć. Obejmuje między innymi zamiany `+` na `-`, `*` na `/`, `%` na `*`, `&` na `|` oraz `<<` na `>>`.
- `Negate Conditionals` - służy do sprawdzania logiki porównań. Działa przez zamianę `==` na `!=`, `!=` na `==`, `<` na `>=`, `<=` na `>` oraz `>` na `<=`.
- `Inline Constant` - mutuje literały przypisane do zmiennych niefinalnych. W zależności od typu zmienia je na wartości graniczne albo zwiększa ich wartość.
- `Remove Increments` - usuwa inkrementację lokalnych zmiennych.
- `Negation (ABS)` - zastępuje użycie zmiennej numerycznej jej negacją.
- `Arithmetic Operator Replacement (AOR)` - wykonuje rozszerzoną zamianę operatorów `+`, `-`, `*`, `/` i `%` na inne operatory arytmetyczne z tej listy.
- `Arithmetic Operator Deletion (AOD)` - usuwa operator arytmetyczny i pozostawia tylko pierwszy albo drugi operand. Na przykład `int a = b + c;` mutuje do `int a = b;`.
- `Constant Replacement (CRCR)` - mutuje stałe według kilku schematów, na przykład do `1`, `0`, `-1`, wartości przeciwnej albo wartości zwiększonej i zmniejszonej o jeden.
- `Bitwise Operator (OBBN)` - mutuje operacje bitowe `&` i `|`, zamieniając operator albo redukując wyrażenie do jednego z operandów.
- `Relational Operator Replacement (ROR)` - rozszerza mutacje operatorów relacyjnych przez podstawienia między `<`, `<=`, `>`, `>=`, `==` i `!=`.
- `Unary Operator Insertion (UOI)` - wstawia operatory jednoargumentowe, takie jak preinkrementacja, postinkrementacja, predekrementacja i postdekrementacja przy odwołaniach do zmiennych.

Mutanty projektowe są w katalogu PIT najliczniejsze.
Wynika to z faktu, że klasyczne testowanie mutacyjne historycznie skupiało się na drobnych błędach w obrębie pojedynczej jednostki kodu, takich jak błędna granica porównania albo niewłaściwa modyfikacja zmiennej lokalnej.

#### Mutanty integracyjne

Mutanty integracyjne stanowią zbiór modyfikacji kodu źródłowego, które badają poprawność współpracy między metodami oraz przepływu wartości pomiędzy komponentami kodu.

- `Void Method Call` - usuwa wywołania metod typu `void`. Pozwala to sprawdzić, czy testy wykrywają brak efektu ubocznego operacji, która nic nie zwraca.
- `Non Void Method Call` - usuwa wywołania metod zwracających wartość oraz zastępuje ich wynik domyślną wartością Javy dla danego typu, na przykład `0`, `false`, `0.0` albo `null`.
- `Experimental Argument Propagation` - zastępuje całe wywołanie metody jednym z jego argumentów o zgodnym typie. Bada to pominięcie logiki metody i dalsze użycie wartości wejściowej.

Jeżeli usunięcie wywołania metody albo zastąpienie przekazywanych parametrów nie wpływa na wynik testów, może to oznaczać, że integracja między elementami programu nie jest wystarczająco dobrze przetestowana.

#### Mutanty obiektowe

Mutanty obiektowe stanowią zbiór modyfikacji kodu źródłowego, które symulują błędy związane z korzystaniem z mechanizmów obiektowych.

- `Constructor Call` - zastępuje wywołanie konstruktora wartością `null`. Służy do badania odporności programu na brak poprawnie zainicjalizowanego obiektu.
- `Experimental Big Integer` - zamienia wywołania metod na obiektach `BigInteger`. Reprezentuje to błędy w użyciu obiektowego API liczbowego.
- `Experimental Member Variable` - usuwa przypisania do pól obiektów, także pól finalnych, przez co pola przyjmują domyślne wartości Javy.
- `Experimental Naked Receiver` - zastępuje wywołanie metody samym odbiorcą wywołania, co oznacza pominięcie logiki tej metody przy zachowaniu obiektu.

Choć PIT nie implementuje całego katalogu klasycznych operatorów obiektowych znanych z literatury, zawiera wystarczająco reprezentatywną grupę związaną z programowaniem obiektowym.

#### Mutanty wykonywane na gramatyce

Mutanty wykonywane na gramatyce obejmują takie modyfikacje, które symulują błędy przepływu sterowania albo zwracania wyniku z metody.
W odróżnieniu od mutacji projektowych nie dotyczą one wyłącznie pojedynczego operatora, lecz wpływają na semantykę instrukcji `return`, `if` lub `switch`.

- `Return Values` – zmienia wynik metody w sposób zależny od typu zwracanej wartości, na przykład dla typów logicznych odwraca `true` i `false`, dla liczb podstawiał wartości domyślne albo przesunięte, a dla obiektów zastępował wynik wartością `null`.
- `Empty Returns` – zastępuje wynik metody odpowiadającą mu pustą reprezentacją. W praktyce może to być pusty napis, pusta kolekcja, `Optional.empty()` albo wartość zero. Operator ten pozwala sprawdzić, czy testy odróżniają wynik rzeczywisty od poprawnego składniowo, ale semantycznie pustego.
- `False Returns` – wymusza zwracanie `false` dla wartości logicznych. Jest użyteczny tam, gdzie poprawność programu zależy od pojedynczych decyzji logicznych zwracanych przez metodę.
- `True Returns` –  wymusza zwracanie `true` dla wartości logicznych. Jest analogiczny do `False Returns`.
- `Null Returns` – zastępuje zwracany obiekt wartością `null`. Operator ten pozwala sprawdzić, czy testy poprawnie sprawdzają brak oczekiwanego obiektu.
- `Primitive Returns` – zastępuje prymitywne wartości zwracane przez `0`. Dzięki temu bada, czy testy odróżniają wynik obliczenia od wartości domyślnej dla typu numerycznego.
- `Remove Conditionals` – usuwa znaczenie warunku i wymusza wykonanie albo pominięcie gałęzi `if` lub `else`. Dokumentacja PIT wyróżnia tu specjalizacje dla warunków równościowych i porządkowych oraz dla gałęzi, która ma zostać wymuszona. Mutator ten sprawdza, czy testy są wrażliwe na sam wybór ścieżki wykonania programu.
- `Experimental Switch` – mutuje instrukcję `switch` przez zastąpienie etykiety domyślnej pierwszą etykietą jawną, a pozostałych etykiet wartością `default`.

Wspólną cechą tych mutantów jest to, że mutacje obejmują konstrukcje składniowe odpowiedzialne za wybór ścieżki wykonania albo za zwracanie wartości z metody.
Pozwala to badać, czy testy wykrywają błędy związane nie tylko z lokalnym operatorem, lecz również z błędną strukturą sterowania.

### Ograniczenia operatorów klasycznych

Mimo tego, że PIT ma bogaty katalog, nadal jest narzędziem opartym na skończonym zbiorze ręcznie zdefiniowanych reguł zaprojektowanych przez autorów narzędzia.
Każdy operator opisuje tylko taki rodzaj zmiany, jaki przewidzieli jego twórcy.
Dlatego przestrzeń możliwych defektów jest symulowana przez stosunkowo ograniczony obszar mutantów.
W praktyce oznacza to, że PIT nie tworzy zmian wyraźnie zależnych od znaczenia całego fragmentu programu, lecz od wzorca rozpoznanego przez konkretny mutator.
Jest to istotne, ponieważ właśnie poza tym obszarem mogą pojawiać się nowe operatory generowane przez LLM, które będą lepiej symulować rzeczywiste błędy w kodzie.
Ograniczona różnorodność transformacji w podejściu klasycznym stanowi więc jedną z głównych przyczyn dla badania LLM jako generatora mutantów.

---

## LLM w testowaniu mutacyjnym

Klasyczne operatory mutacyjne opierają się na skończonym, z góry zdefiniowanym zbiorze operatorów.
Z tego powodu zakres generowanych przez nie mutantów jest ograniczony do zmian realizowanych przez te operatory
Z kolei LLM są znacznie większą klasę narzędzi, ponieważ generują kod na podstawie zależności statystycznych wyuczonych z dużych zbiorów danych.
W zastosowaniach związanych z testowaniem mutacyjnym [6] istotne są takie właściwości jak zdolność do uwzględniania kontekstu, możliwość generowania zmian podobnych do rzeczywistych błędów oraz syntaktycznie poprawnego kodu.
Właściwości te pozwalają traktować LLM jako narzędzie, które może efektywniej generować zmiany w kodzie odzwierciedlające rzeczywiste błędy.

### Czym są LLM?

Duże modele językowe (*Large Language Models*, LLM) są klasą modeli głębokiego uczenia trenowanych na ogromnych zbiorach danych.
Ich działanie jest oparte na modelowaniu zależności między elementami sekwencji oraz przewidywaniu najbardziej prawdopodobnego następnego tokenu na podstawie poprzedniego tekstu.
Współczesne LLM oparte na architekturze transformera, co pozwala im uwzględniać relacje między odległymi elementami wejściowymi i przetwarzać długie fragmenty tekstu w spójny sposób.
W praktyce umożliwia to generowanie, uzupełnianie, streszczanie i przekształcanie treści, w tym również kod, który traktowany jest jako strukturalny tekst, podlegający regułom syntaktycznym, zależnościom typów i wzorcom implementacyjnym.
W kontekście zastosowań mutacyjnych potrafią one generować zmiany, które są formalnie poprawne w danym miejscu w kodzie, a jednocześnie mogą prowadzić do innego zachowania programu.

### Zastosowania LLM jako generatora mutantów

W inżynierii oprogramowania LLM są wykorzystywane do analizy, generowania i modyfikacji kodu.
Obejmuje to uzupełnianie implementacji, wyjaśnianie działania istniejących fragmentów kodu, tworzenie dokumentacji, przygotowywanie testów oraz wspieranie przeglądu kodu.
Wspólną cechą tych zastosowań jest działanie na fragmentach kodu, których poprawność zależy nie tylko od pojedynczych elementów składniowych, ale również od relacji między instrukcjami, typami i przepływem sterowania.

Ta sama właściwość ma znaczenie w testowaniu mutacyjnym, gdzie istotne jest generowanie zmian możliwych do zastosowania w konkretnym miejscu programu, takich, aby mogły wpłynąć na jego zachowanie.
Z tego względu LLM mogą być rozpatrywane jako efektywne narzędzie do generowania mutantów w kodzie.
Model otrzymuje fragment programu oraz prompt opisujący oczekiwaną transformację.
Takie podejście umożliwia generowanie mutantów bez konieczności uprzedniego definiowania każdej reguły mutacyjnej w postaci osobnego operatora.
Zamiast tego model wykorzystuje kontekst, relacje między instrukcjami kodu oraz dane treningowe.

### Zalety i ograniczenia LLM w testowaniu mutacyjnym

Zastosowanie LLM w testowaniu mutacyjnym otwiera nowe możliwości do generowania mutantów, które nie są ograniczone do klasycznego katalogu operatorów.
Najważniejszą zaletą tego podejścia jest większa elastyczność tworzenia zmian, które są dostosowane do kontekstu programu.
Może to prowadzić do większej różnorodności analizowanych defektów oraz generowania mutantów bliższych rzeczywistym błędom.
Podejście to może być również przydatne, gdy celem jest wygenerowanie mniejszej liczby zmian, ale o większej wartości diagnostycznej.

Jednakże, ograniczenia tego podejścia wynikają z mniejszej przewidywalności samego procesu generacji w porównaniu do klasycznych operatorów.
Wygenerowane mutanty w dużym stopniu zależą od modelu, promptu i parametrów uruchomienia, a same zmiany mogą okazać się niekompilowalne albo zduplikowane.
Pod tym względem wykorzystanie LLM w testowaniu mutacyjnym wymaga dodatkowej filtracji oraz walidacji.

---

## Dane eksperymentalne i metryki

Zanim przejdziemy do szczegółowego opisu eksperymentu, należy najpierw odpowiedzieć na pytanie, w jaki sposób ocenić, czy mutanty wygenerowane przez LLM są rzeczywiście lepsze od mutantów klasycznych.
Taka ocena wymaga zbioru rzeczywistych błędów, względem którego można analizować stopień realizmu mutantów, a także zastosowania odpowiednich metryk porównawczych.
W tym rozdziale zostanie przedstawiony zbiór defektów wykorzystany w badaniu, a potem zdefiniowane zostaną metryki służące do określania podobieństwa mutanta do rzeczywistego błędu.

### Zbiór rzeczywistych błędów

Oceniając jakość oprogramowania, kluczowa jest analiza zbioru udokumentowanych, rzeczywistych defektów, które faktycznie wystąpiły w kodzie produkcyjnym, zostały zgłoszone, a następnie naprawione przez programistów.
Zbiory te, znane jako repozytoria błędów, różnią się od standardowych zestawów testowych, ponieważ przechowują trzy kluczowe komponenty dla każdego błędu.
Po pierwsze, istnieje "wersja z błędami" kodu, która zawiera defekt w jego oryginalnym stanie, jeszcze przed naprawą.
Po drugie, mamy "wersję naprawioną" kodu, w której błąd został rozwiązany w sposób, który pozwala na porównanie zachowania programu przed i po naprawie.
Po trzecie, istnieją "testy jednostkowe", które kończą się niepowodzeniem po uruchomieniu wersji z błędami oraz kończą się powodzeniem w naprawionej wersji.
To ustrukturyzowane podejście pozwala na odtworzenie zachowania programu z obecnym błędem oraz porównanie jego z zachowaniem wygenerowanego mutanta.

Źródłem danych w tym badaniu jest **Defects4J** w wersji 3.0.1 [3]. 
Defects4J to zestaw 854 błędów z 17 projektów Java open-source, który jest utrzymywany przez naukowców od 2014 roku.
Dla każdego błędu mamy dostęp do wersji kodu z błędem oraz wersji naprawionej.
Co więcej, w celu ułatwienia analizy dostępna jest lista zmodyfikowanych klas, która pokazuje, które pliki zostały zmienione w wersji poprawionej.
Dostępny jest także zestaw nazw testów oraz możliwość automatycznego kompilowania i uruchamiania testów bez ręcznej konfiguracji środowiska.
Każdy błąd został zgłoszony w systemie śledzenia zgłoszeń, a następnie naprawiony w jednym zatwierdzeniu. 
Kod każdego błędu został ręcznie minimalizowany w taki sposób, żeby usunąć zmiany, które nie były związane z defektem, takie jak refaktoryzacja, czyli nowe funkcje.
Zgodnie z dokumentacją dla każdego błędu istnieje przynajmniej jeden test, który zawsze kończy się niepowodzeniem niezależnie od kolejności wywołania testów.

| Identyfikator   | Projekt                | Liczba aktywnych bugów | IDs aktywnych bugów          |
|-----------------|------------------------|------------------------|------------------------------|
| Chart           | jfreechart             | 26                     | 1–26                         |
| Cli             | commons-cli            | 39                     | 1–5, 7–40                    |
| Closure         | closure-compiler       | 174                    | 1–62, 64–92, 94–176          |
| Codec           | commons-codec          | 18                     | 1–18                         |
| Collections     | commons-collections    | 28                     | 1–28                         |
| Compress        | commons-compress       | 47                     | 1–47                         |
| Csv             | commons-csv            | 16                     | 1–16                         |
| Gson            | gson                   | 18                     | 1–18                         |
| JacksonCore     | jackson-core           | 26                     | 1–26                         |
| JacksonDatabind | jackson-databind       | 110                    | 1–64, 66–88, 90–112          |
| JacksonXml      | jackson-dataformat-xml | 6                      | 1–6                          |
| Jsoup           | jsoup                  | 93                     | 1–93                         |
| JxPath          | commons-jxpath         | 22                     | 1–22                         |
| Lang            | commons-lang           | 61                     | 1, 3–17, 19–24, 26–47, 49–65 |
| Math            | commons-math           | 106                    | 1–106                        |
| Mockito         | mockito                | 38                     | 1–38                         |
| Time            | joda-time              | 26                     | 1–20, 22–27                  |
| **Razem**       |                        | **854**                | —                            |

Projekty reprezentują szerokie spektrum dziedzin, od bibliotek narzędziowych (Lang, Math, Collections), przez parsery i kodeki (Jsoup, Gson, JacksonCore, JacksonDatabind, Codec), aż po kompilatory (Closure) i narzędzia ogólnego przeznaczenia (Compress, Csv, Cli). Różnorodność dziedzin zapewnia, że wyniki nie są specyficzne dla jednego rodzaju kodu i mogą stanowić podstawę wniosków ogólniejszej natury. Ze względu na koszty wywołań interfejsu API modelu językowego i czas uruchomienia testów, spośród dostępnych błędów wybierana jest reprezentatywna próba spełniająca zdefiniowane kryteria selekcji.

Projekty obejmują różne rodzaje aplikacji, takie jak biblioteki pomocnicze (Lang, Math, Collections), parsery (Jsoup, Gson, JacksonCore, JacksonDatabind i Codec), kompilator (Closure) oraz narzędzia ogólnego przeznaczenia (Compress, Csv i Cli).
Taka różnorodność aplikacji pozwala uzyskać wyniki, które nie dotyczą tylko jednego rodzaju kodu, lecz mogą stanowić podstawę wniosków o szerszym zakresie.
Ze względu na koszty połączeń z modelem językowym oraz czas potrzebny na wykonanie testów wybrana zostanie jedynie reprezentatywna grupa błędów.
W dalszej części rozdziału termin defekt oznacza pojedynczy rzeczywisty błąd pochodzący z tego zbioru.

### Rodzaje mutantów

Dla przeprowadzenia badania trzeba zdefiniować rodzaje mutantów, na podstawie których będą liczone metryki dla odpowiedzi na tezy badawcze.

#### Compilable mutants

Mutant kompilowany to wersja kodu, która po wprowadzeniu mutacji przechodzi poprawnie etap kompilacji.
Oznacza to brak błędów strukturalnych, syntaktycznych, niezgodności typów oraz brakujących symboli, które uniemożliwiałyby uruchomienie testów na zmodyfikowanym kodzie.
W badaniu wszystkie wygenerowane mutanty, zarówno klasyczne, jak i wygenerowane przez LLM, są poddawane próbie kompilacji w konfiguracji projektu.
Mutanty niekompilowane nie będą uczestniczyć w metrykach opartych na uruchamianiu testów, ponieważ nie można uruchomić na nich testów.

Metryka jest zdefiniowana jako liczba mutantów, które można skompilować, podzielona przez całkowitą liczbę wygenerowanych mutantów.
```
Compilability Mutation Rate (CMR) = liczba mutantów, które można skompilować / liczba wygenerowanych mutantów
```

Ta metryka będzie używana do obliczenia liczby mutantów możliwych do użycia w testowaniu, ponieważ LLM nie może gwarantować poprawnej generacji mutantów.
Będzie to potrzebne do oceniania stabilności generowania mutantów przez LLM, a także do porównania z klasycznymi mutantami, które charakteryzują się bardzo wysoką kompilowalnością lub 100% dla niektórych klasycznych narzędzi.

#### Duplicate mutants

Mutant zduplikowany to mutant, który syntaktycznie jest identyczny z innym mutantem albo z oryginalnym kodem.
Takie mutanty nie wprowadzają nowego zachowania i nie wnoszą nowych danych do analizy, ponieważ ich efekt został już uwzględniony.
Przed obliczaniem metryk usuwa się je ze zbioru, aby nie zawyżały wyników niektórych metryk.

Algorytm identyfikacji duplikatów polega na porównaniu reprezentacji kodu wygenerowanego mutanta po normalizacji z oryginalnym kodem oraz już istniejącymi mutantami.
Jeżeli dwie reprezentacje mutantów są identyczne względem siebie, oba mutanty traktowane są jako duplikaty tej samej modyfikacji.
Jeżeli mutant jest identyczny z oryginałem, oznacza się go jako duplikat.
Po ich usunięciu pozostaje zbiór mutantów unikalnych, który wraz z warunkiem kompilowalności stanowi podstawę do obliczania dalszych metryk.

```
Duplication Mutation Rate (DMR) = liczba mutantów zduplikowanych / liczba mutantów kompilowalnych
```

Wskaźnik ten pokazuje, jaki odsetek mutantów kompilowanych stanowią duplikaty.

#### Equivalent mutants

Mutant ekwiwalentny to mutant, który mimo różnic syntaktycznych zachowuje się w taki sam sposób jak oryginalny kod.
Oznacza to, że żaden test nie jest w stanie wykryć wprowadzonej zmiany, ponieważ nie prowadzi ona do obserwowalnej różnicy w zachowaniu kodu.
Nie istnieje uniwersalny algorytm rozpoznawania mutantów ekwiwalentnych, ponieważ problem ten jest nierozstrzygalny w ogólnym przypadku, dlatego w analizie będą stosowane przybliżone metryki oparte na wynikach testów.
Za mutanty ekwiwalentne uznaje się mutanty kompilowane i niezduplikowane, które przeżywają cały dostępny zestaw testów.
Podejście daje wyniki przybliżone, bo mutanty mogą przeżywać testy z powodu ich niedostatecznego pokrycia, a nie faktycznej ekwiwalentności semantycznej.
Choć takie podejście nie daje dokładnych wyników, ale pozwala porównać efektywność generacji mutantów, co w naszym przypadku jest wystarczające.

```
Equivalent Mutation Rate (EMR) = liczba mutantów przeżywających / (liczba mutantów kompilowalnych - liczba duplikatów)
```

### Metryki i kryteria oceny

Ocena mutantów opiera się na trzech najważniejszych kryteriach: stopniu różnorodności względem mutantów generowanych przez LLM oraz klasyczne narzędzia, poziomie podobieństwa do rzeczywistych błędów w kodzie, efektywności generacji mutantów, uwzględniając koszt oraz czas potrzebny do ich generacji.

W dalszej części rozdziału termin "mutant" oznacza mutanta kompilowalnego i niezduplikowanego.

#### LLM New Mutant Rate

*LLM New Mutant Rate* (LLM-NMR) mierzy, jaka część mutantów generowanych przez LLM nie ma odpowiednika wśród mutantów klasycznych.
Wskaźnik pozwala ocenić, czy LLM generuje nowe typy mutantów nieobecne w katalogu klasycznych operatorów.

Mutant LLM liczy się za nowy, gdy spełnia jednocześnie:
1. Nie powtarza żadnej zmiany wprowadzonej przez klasycznego mutanta w tej samej linijce kodu (brak odpowiednika syntaktycznego po normalizacji).
2. Nie istnieje mutant klasyczny wywołujący ten sam zestaw nieprzechodzących testów (brak odpowiednika w profilu testowym).

```
LLM-NMR = liczba mutantów LLM bez odpowiednika wśród mutantów klasycznych / liczba wszystkich użytecznych mutantów LLM
```

Wysoka wartość wskaźnika oznacza, że LLM generuje dużo mutantów nieobecnych w katalogu klasycznym; niska, że generowane mutanty w znaczącej mierze pokrywają się z istniejącymi operatorami klasycznymi.

#### Real Bug Detection Rate

*Real Bug Detection Rate* (RBDR) mierzy, dla jakiej części rzeczywistych defektów można znaleźć co najmniej jednego mutanta, który wykazuje częściową zgodność profilu testowego z danym defektem.
Kluczowym elementem tej metryki jest porównanie dwóch zbiorów testów: profilu testowego mutanta oraz defektu.
Profil mutanta definiowany jako zbiór testów nieprzechodzących po wprowadzeniu mutacji, a profil defektu obejmuje testy, które nie przechodzą dla wersji kodu z bugiem, ale przechodzą dla naprawionej wersji.
Na przykład, jeśli profil defektu zawiera testy `T1` i `T2`, a istnieje mutant powodujący niepowodzenie testu `T1`, to taki rzeczywisty defekt jest uznawany za wykryty. 

```
RBDR = liczba defektów wykrytych przez co najmniej jeden mutant / liczba wszystkich analizowanych defektów
```

Wysoka wartość RBDR oznacza, że dla wielu rzeczywistych defektów istnieją mutanty, które powodują niepowodzenie co najmniej części tych samych testów, co wskazuje na to, że odzwierciedlają one zachowanie rzeczywistych błędów.

#### Average Ochiai Rate

*Average Ochiai Rate* (AOR) mierzy, w jakim stopniu mutanty pokrywają się z profilami testowymi rzeczywistych defektów.
Kluczowym elementem oceny jest porównanie dwóch zbiorów testów: profilu mutanta oraz profilu defektu.
W przeciwieństwie do `RBDR`, który jest metryką binarną, `AOR` odzwierciedla stopień tej zależności.
Im większa część testów wykrywających defekt znajduje się również w profilu mutanta, tym wyższa jest wartość tej metryki.

```
AOR = średnia(liczba wspólnych testów nieprzechodzących / pierwiastek z (liczba testów nieprzechodzących mutanta × liczba testów wykrywających defekt))
```

Wyższa wartość `AOR` oznacza, że profile niepowodzeń mutantów są bardziej zbliżone do profili testowych rzeczywistych defektów.

#### Coupling Rate

*Coupling Rate* (CR) mierzy, dla jakiej części użytecznych mutantów można znaleźć powiązanie z profilem testowym rzeczywistego defektu, dla którego dany mutant został wygenerowany.
Kluczowym elementem oceny jest porównanie dwóch zbiorów testów: profilu mutanta oraz profilu defektu.
Mutant jest powiązany z defektem, jeśli powoduje niepowodzenie co najmniej jednego testu z profilu tego defektu.

```
CR = liczba użytecznych mutantów powiązanych z odpowiadającym im defektami / liczba wszystkich użytecznych mutantów
```

W odróżnieniu od `RBDR`, który ocenia pokrycie od strony defektów, `CR` pokazuje, jaka część mutantów jest rzeczywiście związana z zachowaniem błędów w programie.

#### Average Mutant Generation Time

*Average Mutant Generation Time* (AMGT) mierzy średni czas potrzebny do wygenerowania jednego mutanta.
Podstawą oceny jest łączny czas etapu generacji oraz całkowita liczba wygenerowanych mutantów.
Dla LLM czas ten obejmuje okres od wysłania zapytania do modelu do uzyskania pełnej odpowiedzi.

```
AMGT = łączny czas generacji / liczba wszystkich wygenerowanych mutantów
```

Niższa wartość `AMGT` oznacza szybsze wytwarzanie pojedynczych mutantów i mniejszy koszt czasowy etapu generacji mutantów.

#### Cost per Useful Mutant

*Cost per Useful Mutant* (CPUM) mierzy koszt czasowy uzyskania jednego użytecznego mutanta, czyli mutanta kompilowalnego i niezduplikowanego.

```
CPUM = łączny czas generacji / liczba mutantów kompilowalnych i niezduplikowanych
```

Niższa wartość `CPUM` oznacza, że dane podejście szybciej generuje mutanty przydatne do dalszego uruchomienia oraz analizy.

### Cel pracy i pytania badawcze

Celem tej pracy jest weryfikacja, czy LLM mogą generować nowe mutanty, których nie można uzyskać za pomocą klasycznych operatorów mutacyjnych.
Dodatkowo analizowane jest, czy te wygenerowane mutanty są bardziej zbliżone do rzeczywistych defektów w programie w porównaniu do generowanych przy użyciu klasycznych narzędzi, a także jakie są koszty i ograniczenia podejścia opartego na LLM.

Badanie odpowiada na trzy pytania badawcze:

RQ1 - Czy możliwe jest generowanie nowych mutantów przy użyciu LLM, wykraczających poza klasyczny katalog operatorów mutacyjnych?

Pytanie dotyczy różnorodności: czy LLM w ogóle mogą wykroczyć poza zdefiniowany katalog klasycznych operatorów mutacyjnych.
Odpowiada na nie metryka *LLM New Mutant Rate* (LLM-NMR), która mierzy procent mutantów LLM nieposiadających odpowiednika wśród mutantów klasycznych wygenerowanych dla tego samego defektu.
Wysoka wartość LLM-NMR oznacza, że LLM generuje nowe mutanty, niedostępne w katalogu klasycznym.

RQ2 - Czy mutanty LLM są bliższe rzeczywistym defektom niż mutanty klasyczne?

Pytanie dotyczy realizmu: czy mutanty LLM wywołują niepowodzenia testów podobne do tych, które wywołuje rzeczywisty błąd.
Odpowiadają na nie trzy metryki. *Real Bug Detection Rate* (RBDR) mierzy, dla jakiej części analizowanych defektów istnieje co najmniej jeden mutant mający zgodny profil z defektem.
*Average Ochiai Rate* (AOR) wyraża średni stopień podobieństwa między profilem testowym mutanta a profilem rzeczywistego defektu.
*Coupling Rate* (CR) mierzy, jaki odsetek wszystkich mutantów jest powiązany z profilem testowym odpowiadającego im defektu.
Łączna analiza RBDR, AOR i CR pozwala ocenić, które z podejść generuje mutanty lepiej symulujące rzeczywiste defekty programów.

RQ3 - Czy mutanty generowane przez LLM są bardziej wydajne od bliskich klasycznych odpowiedników?

Pytanie dotyczy efektywności: ile kosztuje uzyskanie mutanta do uruchamiania testów, jak duży jest odsetek mutantów, które zostały odrzucone podczas filtracji, oraz jaki jest koszt czasowy potrzebny na generowanie zestawu mutantów.
Odpowiedzi na te pytania dostarczają metryki: *Compilability Mutation Rate* (CMR), *Duplication Mutation Rate* (DMR) i *Equivalent Mutation Rate* (EMR).
Te metryki opisują kolejno odsetek mutantów, które przeszły kompilację, odsetek duplikatów syntaktycznych wśród mutantów kompilowalnych oraz odsetek użytecznych mutantów, które nie zostały wykryte przez cały zestaw testów
Wskaźniki kosztowe, takie jak *Average Mutant Generation Time* (AMGT) i *Cost per Useful Mutant* (CPUM), mierzą odpowiednio średni czas generacji jednego mutanta oraz efektywny koszt uzyskania jednego użytecznego mutanta, uwzględniając straty na etapie filtracji.

Poniższa tabela zbiera wszystkie wskaźniki w formie zestawienia:

| Metryka                        | Skrót   | Co mierzy                                                                 | Powiązane RQ |
|--------------------------------|---------|---------------------------------------------------------------------------|--------------|
| LLM New Mutant Rate            | LLM-NMR | Odsetek mutantów LLM bez odpowiednika wśród mutantów klasycznych          | RQ1          |
| Real Bug Detection Rate        | RBDR    | Odsetek defektów, dla których istnieje co najmniej jeden powiązany mutant | RQ2          |
| Average Ochiai Rate            | AOR     | Średni stopień podobieństwa profili testowych mutanta i defektu           | RQ2          |
| Coupling Rate                  | CR      | Odsetek mutantów powiązanych z profilem odpowiadającego im defektu        | RQ2          |
| Compilability Mutation Rate    | CMR     | Odsetek wygenerowanych mutantów, które przeszły kompilację                | RQ3          |
| Duplication Mutation Rate      | DMR     | Odsetek duplikatów syntaktycznych wśród kompilowalnych mutantów           | RQ3          |
| Equivalent Mutation Rate       | EMR     | Odsetek mutantów przeżywających pełny zestaw testów                       | RQ3          |
| Average Mutant Generation Time | AMGT    | Średni czas wytworzenia jednego mutanta                                   | RQ3          |
| Cost per Useful Mutant         | CPUM    | Efektywny koszt uzyskania jednego użytecznego mutanta                     | RQ3          |

Pytania badawcze są wzajemnie uzupełniające: RQ1 bada różnorodność, RQ2 bada realizm, RQ3 bada efektywność procesu generacji.

---

## Założenia eksperymentu i metodyka

Niniejszy rozdział opisuje, w jaki sposób przeprowadzono badanie empiryczne: jakie dane wybrano, jak generowano mutanty przez model językowy i przez PIT, jak weryfikowano ich poprawność oraz jak definiuje się mutanta nowego względem PIT. Wszystkie wskaźniki oceny zostały zdefiniowane w rozdziale 5 — tutaj podano wyłącznie procedury operacyjne służące do ich wyznaczenia.

### Przebieg eksperymentu

Eksperyment składa się z pięciu etapów wykonywanych kolejno dla każdego analizowanego błędu.

**Etap 1 — Dobór błędów.** Ze zbioru Defects4J 3.0.1 wybierane są błędy spełniające kryteria opisane w sekcji 6.2. Wynik: lista par *projekt + numer błędu*.

**Etap 2 — Generacja mutantów.** Dla każdego błędu wygenerowane są mutanty dwiema metodami: przez model językowy (LLM) i przez narzędzie PIT — obie na tej samej wersji kodu. Szczegóły opisano w sekcji 6.3.

**Etap 3 — Weryfikacja i zebranie wyników.** Każdy mutant LLM jest kompilowany; skompilowane mutanty obu źródeł przechodzą pełny przebieg testów. Profil niepowodzeń każdego mutanta jest porównywany z profilem oryginalnego błędu. Szczegóły opisano w sekcji 6.4.

**Etap 4 — Identyfikacja nowych mutantów.** Każdy skompilowany mutant LLM jest porównywany z mutantami PIT na podstawie dwóch filtrów: syntaktycznego i testowego. Mutanty, które nie mają odpowiednika w PIT według obu kryteriów, uznawane są za nowe. Definicja opisana jest w sekcji 6.5.

**Etap 5 — Obliczenie wskaźników i analiza.** Na podstawie zgromadzonych danych obliczane są wskaźniki zdefiniowane w rozdziale 5. Wyniki zestawiane są osobno dla mutantów LLM i PIT i analizowane w odniesieniu do pytań badawczych RQ1–RQ3.

### Materiał badawczy — zbiór danych i kryteria doboru

Podstawą badania jest zbiór **Defects4J 3.0.1** — powszechnie stosowany w badaniach nad testowaniem oprogramowania zestaw rzeczywistych błędów z projektów open-source pisanych w Javie. Każdy błąd jest opatrzony wersją kodu sprzed naprawy (*buggy*), wersją po naprawie (*fixed*), pełnym zestawem testów regresyjnych i zestawem testów wyzwalających — odróżniających kod błędny od poprawionego. Dzięki temu można zmierzyć, czy wygenerowany mutant zachowuje się podobnie do prawdziwego defektu.

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

### Generacja mutantów — LLM i PIT

Dla każdego wybranego błędu mutanty generowane są dwiema metodami na tej samej wersji kodu (*fixed*). Dane wyjściowe obu metod zapisywane są w ujednoliconym formacie rekordu mutanta. Na etapie generacji każdy rekord zawiera co najmniej identyfikator w pliku wynikowym, plik i linię zmiany, kod przed i po mutacji, nazwę reguły, czas generacji oraz znacznik duplikatu. Wyniki kompilacji i uruchomień testów są zbierane później, na etapie weryfikacji.

**Generacja przez model językowy.** Do modelu przekazywane jest polecenie (*prompt*) złożone z instrukcji oraz pełnej metody Java z numerami linii bezwzględnych. Prompt nakazuje wygenerowanie tylko takich mutantów, które stanowią sensowne pojedyncze zmiany w kodzie, bez narzucania z góry stałej liczby propozycji. Model zwraca listę propozycji w formacie JSON zawierającym wyłącznie: numer linii, linię przed zmianą, linię po zmianie oraz nazwę reguły. Parametry generacji są ustalane raz i stosowane do wszystkich wywołań.

**Generacja przez PIT.** PIT uruchamiany jest z pełnym zestawem operatorów (grupa ALL, 29 operatorów) na tych samych klasach, które były kontekstem dla modelu językowego — zapewnia to porównywalność obu podejść. PIT generuje wyłącznie mutanty skompilowane poprawnie (działa na poziomie kodu bajtowego). Wyniki konwertowane są do tego samego formatu rekordu co mutanty LLM.

### Weryfikacja mutantów i zbieranie wyników

Przed uruchomieniem testów każda propozycja mutanta LLM przechodzi trzy etapy filtracji:

1. **Parsowanie odpowiedzi** — sprawdzenie, czy JSON zawiera wszystkie wymagane pola i czy wskazane linie oraz fragmenty kodu odpowiadają rzeczywistej treści metody; odpowiedzi niekompletne lub niespójne są odrzucane.
2. **Identyfikacja duplikatów syntaktycznych** — jeśli dwa mutanty wprowadzają identyczną zmianę w tej samej linii tego samego pliku albo nie zmieniają kodu względem oryginału, są oznaczane jako duplikaty i uwzględniane w metrykach jakości generacji.
3. **Kompilacja** — zmiana jest aplikowana do kodu i projekt jest kompilowany; mutanty, których kod nie kompiluje się, są odrzucane z zapisem przyczyny błędu (niezgodność typów, brakująca metoda, błąd składniowy itp.). Po kompilacji kod jest natychmiast przywracany.

Dla każdego mutanta, który przeszedł kompilację (LLM i PIT), wykonywana jest identyczna procedura:

1. Przygotowywana jest izolowana kopia robocza projektu (wersja *fixed*).
2. Do kopii wprowadzana jest zmiana mutanta.
3. Uruchamiany jest pełny zestaw testów — zapisywana jest lista testów, które nie przeszły (*profil niepowodzeń mutanta*).
4. Oddzielnie gromadzony jest profil niepowodzeń oryginalnego błędu.
5. Na podstawie obu profili obliczane są wskaźniki podobieństwa opisane w rozdziale 5.
6. Kopia robocza jest usuwana — kolejny mutant weryfikowany jest w czystym środowisku.

Każde uruchomienie testów ma określony limit czasu; jego przekroczenie rejestrowane jest osobno jako oddzielna kategoria odrzucenia.

### Definicja mutanta nowego względem PIT

Zamiast grupować mutanty LLM w klastry i porównywać grupy z katalogiem PIT, stosuje się prostszą i przejrzystą definicję opartą na dwóch filtrach stosowanych do każdego mutanta z osobna.

**Mutant LLM uznaje się za nowy względem PIT, jeżeli spełnia oba poniższe warunki jednocześnie:**

1. **Filtr syntaktyczny** — mutant nie odpowiada żadnemu mutantowi PIT wygenerowanemu dla tego samego błędu na poziomie transformacji kodu: żaden mutant PIT nie wprowadza identycznej zmiany (ta sama linia, ta sama modyfikacja) w tym samym pliku.

2. **Filtr testowy** — mutant nie wykazuje tego samego profilu testów nieprzechodzących, co którykolwiek mutant PIT wygenerowany dla tego samego błędu: żaden mutant PIT nie powoduje niepowodzenia dokładnie tego samego zestawu testów.

Mutant spełniający oba warunki nie ma odpowiednika w PIT ani syntaktycznego, ani pod względem profilu testowego — jest to operacyjna i weryfikowalna definicja nowości, niezależna od arbitralnych progów klasyfikacji. Mutanty, które spełniają tylko jeden z warunków, są traktowane jako *częściowo pokryte przez PIT* i analizowane osobno.

---

## Analiza wyników i wnioski

Niniejszy rozdział łączy wyniki eksperymentu z ich interpretacją i bezpośrednimi odpowiedziami na pytania badawcze. Dla każdego pytania (RQ1–RQ3) przedstawiono dane liczbowe, omówiono ich znaczenie, a następnie sformułowano jednoznaczną odpowiedź. Rozdział zamykają synteza porównawcza LLM vs PIT, ograniczenia badania oraz kierunki dalszych prac.

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

### Ograniczenia badania

**Ograniczona generalizowalność (język i zbiór danych).** Eksperyment przeprowadzono wyłącznie na projektach Java z Defects4J 3.0.1. Wyniki mogą nie być w pełni przenoszalne na inne języki programowania (Python, C#, Kotlin) ani na projekty spoza tego benchmarku. Przyszłe badania powinny objąć przynajmniej jeden dodatkowy benchmark.

**Jeden model LLM.** Użyto modelu GPT-4o-mini. Inne modele (Claude 3, DeepSeek, CodeLlama) mogą generować inne rozkłady operatorów i inny compile rate. Wybór modelu był podyktowany kosztami API i dostępnością — nie jest dowodem przewagi GPT-4o-mini nad innymi modelami.

**Heurystyczna klasyfikacja NEW/PARTIAL/EXISTING.** Progi 30% i 80% pokrycia (sekcja 7.8) są arbitralne — kalibrowane na próbie pilotażowej, lecz nie wynikają z teorii. Zmiana progów może wpłynąć na odsetek operatorów NEW.

**Przybliżona ekwiwalentność.** Mutanty przeżywające traktowane są jako proxy dla mutantów ekwiwalentnych. Część z nich to mutanty słabe — niewychwycone przez niedostateczne testy, a nie faktycznie ekwiwalentne. To może zawyżać szacowany Equivalent Mutation Rate.

**Niedeterminizm LLM.** Te same dane wejściowe dają różne mutanty w różnych uruchomieniach. Archiwizacja odpowiedzi API pozwala odtworzyć wyniki, ale nie eliminuje ryzyka, że inne uruchomienie dałoby inny rozkład operatorów.

### Kierunki dalszych badań

Na podstawie wyników i ograniczeń zidentyfikowanych w niniejszej pracy można wskazać następujące kierunki przyszłych badań:

**Replikacja na różnych językach i zbiorach danych.** Eksperyment ograniczony do Javy i Defects4J 3.0.1 powinien być powtórzony dla Pythona (BugsInPy) lub JavaScript, aby zbadać, czy nowość operatorów LLM jest cechą specyficzną dla Javy, czy zjawiskiem ogólnym.

**Porównanie wielu modeli LLM.** Użycie GPT-4o-mini, Claude 3 Haiku i modeli open-source (CodeLlama, DeepSeek-Coder) przy tym samym protokole pozwoli ocenić, czy różnorodność i realizm operatorów zależą od konkretnego modelu, czy są powtarzalną właściwością podejścia LLM jako klasy.

**Poprawa compile rate przez inżynierię promptu i fine-tuning.** Rozszerzenie promptu o informację o typach i sygnaturach metod lub fine-tuning na zbiorze par (kod, skompilowany mutant) może znacząco podnieść CR i obniżyć efektywny koszt generacji.

**Automatyczna detekcja ekwiwalentności.** Przybliżona miara ekwiwalentności przez survived mutants jest niewystarczająca. Przyszłe prace mogą stosować symbolic execution lub SMT solvers do precyzyjniejszego wykrywania ekwiwalentnych mutantów.

**Hybrydowe podejście PIT + LLM.** Najbardziej obiecującym kierunkiem praktycznym jest automatyczny selektor: PIT jako szybka i deterministyczna warstwa bazowa, LLM jako warstwa uzupełniająca dla klas kodu o niskim Ochiai lub braku wykrycia przez PIT.

---

## Podsumowanie

Niniejsza praca dotyczyła zastosowania dużych modeli językowych do generowania operatorów mutacyjnych — reguł wprowadzania celowych błędów w kodzie źródłowym, służących do oceny jakości testów automatycznych. Klasyczne operatory mutacyjne definiowane w narzędziach takich jak PIT stanowią ograniczony i statyczny katalog reguł, który może nie odzwierciedlać typów błędów rzeczywiście popełnianych przez programistów.

W pracy postawiono trzy pytania badawcze: (RQ1) czy LLM generuje operatory mutacyjne nieobecne w katalogu PIT ALL; (RQ2) czy mutanty LLM są bliższe rzeczywistym defektom z Defects4J pod względem zachowania programu niż mutanty PIT; (RQ3) jakie są koszty i wydajność podejścia LLM w porównaniu z PIT. Eksperyment przeprowadzono na zbiorze 605 błędów z 12 projektów Java należących do benchmarku Defects4J 3.0.1 — uznanego standardu w badaniach nad jakością testów.

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

[3] Defects4J:
URL: https://github.com/rjust/defects4j

[4] Paul Ammann and Jeff Offutt Introduction to Software Testing, Cambridge University Press, Cambridge, UK, 2008
URL: https://lira.epac.to/DOCS-TECH/Engineering%20and%20Management/Software%20Testing/Introduction%20to%20Software%20Testing.pdf

[5] R.A. De Millo, R.J. Lipton, and F.G. Sayward. Hints on test data selection: help for the practicing programmer
URL: https://www.st.cs.uni-saarland.de/edu/recommendation-systems/papers/Hints_on_Test_Data_Selection-1.pdf

[6] LLMorpheus: Mutation Testing using Large Language Models
URL: https://arxiv.org/html/2404.09952v2#S1
