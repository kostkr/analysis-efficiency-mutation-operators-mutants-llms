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

- [Rozdział 1 — Wstęp](#rozdział-wstęp)
  - [1.1 Temat i cel pracy](#temat-i-cel-pracy)(DONE)
  - [1.2 Budowa pracy](#budowa-pracy) (TO DO)

- [Rozdział 2 — Testowanie mutacyjne](#rozdział-testowanie-mutacyjne)(TO DO)
  - [2.1 Czym jest mutant?](#czym-jest-mutant)
  - [2.2 Zabicie mutanta i mutation score](#zabicie-mutanta-i-mutation-score)
  - [2.3 Rodzaje mutantów](#rodzaje-mutantów)(TO DO)
    - [2.3.1 Equivalent mutants](#equivalent-mutants)
    - [2.3.2 Duplicate mutants](#duplicate-mutants)
    - [2.3.3 Trivial mutants](#trivial-mutants)
  - [2.4 Proces testowania mutacyjnego krok po kroku](#proces-testowania-mutacyjnego-krok-po-kroku)(TO DO)
  - [2.5 Koszty i problemy praktyczne](#koszty-i-problemy-praktyczne)(TO DO)
    - [2.5.1 Czas wykonania i narzut obliczeniowy](#czas-wykonania-i-narzut-obliczeniowy)(TO DO)
    - [2.5.2 Problem ekwiwalentności](#problem-ekwiwalentności)(TO DO)
    - [2.5.3 Redukcja liczby mutantów (selektory, sampling)](#redukcja-liczby-mutantów-selektory-sampling)(TO DO)

- [Rozdział 3 — Operatory mutacyjne w narzędziach klasycznych (PIT)](#rozdział-3--operatory-mutacyjne-w-narzędziach-klasycznych-pit)(TO DO)
  - [3.1 Czym jest PIT i jak działa](#31-czym-jest-pit-i-jak-działa)
  - [3.2 Model generacji mutantów w PIT](#32-model-generacji-mutantów-w-pit)
  - [3.3 Katalog operatorów: typy i przykłady](#33-katalog-operatorów-typy-i-przykłady)
  - [3.4 Ograniczenia operatorów klasycznych](#34-ograniczenia-operatorów-klasycznych)
    - [3.4.1 Ograniczona różnorodność transformacji](#341-ograniczona-różnorodność-transformacji)
    - [3.4.2 Niedopasowanie do błędów z praktyki](#342-niedopasowanie-do-błędów-z-praktyki)

- [Rozdział 4 — Duże modele językowe w inżynierii oprogramowania](#rozdział-4--duże-modele-językowe-w-inżynierii-oprogramowania)(TO DO)
  - [4.1 Czym są LLM?](#41-czym-są-llm)
  - [4.2 LLM w pracy programisty: typowe zastosowania](#42-llm-w-pracy-programisty-typowe-zastosowania)
  - [4.3 LLM jako generator zmian w kodzie](#43-llm-jako-generator-zmian-w-kodzie)
  - [4.4 Ryzyka i ograniczenia LLM (z perspektywy jakości kodu)](#44-ryzyka-i-ograniczenia-llm-z-perspektywy-jakości-kodu)

- [Rozdział 5 — Repozytoria rzeczywistych błędów jako punkt odniesienia](#rozdział-5--repozytoria-rzeczywistych-błędów-jako-punkt-odniesienia)(TO DO)
  - [5.1 Czym są repozytoria bugów i do czego służą](#51-czym-są-repozytoria-bugów-i-do-czego-służą)
  - [5.2 Defects4J — charakterystyka zbioru](#52-defects4j--charakterystyka-zbioru)
  - [5.3 Jak mierzyć podobieństwo do realnych defektów](#53-jak-mierzyć-podobieństwo-do-realnych-defektów)

- [Rozdział 6 — Problem badawczy i plan badań](#rozdział-6--problem-badawczy-i-plan-badań) (TO DO)
  - [6.1 Problem badawczy (dlaczego PIT może nie wystarczyć)](#61-problem-badawczy-dlaczego-pit-może-nie-wystarczyć)
  - [6.2 Cel badania i wkład pracy](#62-cel-badania-i-wkład-pracy)
  - [6.3 Pytania badawcze (do wyboru)](#63-pytania-badawcze-do-wyboru)
  - [6.4 Kryteria oceny i metryki (mapowanie na wyniki)](#64-kryteria-oceny-i-metryki-mapowanie-na-wyniki)
  - [6.5 Zagrożenia dla rzetelności (validity threats)](#65-zagrożenia-dla-rzetelności-validity-threats)

- [Rozdział 7 — Założenia eksperymentu i metodyka](#rozdział-7--założenia-eksperymentu-i-metodyka)(TO DO)
  - [7.1 Pipeline badania](#71-pipeline-badania)
  - [7.2 Materiał badawczy — dataset i kryteria selekcji](#72-materiał-badawczy--dataset-i-kryteria-selekcji)
  - [7.3 Narzędzia i środowisko techniczne](#73-narzędzia-i-środowisko-techniczne)
  - [7.4 Jednostka analizy — MutantRecord](#74-jednostka-analizy--mutantrecord)
  - [7.5 Generacja mutantów LLM](#75-generacja-mutantów-llm)
    - [7.5.1 Konstrukcja promptów i kontrola parametrów](#751-konstrukcja-promptów-i-kontrola-parametrów)
    - [7.5.2 Walidacja (kompilacja, filtracja błędów)](#752-walidacja-kompilacja-filtracja-błędów)
  - [7.6 Generacja mutantów PIT (baseline)](#76-generacja-mutantów-pit-baseline)
  - [7.7 Uruchomienie testów i zbieranie wyników](#77-uruchomienie-testów-i-zbieranie-wyników)
  - [7.8 Klasteryzacja mutantów LLM w operatory](#78-klasteryzacja-mutantów-llm-w-operatory)
  - [7.9 Dopasowanie operatorów LLM do katalogu PIT](#79-dopasowanie-operatorów-llm-do-katalogu-pit)
  - [7.10 Definicje metryk](#710-definicje-metryk)

- [Rozdział 8 — Wyniki](#rozdział-8--wyniki)(TO DO)
  - [8.1 Statystyki ogólne eksperymentu](#81-statystyki-ogólne-eksperymentu)
  - [8.2 Różnorodność i nowość operatorów LLM](#82-różnorodność-i-nowość-operatorów-llm)
  - [8.3 Podobieństwo mutantów do defektów z Defects4J](#83-podobieństwo-mutantów-do-defektów-z-defects4j)
  - [8.4 Skuteczność względem jakości testów (mutation score)](#84-skuteczność-względem-jakości-testów-mutation-score)
  - [8.5 Koszt i wydajność podejścia](#85-koszt-i-wydajność-podejścia)

- [Rozdział 9 — Opracowanie i dyskusja wyników](#rozdział-9--opracowanie-i-dyskusja-wyników)(TO DO)
  - [9.1 Interpretacja wyników według kryteriów oceny](#91-interpretacja-wyników-według-kryteriów-oceny)
  - [9.2 Porównanie LLM vs PIT: kiedy które podejście ma sens](#92-porównanie-llm-vs-pit-kiedy-które-podejście-ma-sens)
  - [9.3 Ograniczenia badania](#93-ograniczenia-badania)

- [Rozdział 10 — Wnioski i dalsze prace](#rozdział-10--wnioski-i-dalsze-prace)(TO DO)
  - [10.1 Wnioski końcowe](#101-wnioski-końcowe)
  - [10.2 Kierunki dalszych badań](#102-kierunki-dalszych-badań)

- [Podsumowanie](#podsumowanie)
  - [Cel i zakres pracy — przypomnienie](#cel-i-zakres-pracy--przypomnienie)
  - [Najważniejsze wyniki](#najważniejsze-wyniki)
  - [Ograniczenia badania](#ograniczenia-badania)
  - [Kierunki dalszych badań](#kierunki-dalszych-badań)

- [Bibliografia](#bibliografia)

---

## Streszczenie

> ✏️ **Wskazówka do pisania:** Streszczenie piszesz NA KOŃCU, gdy masz już wyniki.
> Napisz 8–12 zdań w następującej kolejności:
> (1) o czym jest praca, (2) jaki problem rozwiązujesz, (3) jak to sprawdzasz,
> (4) 2–3 najważniejsze wyniki liczbowe, (5) jedno zdanie wniosków.
> Bez detali technicznych. Ogólny opis „co i po co".

*[Do napisania jako ostatnie — po przeprowadzeniu eksperymentu i napisaniu pozostałych rozdziałów.]*

Praca dotyczy zastosowania dużych modeli językowych (LLM) do generowania operatorów mutacyjnych — reguł wprowadzania celowych błędów w kodzie źródłowym, służących do oceny jakości testów automatycznych. Klasyczne operatory mutacyjne, definiowane ręcznie w narzędziach takich jak PIT, stanowią ograniczony i statyczny katalog reguł, który może nie odzwierciedlać typów błędów rzeczywiście popełnianych przez programistów. Niniejsza praca weryfikuje, czy LLM są w stanie indukować nowe reguły mutacyjne wykraczające poza ten katalog oraz czy generowane przez nie mutanty są behawioralnie bliższe rzeczywistym defektom oprogramowania.

W ramach badania przeprowadzono jeden kompleksowy eksperyment na zbiorze błędów z repozytorium Defects4J: wygenerowano mutanty przy użyciu LLM oraz narzędzia PIT dla tych samych projektów Java, następnie każdy mutant poddano kompilacji i uruchomieniu testów, a zebrane dane przeanalizowano pod kątem trzech tez badawczych dotyczących nowości, realizmu i wydajności operatorów LLM.

*[Uzupełnić po eksperymencie: X% wygenerowanych operatorów LLM nie posiadało odpowiednika w katalogu PIT. Mediana podobieństwa behawioralnego (proximity) mutantów LLM do rzeczywistych błędów wyniosła Y, wobec Z dla mutantów PIT. Wyniki sugerują, że …]*

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
To pozwala wykraczyć poza ograniczony zestaw reguł dostępnych w klasycznych mutacyjnych narzędziach, a tym samym pomoże zwiększyć jakość testów.
Co z kolei pozwala wzmocnić poziom zaufania do oprogramowania, w tym do automatycznie wygenerowanego kodu.

Celem niniejszej pracy jest analiza efektywności generowania operatorów mutacyjnych (mutantów) poprzez duże modele językowe w porównaniu do klasycznych operatorów.
W ramach badania zostaną przeanalizowane nowe operatory LLM, ich bliskości do rzeczywistych błędów oraz wydajności w porównaniu do klasycznych operatorów.

---

### Budowa pracy

Wygląd zawartości rozdziałów przedstawionych w pracy:

- **Rozdział 1** wprowadza temat i cel pracy, przedstawia zawartość poszczególnych rozdziałów.
- **Rozdział 2** zawiera wprowadzenie do testowania mutacyjnego, definicja pojęcia mutanta i mutation score, rodzajów mutantów oraz procesu testowania mutacyjnego wraz z jego kosztami praktycznymi.
- **Rozdział 3** opisuje klasyczne operatory mutacyjne na przykładzie narzędzia PIT, zasadę działania, katalog operatorów grupy ALL oraz ich ograniczenia.
- **Rozdział 4** wprowadza w tematykę dużych modeli językowych w inżynierii oprogramowania, zastosowania LLM w pracy programisty, koncepcję LLM jako generatora zmian w kodzie oraz związane z tym ryzyka.
- **Rozdział 5** charakteryzuje repozytoria rzeczywistych błędów, omawia zbiór defektu wraz z przykładami dla badania i wprowadza metrykę proximity jako miarę podobieństwa mutanta do rzeczywistego defektu.
- **Rozdział 6** formułuje problem badawczy, cel pracy, pytania badawcze wraz z metrykami oceny oraz omawia zagrożenia dla rzetelności wyników.
- **Rozdział 7** opisuje metodykę eksperymentu, kryteria selekcji błędów, narzędzia i środowisko techniczne, protokoły generacji mutantów.
- **Rozdział 8** zawiera wyniki eksperymentu w postaci tabel statystycznych odpowiadających pytaniom badawczym.
- **Rozdział 9** zawiera opracowanie wyników, interpretację w kontekście pytań badawczych oraz porównanie LLM i PIT.
- **Rozdział 10** formułuje wnioski końcowe i proponuje kierunki dalszych badań.
- **Podsumowanie** jest syntetycznym zestawieniem najważniejszych rezultatów, ograniczeń i propozycji dalszych prac.

---

## Rozdział Testowanie mutacyjne

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

---

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

---

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

### Rodzaje mutantów

> ✏️ **Wskazówka:** To są kluczowe pojęcia, które wrócą w rozdziale 7 przy definicji metryk. Wyraźnie odróżnij wszystkie trzy typy — każdy ma inny wpływ na statystyki eksperymentu.

#### Equivalent mutants

> ✏️ **Wskazówka:** Mutant syntaktycznie różny, ale semantycznie identyczny z oryginałem — żaden test nie może go zabić. Podaj przykład (np. `i = i + 1` vs `i += 1`). Dlaczego to problem: sztucznie obniża mutation score, jest nierozstrzygalny automatycznie.

*[Do napisania]*

#### Duplicate mutants

> ✏️ **Wskazówka:** Mutant wywołujący identyczny profil testowy co inny mutant (te same testy fail/pass). Różni się od equivalent: duplicate może być „zabity", ale nie wnosi nowej informacji o jakości testów. Wpływ: zawyża rozmiar zbioru mutantów.

*[Do napisania]*

#### Trivial mutants

> ✏️ **Wskazówka:** Mutanty wykrywane przez praktycznie każdy test — łatwe do zabicia, nie różnicują jakości zestawu testów. Często generowane przez proste operatory (np. zmiana stałej na 0). Ich obecność może zawyżać mutation score bez realnej informacji o sile testów.

*[Do napisania]*

---

### Proces testowania mutacyjnego krok po kroku

> ✏️ **Wskazówka:** Lista numerowana — sekwencja od kodu źródłowego do raportu końcowego. Bez szczegółów implementacyjnych. Uwzględnij: generację mutantów → kompilację → uruchomienie testów → klasyfikację (killed/survived) → obliczenie mutation score. Opcjonalnie: prosty diagram przepływu.

*[Do napisania]*

---

### Koszty i problemy praktyczne

> ✏️ **Wskazówka:** Ta sekcja uzasadnia, dlaczego testowanie mutacyjne nie jest powszechnie stosowane w przemyśle. Każda podsekcja to osobny problem — połącz je na końcu krótkim akapitem podsumowującym.

#### Czas wykonania i narzut obliczeniowy

> ✏️ **Wskazówka:** Podaj rząd wielkości: dla projektu z N testami i M mutantami czas rośnie jak N×M. Przytoczyć można przykład z literatury lub własne obserwacje z Defects4J. Techniki przyspieszenia: równoległość, bytecode mutation (PIT).

*[Do napisania]*

#### Problem ekwiwalentności

> ✏️ **Wskazówka:** Rozwiń punkt 2.4.1 — dlaczego automatyczne wykrywanie equivalent mutants jest nierozstrzygalne (problem stopu). Konsekwencje dla praktyki: ręczna inspekcja, przybliżone metryki (np. survived mutants jako proxy).

*[Do napisania]*

#### Redukcja liczby mutantów (selektory, sampling)

> ✏️ **Wskazówka:** Dwa główne podejścia: (1) mutant sampling — losowe próbkowanie podzbioru mutantów; (2) selective mutation — ograniczenie do podzbioru operatorów. Krótko o badaniach pokazujących, że niewielki podzbiór operatorów wystarczy do uzyskania dobrego przybliżenia pełnego mutation score.

*[Do napisania]*

---

## Rozdział 3 — Operatory mutacyjne w narzędziach klasycznych (PIT)

> ✏️ **Wskazówka do rozdziału:** Rozdział skupia się wyłącznie na narzędziu PIT jako reprezentancie klasycznego podejścia do testowania mutacyjnego. Po przeczytaniu czytelnik powinien wiedzieć: czym jest PIT, jak generuje mutanty, jakie operatory zawiera katalog ALL i — co najważniejsze — jakie są jego ograniczenia. Ta ostatnia część jest bezpośrednim uzasadnieniem dla badania opisanego w rozdziale 6.

---

### 3.1 Czym jest PIT i jak działa

> ✏️ **Wskazówka:** Krótki opis narzędzia: język Java, operuje na bytecode JVM (nie na kodzie źródłowym — to ważna właściwość), integracja z Maven/Gradle, generuje raporty HTML. Podkreśl, że PIT jest *de facto* standardem w testowaniu mutacyjnym dla Javy. 1–2 akapity.

*[Do napisania]*

---

### 3.2 Model generacji mutantów w PIT

> ✏️ **Wskazówka:** Opisz jak PIT generuje mutanty: analiza bytecode → aplikacja reguły transformacji → zapis zmutowanej klasy. Nie wchodź w szczegóły JVM — wystarczy intuicja. Zaznacz, że operowanie na bytecode gwarantuje kompilację mutantów (co odróżnia PIT od generatorów tekstowych, np. LLM). Cecha istotna dla późniejszego porównania compile rate.

*[Do napisania]*

---

### 3.3 Katalog operatorów: typy i przykłady

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

### 3.4 Ograniczenia operatorów klasycznych

> ✏️ **Wskazówka:** To jest kluczowa sekcja uzasadniająca całe badanie. Pisz konkretnie — nie „PIT jest ograniczony", ale „PIT nie uwzględnia X, Y, Z". Zakończ wyraźnym stwierdzeniem: ta luka uzasadnia poszukiwanie innych źródeł reguł mutacyjnych.

#### 3.4.1 Ograniczona różnorodność transformacji

> ✏️ **Wskazówka:** Katalog PIT ALL obejmuje ~12 operatorów — to skończony, statyczny zestaw reguł wybranych przez ekspertów. Porównaj z przestrzenią możliwych błędów: brakujące null-checki, błędy inicjalizacji, niepoprawna kolejność operacji, błędy obsługi wyjątków, problemy z współbieżnością — żadne z tych nie ma odpowiednika w ALL. Podaj liczby: ile operatorów ma PIT ALL vs ile klas błędów wyróżnia literatura (np. Defects4J taxonomy).

*[Do napisania]*

#### 3.4.2 Niedopasowanie do błędów z praktyki

> ✏️ **Wskazówka:** Powołaj się na badania pokazujące, że operatory PIT nie odpowiadają rozkładowi rzeczywistych defektów (literatura: Andrews et al., Daran & Thévenod-Fosse, lub podobne). Wspomnij o koncepcji „realistic mutation operators" jako kierunku badań. To bezpośrednio prowadzi do pytania: czy LLM, trenowany na historii bugów, może generować realistyczniejsze mutanty?

*[Do napisania]*

---

## Rozdział 4 — Duże modele językowe w inżynierii oprogramowania

> ✏️ **Wskazówka do rozdziału:** Rozdział wprowadza czytelnika w tematykę LLM z perspektywy inżynierii oprogramowania — nie z perspektywy teorii ML. Unikaj szczegółów architektury transformerów. Skup się na: czym są LLM w kontekście kodu, do czego są używane w SE, i — kluczowe dla pracy — jakie są ich możliwości i ograniczenia jako generatora zmian w kodzie.

---

### 4.1 Czym są LLM?

> ✏️ **Wskazówka:** Dwa akapity: (1) intuicja — modele trenowane na ogromnych zbiorach tekstu (w tym kodu), modelują statystyczne zależności między tokenami; (2) kontekst do pracy — LLM „widział" miliardy linii kodu i historii bugów podczas treningu, co daje mu wiedzę o typowych wzorcach błędów. Wspomnij o kluczowych modelach: GPT-4, Claude, Gemini, CodeLlama. Odnieś się do Codex (Chen et al. 2021) jako pionierskiej pracy.

*[Do napisania]*

---

### 4.2 LLM w pracy programisty: typowe zastosowania

> ✏️ **Wskazówka:** Lista 5–6 zastosowań z jednozdaniowym komentarzem każde: generowanie kodu (Copilot), APR (automatyczna naprawa błędów), code review, generowanie testów, analiza podatności, dokumentacja. Dla każdego podaj przykład narzędzia lub pracy naukowej. Cel: pokazać, że LLM są aktywnie stosowane w SE — to uzasadnia ich użycie w badaniu.

*[Do napisania]*

---

### 4.3 LLM jako generator zmian w kodzie

> ✏️ **Wskazówka:** To jest bezpośrednie tło dla Twojego eksperymentu. Opisz koncepcję: LLM jako „generator hipotez mutacyjnych" — model dostaje kontekst kodu + instrukcję i zwraca zmodyfikowany fragment + opis reguły. Kluczowa zaleta: reguła jest indukcyjna (wynika z wzorców w danych), a nie ręcznie specyfikowana. Wspomnij o wcześniejszych pracach stosujących LLM do generowania mutantów (MutationGPT, ChatMut — jeśli dostępne w literaturze).

*[Do napisania]*

---

### 4.4 Ryzyka i ograniczenia LLM (z perspektywy jakości kodu)

> ✏️ **Wskazówka:** Wyważ obraz — LLM mają istotne ograniczenia istotne dla Twojego badania. Omów: (1) niedeterminizm — różne wyniki dla tego samego wejścia, problemy z reprodukowalnością; (2) halucynacje — generowanie nieskompilowanego lub semantycznie niepoprawnego kodu; (3) brak gwarancji realizmu — wygenerowana zmiana może być arbitralna, nie symulować prawdziwego błędu; (4) zależność od jakości promptu. Zaznacz, że protokół eksperymentu (filtracja, walidacja kompilacji) adresuje te ograniczenia.

*[Do napisania]*

---

## Rozdział 5 — Repozytoria rzeczywistych błędów jako punkt odniesienia

> ✏️ **Wskazówka do rozdziału:** Rozdział wyjaśnia, dlaczego Defects4J jest używany w badaniu i co konkretnie z niego wykorzystujesz. Kluczowy element: pojęcie `FailBug` (zbiór testów wyzwalających dla rzeczywistego błędu) — to fundament metryki proximity, która pojawi się w rozdziale 7. Opisz dataset konkretnie: liczby, projekty, metadane.

---

### 5.1 Czym są repozytoria bugów i do czego służą

> ✏️ **Wskazówka:** Definicja: kuratowane zbiory defektów z historii repozytoriów kodu, zawierające wersję przed/po naprawie, opis błędu i testy wykrywające. Zastosowania w badaniach: benchmarking technik naprawy (APR), testowania, analizy jakości. Wspomnij o innych repozytoriach (QuixBugs, Bears, ConDefects) jako kontekście — ale skup się na tym, dlaczego Defects4J jest najodpowiedniejszy dla Javy.

*[Do napisania]*

---

### 5.2 Defects4J — charakterystyka zbioru

> ✏️ **Wskazówka:** Opisz dataset konkretnie: Just et al. 2014, 800+ błędów, projekty Java open-source. Dodaj tabelę projektów (Commons Lang, Commons Math, Joda-Time, JFreeChart, Closure Compiler) z liczbą błędów. Wymień metadane dostępne dla każdego błędu: wersja buggy/fixed, modified.classes, triggering tests, CLI (`checkout`, `compile`, `test`). Zaznacz, że CLI umożliwia w pełni zautomatyzowaną reprodukcję każdego błędu.

| Projekt | Opis | Liczba błędów (przykładowo) |
|---|---|---|
| Apache Commons Lang | Narzędzia dla klas Java | ~65 |
| Apache Commons Math | Biblioteka matematyczna | ~106 |
| Joda-Time | Obsługa dat i czasu | ~27 |
| JFreeChart | Biblioteka wykresów | ~26 |
| Closure Compiler | Kompilator JavaScript | ~176 |

*[Do uzupełnienia po finalnym wyborze projektów do eksperymentu]*

---

### 5.3 Jak mierzyć podobieństwo do realnych defektów

> ✏️ **Wskazówka:** Wprowadź pojęcie `FailBug` — zbiór testów wyzwalających dla danego błędu (testy, które nie przechodzą dla wersji buggy, ale przechodzą dla fixed). Wyjaśnij koncepcję metryki proximity: Jaccard(`FailMut`, `FailBug`) — im wyższy wynik, tym bardziej mutant „zachowuje się jak" prawdziwy błąd. Uzasadnij, dlaczego to jest dobra miara realizmu mutanta. Wspomnij o ograniczeniach: proximity = 0 nie oznacza złego mutanta, może oznaczać brak pokrycia testowego.

*[Do napisania]*

---

## Rozdział 6 — Problem badawczy i plan badań

> ✏️ **Wskazówka do rozdziału:** To jest „serce" pracy naukowej — formalne sformułowanie problemu badawczego i metodologiczne podstawy eksperymentu. Pisz precyzyjnie: każde pytanie badawcze powinno być weryfikowalne, każda metryka powinna mieć jasną definicję. Rozdział łączy teorię (rozdziały 2–5) z eksperymentem (rozdział 7).

---

### 6.1 Problem badawczy (dlaczego PIT może nie wystarczyć)

> ✏️ **Wskazówka:** Synteza rozdziałów 2–5 w jedno sformułowanie problemu: klasyczne narzędzia (PIT) mają ograniczony, statyczny katalog operatorów niedopasowany do rzeczywistych defektów, podczas gdy LLM posiadają wiedzę o wzorcach bugów z danych treningowych. Pytanie: czy LLM mogą generować wartościowe operatory mutacyjne wykraczające poza katalog PIT? 2–3 akapity.

*[Do napisania]*

---

### 6.2 Cel badania i wkład pracy

> ✏️ **Wskazówka:** Jawnie sformułuj cel (np. „Celem pracy jest empiryczna weryfikacja, czy LLM generują operatory mutacyjne o wyższym realizmie i różnorodności niż PIT ALL") i wkład (ang. contribution): (1) empiryczne porównanie LLM vs PIT na zbiorze Defects4J; (2) metodologia klasteryzacji mutantów LLM w operatory; (3) metryka proximity jako narzędzie oceny realizmu mutantów. Lista punktowana.

*[Do napisania]*

---

### 6.3 Pytania badawcze (do wyboru)

> ✏️ **Wskazówka:** Sformułuj 3 pytania badawcze (Research Questions) odpowiadające tezom z eksperymentu. Format: RQ1, RQ2, RQ3 — każde jako jedno zdanie pytające. Każde pytanie powinno być: konkretne (mierzalne), empirycznie weryfikowalne, powiązane z metryką z sekcji 6.4. Przykład formatu: „RQ1: Jaki odsetek operatorów mutacyjnych indukowanych przez LLM nie ma odpowiednika w katalogu PIT ALL?"

*[Do napisania]*

---

### 6.4 Kryteria oceny i metryki (mapowanie na wyniki)

> ✏️ **Wskazówka:** Tabela mapująca: RQ → metryka → sekcja wyników (rozdział 8). Każda metryka = wzór + jednozdaniowa interpretacja. Metryki do uwzględnienia: % nowych operatorów, compile rate, mutation score, proximity (Jaccard), duplicate rate, equivalent rate, liczba zastosowań operatora. Ta sekcja jest punktem odniesienia dla całego rozdziału 8.

| Metryka | Wzór | Interpretacja | Powiązane RQ |
|---|---|---|---|
| % nowych operatorów | `#NEW / #total_operators` | Odsetek operatorów LLM bez odpowiednika w PIT | RQ1 |
| Compile rate | `#compile=1 / #all` | Odsetek mutantów kompilujących się poprawnie | RQ1, RQ3 |
| Mutation score | `#killed / #compiled` | Odsetek skompilowanych mutantów wykrytych przez testy | RQ2, RQ3 |
| Proximity | `\|FailMut ∩ FailBug\| / \|FailMut ∪ FailBug\|` | Behawioralne podobieństwo mutanta do rzeczywistego błędu | RQ2 |
| Duplicate rate | `#duplicates / #all` | Odsetek mutantów z identycznym profilem testowym | RQ3 |
| Equivalent rate | `#(compile=1, killed=0) / #compiled` | Przybliżenie odsetka mutantów semantycznie równoważnych | RQ3 |
| Liczba zastosowań | `#mutants_per_operator` | Średnia liczba miejsc w kodzie, gdzie reguła ma zastosowanie | RQ1, RQ3 |

*[Do uzupełnienia po finalnym ustaleniu pytań badawczych]*

---

### 6.5 Zagrożenia dla rzetelności (validity threats)

> ✏️ **Wskazówka:** Standardowy element prac empirycznych — pisz uczciwie. Podziel zagrożenia na 4 kategorie (wg Wohlin et al.): construct validity (czy mierzymy to, co chcemy mierzyć?), internal validity (czy wyniki są wiarygodne?), external validity (generalizowalność), reliability (reprodukowalność). Każde zagrożenie = 1–2 zdania opisu + jak je mitigujesz.

*[Do napisania]*

---

## Rozdział 7 — Założenia eksperymentu i metodyka

> ✏️ **Wskazówka do rozdziału:** Rozdział musi być na tyle szczegółowy, żeby inny badacz mógł odtworzyć eksperyment. Pisz precyzyjnie: konkretne liczby (K mutantów per bug, timeouty), konkretne narzędzia z wersjami, konkretne kryteria (progi Jaccarda). Każda decyzja projektowa powinna być uzasadniona — dlaczego tak, a nie inaczej.

---

### 7.1 Pipeline badania

> ✏️ **Wskazówka:** Opisz eksperyment jako sekwencję numerowanych kroków (8 kroków): (1) selekcja bugów z Defects4J, (2) generacja mutantów LLM, (3) generacja mutantów PIT, (4) kompilacja każdego mutanta, (5) uruchomienie testów, (6) klasteryzacja mutantów LLM w operatory, (7) klasyfikacja operatorów LLM (NEW/PARTIAL/EXISTING), (8) obliczenie metryk i analiza. Każdy krok = jeden krótki akapit. Cel: czytelnik widzi całość przed wejściem w szczegóły.

*[Do napisania]*

---

### 7.2 Materiał badawczy — dataset i kryteria selekcji

> ✏️ **Wskazówka:** Podaj konkretnie: N = [liczba] błędów z projektów [lista]. Kryteria selekcji jako lista numerowana: (1) kompilowalność bazowa (defects4j compile bez błędów), (2) istnienie testów wyzwalających (|FailBug| ≥ 1), (3) akceptowalny czas testów (< 10 min), (4) ograniczony zakres zmiany (≤ X plików). Dla każdego kryterium uzasadnij wybór progu. Dodaj tabelę z finalnymi projektami i liczbą wybranych bugów.

*[Do napisania — uzupełnić po przeprowadzeniu selekcji]*

---

### 7.3 Narzędzia i środowisko techniczne

> ✏️ **Wskazówka:** Tabela narzędzi z kolumnami: Narzędzie | Wersja | Rola w eksperymencie. Uwzględnij: Defects4J CLI, PIT, model LLM (nazwa + wersja API), model embeddingowy, algorytm klasteryzacji, Python, Podman. Krótki opis środowiska uruchomieniowego: kontener Podman, izolacja, reprodukowalność.

| Narzędzie | Wersja | Rola w eksperymencie |
|---|---|---|
| Defects4J CLI | [wersja] | Checkout, compile, test dla każdego mutanta |
| PIT (Pitest) | [wersja] | Generacja mutantów klasycznych (ALL) |
| *[model LLM]* | [wersja API] | Generacja mutantów LLM + opisy reguł |
| *[model embeddingowy]* | [wersja] | Wektoryzacja opisów reguł do klasteryzacji |
| *[algorytm klasteryzacji]* | — | Grupowanie mutantów LLM w operatory |
| Python 3.x | [wersja] | Automatyzacja pipeline'u |
| Podman | [wersja] | Kontener z środowiskiem Defects4J |

*[Do uzupełnienia po finalnym ustaleniu wersji narzędzi]*

---

### 7.4 Jednostka analizy — MutantRecord

> ✏️ **Wskazówka:** Wyjaśnij, że wszystkie dane z eksperymentu są zapisywane jako ujednolicony rekord JSON (MutantRecord). Pokaż schemat z komentarzem do każdego pola. Podkreśl: wspólny schemat dla mutantów LLM i PIT umożliwia obliczenie wszystkich metryk z jednego strumienia danych. Wskaż pola specyficzne dla LLM (rule_description, operator_cluster_id) i PIT (pit_mutator_type).

```json
{
  "id": "Lang-1-llm-042",
  "source": "LLM",
  "project": "Lang",
  "bug_id": 1,
  "file": "src/main/java/.../StringUtils.java",
  "location": { "class": "StringUtils", "method": "isEmpty", "line": 234 },
  "patch": "--- a/StringUtils.java\n+++ b/StringUtils.java\n...",
  "rule_description": "Negacja strażnika null-check na wejściu metody",
  "compile": 1,
  "compile_error_type": null,
  "tests_run_count": 312,
  "failing_tests_set": ["org.apache.commons.lang3.StringUtilsTest#testIsEmpty"],
  "killed": 1,
  "time_cost_s": 47.3,
  "operator_cluster_id": "cluster_07",
  "pit_mutator_type": null,
  "pit_match_label": null,
  "proximity": 0.71
}
```

*[Do uzupełnienia: ewentualnie rozszerzyć schemat po ustaleniu finalnej struktury danych]*

---

### 7.5 Generacja mutantów LLM

> ✏️ **Wskazówka:** Opisz protokół generacji od A do Z: przygotowanie kontekstu → konstrukcja promptu → parametry generacji → parsowanie odpowiedzi → zapis. Każdy element to osobny blok. Uzasadnij każdy wybór: dlaczego ±20 linii kontekstu? Dlaczego temperatura X? Dlaczego K mutantów per bug?

#### 7.5.1 Konstrukcja promptów i kontrola parametrów

> ✏️ **Wskazówka:** Opisz strukturę promptu: (1) instrukcja systemowa, (2) kontekst kodu (±N linii wokół miejsca zmiany), (3) żądanie K wariantów błędu z opisem reguły i formatem diff. Podaj parametry: K = [liczba], temperatura = [wartość], seed = [wartość], model = [nazwa]. Uzasadnij każdy wybór parametru. Ewentualnie dołącz przykładowy prompt w sekcji Załączniki.

*[Do napisania — uzupełnić po ustaleniu finalnej wersji promptu]*

#### 7.5.2 Walidacja (kompilacja, filtracja błędów)

> ✏️ **Wskazówka:** Opisz filtrację odpowiedzi LLM przed kompilacją: (1) parsowanie patcha (czy da się wyekstrahować unified diff?), (2) weryfikacja składni (opcjonalnie), (3) odrzucenie nieparsowanych odpowiedzi z dokumentacją przyczyny. Podaj statystyki, które zbierasz: parse rate, compile rate, jako metryki jakości promptu.

*[Do napisania]*

---

### 7.6 Generacja mutantów PIT (baseline)

> ✏️ **Wskazówka:** Opisz konfigurację PIT: mutators=ALL, targetClasses (z modified.classes), targetTests (wszystkie testy projektu). Jak mapujesz wyniki PIT (raport XML) do MutantRecord? Jakie są różnice względem mutantów LLM w kontekście kompilacji (PIT zawsze generuje kompilowalne mutanty)? Czy uruchamiasz PIT dla wersji buggy czy fixed? Uzasadnij.

*[Do napisania]*

---

### 7.7 Uruchomienie testów i zbieranie wyników

> ✏️ **Wskazówka:** Opisz procedurę dla KAŻDEGO mutanta (identyczną dla LLM i PIT): (1) skopiuj plik z patchem do kontenera, (2) utwórz backup oryginału, (3) zastosuj patch, (4) defects4j compile [timeout], (5) defects4j test -r [timeout], (6) przywróć oryginał, (7) oblicz proximity. Podaj timeouty (900s compile, 1800s test) i uzasadnij. Zaznacz mechanizm restore w bloku finally — gwarancja integralności środowiska.

*[Do napisania — uzupełnić o doświadczenia z rzeczywistego przebiegu eksperymentu]*

---

### 7.8 Klasteryzacja mutantów LLM w operatory

> ✏️ **Wskazówka:** Opisz proces grupowania mutantów LLM w operatory: (1) wektoryzacja rule_description modelem embeddingowym, (2) klasteryzacja algorytmem [HDBSCAN/k-means] z uzasadnieniem wyboru, (3) definicja operatora (nazwa, opis centroidu, przykładowe patche), (4) ręczna weryfikacja spójności klastrów przez 2 oceniających, (5) zapis cluster_id do MutantRecord. Podaj konkretne parametry algorytmu i metrykę jakości klastrów (np. silhouette score).

*[Do napisania — uzupełnić po przeprowadzeniu klasteryzacji]*

---

### 7.9 Dopasowanie operatorów LLM do katalogu PIT

> ✏️ **Wskazówka:** Opisz algorytm klasyfikacji: NEW/PARTIAL/EXISTING. Dwa kroki: A1 (Jaccard profili testowych — progi 0.9 i 0.4) i A2 (heurystyki typów zmian w patchu — dla przypadków nierozstrzygniętych przez A1). Pokaż tabelę wzorców zmian → etykiet (z oryginalnej pracy). Wyjaśnij jak etykieta klastra wynika z rozkładu etykiet mutantów (reguła ≥50%).

*[Do uzupełnienia o finalną wersję algorytmu po kalibracji progów]*

---

### 7.10 Definicje metryk

> ✏️ **Wskazówka:** Formalna tabela wszystkich metryk (taka sama jak w sekcji 6.4, ale z pełnymi wzorami i odniesieniami do pól MutantRecord). Każda metryka = wzór + interpretacja + z jakich pól MutantRecord jest obliczana. To jest punkt odniesienia dla sekcji 8.

| Metryka | Wzór | Interpretacja |
|---|---|---|
| % nowych operatorów | `#NEW / #total_operators` | Odsetek operatorów LLM bez odpowiednika w PIT |
| Compile rate | `#compile=1 / #all` | Odsetek mutantów kompilujących się poprawnie |
| Mutation score | `#killed / #compiled` | Odsetek skompilowanych mutantów wykrytych przez testy |
| Proximity | `\|FailMut ∩ FailBug\| / \|FailMut ∪ FailBug\|` | Behawioralne podobieństwo mutanta do rzeczywistego błędu (0–1) |
| Duplicate rate | `#duplicates / #all` | Odsetek mutantów z identycznym `failing_tests_set` |
| Equivalent rate | `#(compile=1, killed=0) / #compiled` | Przybliżenie odsetka mutantów semantycznie równoważnych |
| Liczba zastosowań | `#mutants_per_operator` | Średnia liczba miejsc w kodzie, gdzie reguła ma zastosowanie |

---

## Rozdział 8 — Wyniki

> ✏️ **Wskazówka do rozdziału:** Tylko fakty i liczby — bez interpretacji. Tabele, wykresy, wartości liczbowe. Interpretacja idzie do rozdziału 9. Każdą tabelę uzupełnij po eksperymencie. Jeśli wynik jest nieoczekiwany, zanotuj go — ale nie wyjaśniaj tu dlaczego.

---

### 8.1 Statystyki ogólne eksperymentu

> ✏️ **Wskazówka:** Tabela zbiorcza: liczba projektów, bugów, wygenerowanych mutantów (LLM i PIT osobno), compile rate, mutation score, łączny czas eksperymentu. To jest „big picture" — czytelnik musi wiedzieć, jaka jest skala eksperymentu.

*[Do uzupełnienia po eksperymencie]*

| Statystyka | Wartość |
|---|---|
| Liczba projektów | |
| Liczba analizowanych błędów (N) | |
| Liczba mutantów LLM łącznie | |
| Liczba mutantów PIT łącznie | |
| Mutanty LLM — skompilowane | |
| Mutanty PIT — skompilowane | |
| Mutanty LLM — zabite | |
| Mutanty PIT — zabite | |
| Łączny czas eksperymentu | |

---

### 8.2 Różnorodność i nowość operatorów LLM

> ✏️ **Wskazówka:** Tabela rozkładu etykiet (NEW/PARTIAL/EXISTING) z liczba operatorów i %. Tabela z przykładami 2–3 operatorów NEW — nazwa, opis reguły, przykładowy patch, liczba mutantów w klastrze. Opcjonalnie: wykres kołowy lub słupkowy rozkładu etykiet.

*[Do uzupełnienia po eksperymencie]*

| Etykieta | Liczba operatorów | % operatorów |
|---|---|---|
| NEW | | |
| PARTIAL | | |
| EXISTING | | |
| **Razem** | | |

---

### 8.3 Podobieństwo mutantów do defektów z Defects4J

> ✏️ **Wskazówka:** Tabela statystyk opisowych proximity (mediana, średnia, odchylenie standardowe, Q1, Q3, odsetek > 0.5) dla LLM i PIT osobno. Wynik testu statystycznego (Mann-Whitney U, p-value). Opcjonalnie: boxplot LLM vs PIT.

*[Do uzupełnienia po eksperymencie]*

| Statystyka | LLM | PIT |
|---|---|---|
| Mediana Proximity | | |
| Średnia Proximity | | |
| Odchylenie standardowe | | |
| Q1 (25. percentyl) | | |
| Q3 (75. percentyl) | | |
| Odsetek mutantów z Proximity > 0.5 | | |
| Wynik testu Mann-Whitney U | | |
| Mutation score | | |

---

### 8.4 Skuteczność względem jakości testów (mutation score)

> ✏️ **Wskazówka:** Porównanie mutation score LLM vs PIT (wszystkie mutanty i osobno dla par EXISTING/PARTIAL). Tabela: metryki dla LLM (all), PIT (all), LLM (EXISTING/PARTIAL), matched PIT. Opcjonalnie: rozkład mutation score per projekt.

*[Do uzupełnienia po eksperymencie]*

| Metryka | LLM (all) | PIT (all) | LLM (EXISTING/PARTIAL) | Matched PIT |
|---|---|---|---|---|
| Mutation score | | | | |
| Compile rate | | | | |
| Duplicate rate | | | | |
| Equivalent rate | | | | |
| Mediana Proximity | | | | |
| Średnia liczba zastosowań | | | | |

---

### 8.5 Koszt i wydajność podejścia

> ✏️ **Wskazówka:** Dane o kosztach operacyjnych: czas generacji per bug (LLM vs PIT), koszt API (jeśli dotyczy), compile rate (= odsetek zmarnowanych wywołań API dla LLM), rozkład czasu uruchomienia testów. Tabela lub krótki tekst z liczbami. Te dane są potrzebne do oceny praktycznej użyteczności podejścia.

*[Do uzupełnienia po eksperymencie]*

---

## Rozdział 9 — Opracowanie i dyskusja wyników

> ✏️ **Wskazówka do rozdziału:** Tu łączysz liczby z sensem. Każda podsekcja odpowiada na jedno z pytań badawczych. Pisz: co wyniki oznaczają, dlaczego są takie a nie inne, jakie są alternatywne interpretacje. Nie powtarzaj liczb bez komentarza — każda liczba powinna mieć interpretację.

---

### 9.1 Interpretacja wyników według kryteriów oceny

> ✏️ **Wskazówka:** Podziel na bloki odpowiadające RQ1, RQ2, RQ3. Dla każdego: (1) przypomnij pytanie badawcze i kluczową metrykę, (2) podaj wynik liczbowy, (3) zinterpretuj — co to oznacza dla hipotezy, (4) omów kontekst (np. wysoki mutation score PIT to nie zawsze zaleta, bo trivial mutants). Uwzględnij nieoczekiwane wyniki i zaproponuj wyjaśnienia.

*[Do napisania po eksperymencie]*

---

### 9.2 Porównanie LLM vs PIT: kiedy które podejście ma sens

> ✏️ **Wskazówka:** Synteza porównawcza: w jakich sytuacjach LLM przewyższa PIT (np. wykrywanie realistycznych błędów, nowe typy operatorów), kiedy PIT jest lepszym wyborem (szybkość, deterministyczność, brak kosztów API, wysoki compile rate). Zaproponuj praktyczne rekomendacje: kiedy warto łączyć oba podejścia? Czy LLM może uzupełniać PIT, a nie go zastępować?

*[Do napisania po eksperymencie]*

---

### 9.3 Ograniczenia badania

> ✏️ **Wskazówka:** Pisz uczciwie i konkretnie. Lista ograniczeń z krótkim komentarzem do każdego: (1) ograniczenie do Javy i Defects4J (generalizowalność?), (2) heurystyczna klasyfikacja NEW/EXISTING (arbitralność progów), (3) niedeterminizm LLM (reprodukowalność), (4) przybliżenie equivalent rate, (5) subiektywność ręcznej weryfikacji klastrów. Każde ograniczenie = jak wpływa na wnioski + jak można je adresować w przyszłości.

*[Do napisania po eksperymencie]*

---

## Rozdział 10 — Wnioski i dalsze prace

> ✏️ **Wskazówka do rozdziału:** Krótki, syntetyczny rozdział. Unikaj powtarzania szczegółów z rozdziałów 8–9. Każdy wniosek = jedno zdanie z odpowiedzią na pytanie badawcze + jedno zdanie implikacji. Kierunki dalszych badań powinny być konkretne i wynikać z ograniczeń opisanych w 9.3.

---

### 10.1 Wnioski końcowe

> ✏️ **Wskazówka:** Trzy akapity — jeden per RQ. Każdy akapit: (1) pytanie badawcze, (2) wynik (potwierdzone/częściowo/odrzucone), (3) kluczowa liczba uzasadniająca, (4) implikacja praktyczna. Na końcu jeden akapit wniosku ogólnego: co to znaczy dla przyszłości testowania mutacyjnego.

*[Do napisania po eksperymencie]*

---

### 10.2 Kierunki dalszych badań

> ✏️ **Wskazówka:** 4–5 konkretnych kierunków wynikających z ograniczeń i obserwacji z eksperymentu. Każdy kierunek = jedno zdanie pytania + jedno zdanie uzasadnienia dlaczego warto. Przykłady: rozszerzenie na inne języki (Python, JavaScript), porównanie różnych modeli LLM, automatyzacja klastryzacji, formalna klasyfikacja semantyczna operatorów na podstawie AST diff.

*[Do napisania]*

---

## Podsumowanie

> ✏️ **Wskazówka:** Podsumowanie to skrócona wersja całej pracy — piszesz je jako ostatnie. Cel: czytelnik, który przeczyta tylko podsumowanie, powinien wiedzieć: jaki był problem, jak go rozwiązałeś i co z tego wynika. Maksymalnie 1–1.5 strony.

---

### Cel i zakres pracy — przypomnienie

> ✏️ **Wskazówka:** 2–3 zdania przypominające cel pracy. Nie przepisuj Wstępu — napisz to inaczej, zwięźlej. Wspomnij skalę eksperymentu (N bugów, M mutantów).

*[Do napisania po eksperymencie]*

---

### Najważniejsze wyniki

> ✏️ **Wskazówka:** 3–5 wyników liczbowych. Każdy wynik = jedno zdanie z wartością + jedno zdanie interpretacji. Format: „RQ1: X% operatorów LLM nie posiadało odpowiednika w PIT ALL, co oznacza…". Nie interpretuj głęboko — to jest tu podsumowanie, nie dyskusja.

*[Do napisania po eksperymencie]*

---

### Ograniczenia badania

> ✏️ **Wskazówka:** 3–4 zdania. Skrót z sekcji 9.3 — tylko najważniejsze ograniczenia wpływające na generalizowalność wniosków.

*[Do napisania po eksperymencie]*

---

### Kierunki dalszych badań

> ✏️ **Wskazówka:** 3–4 punkty. Skrót z sekcji 10.2 — najbardziej obiecujące kierunki.

*[Do napisania po eksperymencie]*

---

## Bibliografia

TO DO
