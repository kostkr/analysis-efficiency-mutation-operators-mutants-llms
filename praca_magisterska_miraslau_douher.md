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

- [Streszczenie](#streszczenie)
- [Rozdział 1 — Wstęp](#rozdział-1--wstęp)
  - [1.1 Temat i cel pracy](#11-temat-i-cel-pracy)
  - [1.2 Budowa pracy](#12-budowa-pracy)
- [Rozdział 2 — Opis planowanych badań i tezy badawcze](#rozdział-2--opis-planowanych-badań-i-tezy-badawcze)
  - [2.1 Pipeline badania](#21-pipeline-badania)
  - [2.2 Tezy badawcze](#22-tezy-badawcze)
    - [Teza 1 — Czy LLM generuje nowe operatory mutacyjne?](#teza-1--czy-llm-generuje-nowe-operatory-mutacyjne)
    - [Teza 2 — Czy operatory LLM są bliższe prawdziwym usterkom?](#teza-2--czy-operatory-llm-są-bliższe-prawdziwym-usterkom)
    - [Teza 3 — Czy operatory LLM są bardziej wydajne od klasycznych odpowiedników?](#teza-3--czy-operatory-llm-są-bardziej-wydajne-od-klasycznych-odpowiedników)
- [Rozdział 3 — Wstęp teoretyczny](#rozdział-3--wstęp-teoretyczny)
  - [3.1 Testowanie mutacyjne](#31-testowanie-mutacyjne)
    - [3.1.1 Czym jest mutant?](#311-czym-jest-mutant)
    - [3.1.2 Zabicie mutanta i mutation score](#312-zabicie-mutanta-i-mutation-score)
    - [3.1.3 Equivalent mutant i duplicate mutant](#313-equivalent-mutant-i-duplicate-mutant)
    - [3.1.4 Proces testowania mutacyjnego](#314-proces-testowania-mutacyjnego)
  - [3.2 Klasyczne operatory mutacyjne — narzędzie PIT](#32-klasyczne-operatory-mutacyjne--narzędzie-pit)
    - [3.2.1 Czym jest PIT?](#321-czym-jest-pit)
    - [3.2.2 Typy zmian w grupie ALL](#322-typy-zmian-w-grupie-all)
    - [3.2.3 Ograniczenia klasycznych operatorów](#323-ograniczenia-klasycznych-operatorów)
  - [3.3 Duże modele językowe w inżynierii oprogramowania](#33-duże-modele-językowe-w-inżynierii-oprogramowania)
    - [3.3.1 Czym są LLM?](#331-czym-są-llm)
    - [3.3.2 Zastosowania LLM w inżynierii oprogramowania](#332-zastosowania-llm-w-inżynierii-oprogramowania)
    - [3.3.3 LLM jako generator zmian w kodzie — szanse i ograniczenia](#333-llm-jako-generator-zmian-w-kodzie--szanse-i-ograniczenia)
  - [3.4 Repozytoria rzeczywistych błędów](#34-repozytoria-rzeczywistych-błędów)
    - [3.4.1 Czym są repozytoria bugów?](#341-czym-są-repozytoria-bugów)
    - [3.4.2 Defects4J — główny zbiór danych](#342-defects4j--główny-zbiór-danych)
    - [3.4.3 Dlaczego Defects4J jest dobrym punktem odniesienia?](#343-dlaczego-defects4j-jest-dobrym-punktem-odniesienia)
- [Rozdział 4 — Założenia eksperymentu](#rozdział-4--założenia-eksperymentu)
  - [4.1 Materiał badawczy — dataset i kryteria selekcji](#41-materiał-badawczy--dataset-i-kryteria-selekcji)
  - [4.2 Narzędzia i środowisko techniczne](#42-narzędzia-i-środowisko-techniczne)
  - [4.3 Jednostka analizy — MutantRecord](#43-jednostka-analizy--mutantrecord)
  - [4.4 Generacja mutantów LLM](#44-generacja-mutantów-llm)
  - [4.5 Generacja mutantów PIT](#45-generacja-mutantów-pit)
  - [4.6 Kompilacja i uruchomienie testów](#46-kompilacja-i-uruchomienie-testów)
  - [4.7 Klasteryzacja mutantów LLM w operatory](#47-klasteryzacja-mutantów-llm-w-operatory)
  - [4.8 Automatyczne dopasowanie operatora LLM do katalogu PIT](#48-automatyczne-dopasowanie-operatora-llm-do-katalogu-pit)
  - [4.9 Definicje metryk](#49-definicje-metryk)
- [Rozdział 5 — Wyniki](#rozdział-5--wyniki)
  - [5.1 Statystyki ogólne eksperymentu](#51-statystyki-ogólne-eksperymentu)
  - [5.2 Wyniki dla Tezy 1 — nowość operatorów](#52-wyniki-dla-tezy-1--nowość-operatorów)
  - [5.3 Wyniki dla Tezy 2 — bliskość do rzeczywistych błędów](#53-wyniki-dla-tezy-2--bliskość-do-rzeczywistych-błędów)
  - [5.4 Wyniki dla Tezy 3 — wydajność operatorów](#54-wyniki-dla-tezy-3--wydajność-operatorów)
- [Rozdział 6 — Opracowanie wyników](#rozdział-6--opracowanie-wyników)
  - [6.1 Interpretacja wyników dla Tezy 1](#61-interpretacja-wyników-dla-tezy-1)
  - [6.2 Interpretacja wyników dla Tezy 2](#62-interpretacja-wyników-dla-tezy-2)
  - [6.3 Interpretacja wyników dla Tezy 3](#63-interpretacja-wyników-dla-tezy-3)
- [Rozdział 7 — Wnioski z eksperymentu](#rozdział-7--wnioski-z-eksperymentu)
  - [7.1 Wnioski dla Tezy 1](#71-wnioski-dla-tezy-1)
  - [7.2 Wnioski dla Tezy 2](#72-wnioski-dla-tezy-2)
  - [7.3 Wnioski dla Tezy 3](#73-wnioski-dla-tezy-3)
  - [7.4 Zagrożenia dla rzetelności wyników](#74-zagrożenia-dla-rzetelności-wyników)
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

## Rozdział 1 — Wstęp

### 1.1 Temat i cel pracy

#### Czym jest testowanie mutacyjne?

> ✏️ **Wskazówka:** Napisz 2–3 zdania wyjaśniające intuicję, bez wzorów.
> Kluczowa myśl: zamiast sprawdzać, czy kod jest dobry, sprawdzamy, czy testy są wystarczająco silne, by wykryć celowe błędy.

Testowanie mutacyjne to technika oceny jakości zestawów testów automatycznych. Polega ona na tworzeniu zmodyfikowanych wersji programu — zwanych mutantami — poprzez wprowadzenie drobnej, celowej zmiany do kodu źródłowego, a następnie sprawdzeniu, czy istniejące testy potrafią wykryć tę zmianę. Jeżeli test wykryje różnicę w zachowaniu mutanta względem oryginalnego programu, mówimy, że mutant został „zabity"; jeżeli nie — mutant „przeżywa", co wskazuje na słabość zestawu testów w danym obszarze kodu.

#### Jaki jest problem z obecnymi operatorami mutacyjnymi?

> ✏️ **Wskazówka:** Trzy osobne problemy — opisz każdy w 1–2 zdaniach.
> To jest uzasadnienie dla całej pracy. Czytelnik musi zrozumieć, dlaczego temat jest ważny.

Klasyczne operatory mutacyjne, takie jak te zdefiniowane w narzędziu PIT w grupie „ALL", są tworzone ręcznie przez ekspertów i kodowane bezpośrednio w narzędziu. Powoduje to, że zbiór dostępnych reguł jest skończony i statyczny — nie rozrasta się wraz z ewolucją języków programowania ani wzorców błędów.

Dodatkowym problemem jest wysoki odsetek mutantów semantycznie równoważnych (*equivalent mutants*) — takich, które nie zmieniają zachowania programu w żaden sposób wykrywalny przez testy — oraz duplikatów semantycznych (*duplicate mutants*), które wywołują identyczne reakcje zestawu testów co inne mutanty. Oba typy sztucznie zawyżają liczbę mutantów, zwiększając koszt analizy bez wnoszenia nowej informacji.

Fundamentalnym pytaniem pozostaje, czy ręcznie zaprojektowane reguły mutacyjne rzeczywiście odzwierciedlają typy błędów, jakie programiści popełniają w praktyce, czy raczej stanowią formalne, ale oderwane od rzeczywistości abstrakty syntaktyczne.

#### Dlaczego LLM mogą tu pomóc?

> ✏️ **Wskazówka:** Podaj 2 konkretne powody — uczenie na realnym kodzie i zdolność do generowania różnorodnych zmian.

Duże modele językowe (LLM) trenowane są na ogromnych zbiorach kodu źródłowego i raportów błędów. Dzięki temu mają dostęp do wiedzy o tym, jakie typy zmian faktycznie powodują defekty w oprogramowaniu. W odróżnieniu od ręcznie zaprojektowanych operatorów, LLM mogą generować mutacje inspirowane realnymi wzorcami błędów zaobserwowanymi w milionach repozytoriów.

Ponadto LLM potrafią generować semantycznie zróżnicowane zmiany — nie tylko proste podstawienia operatorów arytmetycznych, ale również usunięcia guard'ów, zmianę kolejności inicjalizacji, modyfikacje warunków złożonych czy usunięcia null-checków. To zróżnicowanie może prowadzić do odkrycia nowych, nieznanych wcześniej klas operatorów mutacyjnych.

#### Cel pracy

> ✏️ **Wskazówka:** Napisz cel jako 3 tezy w jednym akapicie. To jest serce całej pracy.

Celem niniejszej pracy jest empiryczna weryfikacja trzech hipotez dotyczących jakości operatorów mutacyjnych generowanych przez LLM. Po pierwsze, czy LLM potrafią indukować reguły mutacyjne wykraczające poza katalog PIT „ALL" — czyli generować operatory, których PIT nie zawiera. Po drugie, czy mutanty wygenerowane przez LLM są behawioralnie bliższe rzeczywistym błędom oprogramowania niż mutanty generowane przez klasyczne narzędzia. Po trzecie, czy operatory LLM są bardziej wydajne od swoich klasycznych odpowiedników mierzonych metrykami testowania mutacyjnego.

---

### 1.2 Budowa pracy

Praca podzielona jest na siedem rozdziałów poprzedzonych streszczeniem. Wygląd zawartości rozdziałów przedstawionych w pracy:

- **Rozdział 2** zawiera opis planowanego pipeline'u badania — sekwencję ośmiu kroków eksperymentu — oraz formalne sformułowanie trzech tez badawczych wraz z przypisanymi metrykami weryfikacji.
- **Rozdział 3** zawiera wstęp teoretyczny: omówienie testowania mutacyjnego i jego procesu, opis klasycznych operatorów mutacyjnych i narzędzia PIT, wprowadzenie do dużych modeli językowych w kontekście inżynierii oprogramowania oraz opis repozytorium Defects4J jako źródła danych badawczych.
- **Rozdział 4** zawiera założenia eksperymentu: opis datasetu i kryteriów selekcji bugów, narzędzi i środowiska technicznego, protokołu generacji mutantów LLM i PIT, procedury kompilacji i uruchomienia testów, metodyki klasteryzacji operatorów LLM oraz definicje wszystkich metryk używanych w badaniu.
- **Rozdział 5** zawiera surowe wyniki eksperymentu w postaci tabel statystycznych — ogólne statystyki oraz wyniki dla każdej z trzech tez badawczych.
- **Rozdział 6** zawiera opracowanie wyników — interpretację liczb w kontekście każdej tezy, omówienie relacji między metrykami oraz wnioski cząstkowe.
- **Rozdział 7** zawiera wnioski końcowe z eksperymentu: odpowiedź na każdą z trzech tez oraz omówienie zagrożeń dla rzetelności wyników.
- **Podsumowanie** jest syntetycznym zestawieniem najważniejszych rezultatów pracy, omówieniem ograniczeń badania i propozycją kierunków dalszych badań.

---

## Rozdział 2 — Opis planowanych badań i tezy badawcze

### 2.1 Pipeline badania

> ✏️ **Wskazówka:** Opisz JEDNO badanie jako logiczną sekwencję kroków.
> Nie tłumacz jak technicznie — opisz CO robisz na każdym etapie.
> Każdy krok to jedno zdanie lub krótki akapit.

Badanie realizowane jest jako jeden spójny eksperyment, którego wyniki analizowane są następnie w trzech niezależnych pakietach odpowiadających tezom T1–T3. Pipeline obejmuje osiem etapów:

**Krok 1 — Wybór projektów i błędów**  
Ze zbioru Defects4J wybierane są błędy spełniające kryteria selekcji: poprawna kompilacja, istnienie testów wyzwalających oraz akceptowalny czas uruchomienia testów.

**Krok 2 — Generacja mutantów LLM**  
Dla każdego wybranego błędu model LLM otrzymuje kontekst kodu źródłowego wokół miejsca zmiany i jest proszony o wygenerowanie kilku realistycznych wariantów błędu wraz z opisem reguły mutacyjnej (operatora LLM).

**Krok 3 — Generacja mutantów PIT**  
Dla tych samych projektów i klas uruchamiane jest narzędzie PIT z pełnym zestawem operatorów (ALL), generując zbiór mutantów klasycznych jako bazę porównawczą.

**Krok 4 — Kompilacja każdego mutanta**  
Każdy mutant (LLM i PIT) jest kompilowany w izolowanym środowisku Defects4J. Rejestrowany jest wynik kompilacji (sukces/błąd) oraz typ błędu kompilacji. Mutanty nieskompilowane są odrzucane z dokumentacją przyczyny.

**Krok 5 — Uruchomienie testów**  
Dla mutantów, które skompilowały się poprawnie, uruchamiany jest zestaw testów jednostkowych. Zbierany jest zbiór testów, które nie przechodzą (*failing tests*), oraz informacja, czy mutant został „zabity".

**Krok 6 — Klasteryzacja mutantów LLM w operatory**  
Opisy reguł mutacyjnych wygenerowane przez LLM są wektoryzowane i poddane klasteryzacji. Każdy klaster definiuje jeden operator LLM — abstrakcyjną regułę reprezentowaną przez opis i przykładowe patche.

**Krok 7 — Dopasowanie operatorów LLM do katalogu PIT**  
Każdy operator LLM jest automatycznie klasyfikowany jako NEW (brak odpowiednika w PIT), PARTIAL (częściowe pokrycie) lub EXISTING (odpowiednik w PIT istnieje), w oparciu o podobieństwo profili testowych i heurystyki typów zmian.

**Krok 8 — Obliczenie metryk i analiza**  
Na podstawie zgromadzonych danych obliczane są metryki odpowiadające trzem tezom badawczym i przeprowadzana jest analiza porównawcza LLM vs PIT.

---

### 2.2 Tezy badawcze

> ✏️ **Wskazówka:** Każda teza = hipoteza + metryki weryfikacji.
> Piszesz tu NA POZIOMIE KONCEPCYJNYM — szczegóły techniczne idą do Rozdziału 4.

#### Teza 1 — Czy LLM generuje nowe operatory mutacyjne?

**Hipoteza:**  
Duże modele językowe potrafią generować operatory mutacyjne inne niż klasyczne operatory PIT „ALL" — tj. indukować reguły mutacyjne, dla których nie istnieje odpowiednik w aktualnym katalogu narzędzia PIT.

**Metryki weryfikacji:**
- **% nowych operatorów** — odsetek operatorów LLM bez odpowiednika w PIT „ALL".
- **Kompilowalność** — procent kompilujących się mutantów wygenerowanych przez daną regułę.
- **Liczba zastosowań** — jak często reguła ma sensowne zastosowanie w kodzie różnych projektów (z uwzględnieniem duplicate i equivalent mutants).

**Metoda weryfikacji:**  
Operatory LLM (klastry mutantów) są automatycznie porównywane z listą mutatorów PIT poprzez analizę podobieństwa profili testowych i typów zmian w kodzie. Odsetek operatorów sklasyfikowanych jako NEW stanowi główny wskaźnik dla tej tezy.

**Oczekiwany wynik:**  
Jeśli teza jest prawdziwa, co najmniej część operatorów LLM będzie miała etykietę NEW — co oznaczałoby rozszerzenie przestrzeni mutacji poza katalog PIT.

---

#### Teza 2 — Czy operatory LLM są bliższe prawdziwym usterkom?

**Hipoteza:**  
Mutanty generowane przez LLM są behawioralnie bliższe rzeczywistym błędom oprogramowania niż mutanty generowane przez PIT — tzn. wywołują podobne reakcje zestawu testów co rzeczywiste defekty.

**Metryki weryfikacji:**
- **Bliskość do prawdziwego błędu (proximity)** — podobieństwo profilu PASS/FAIL mutanta i rzeczywistego błędu (Jaccard na zbiorach failing tests).
- **Mutation score** — odsetek mutantów wykrywanych przez testy dla operatorów LLM vs odpowiedniki PIT.

**Metoda weryfikacji:**  
Dla każdego mutanta obliczane jest podobieństwo Jaccarda między zbiorem testów, które nie przechodzą dla mutanta (`FailMut`), a zbiorem testów, które nie przechodzą dla rzeczywistego błędu (`FailBug`). Rozkłady tej metryki (*proximity*) dla mutantów LLM i PIT są porównywane statystycznie.

**Oczekiwany wynik:**  
Jeśli teza jest prawdziwa, mediana proximity dla mutantów LLM powinna być istotnie wyższa niż dla mutantów PIT na tych samych projektach.

---

#### Teza 3 — Czy operatory LLM są bardziej wydajne od klasycznych odpowiedników?

**Hipoteza:**  
Operatory LLM są bardziej wydajne od swoich klasycznych odpowiedników z PIT, co objawia się niższym odsetkiem duplikatów, porównywalną lub wyższą kompilowalności oraz wyższą proximity.

**Metryki weryfikacji:**
- **Mutation score** operatorów LLM vs ich „bliskich klasycznych odpowiedników" z PIT.
- **Kompilowalność** — porównanie odsetka kompilujących się mutantów: LLM vs PIT.
- **Duplicate rate** — odsetek duplikatów semantycznych wśród mutantów: LLM vs PIT.
- **Liczba zastosowań** — średnia liczba miejsc w kodzie, gdzie dana reguła ma zastosowanie: LLM vs PIT.

**Metoda weryfikacji:**  
Dla operatorów LLM sklasyfikowanych jako EXISTING lub PARTIAL (mających odpowiednik w PIT) przeprowadzane jest bezpośrednie porównanie metryk pomiędzy operatorem LLM a jego klasycznym odpowiednikiem.

**Oczekiwany wynik:**  
Jeśli teza jest prawdziwa, operatory LLM w parach LLM–PIT powinny osiągać niższy duplicate rate i wyższą proximity przy zachowaniu akceptowalnego compile rate.

---

## Rozdział 3 — Wstęp teoretyczny

> ✏️ **Wskazówka do całego rozdziału:** Tu tłumaczysz pojęcia, których używasz w Rozdziale 4.
> Pisz intuicyjnie — bez wzorów, bez implementacji.
> Cel: czytelnik niezaznajomiony z tematem powinien rozumieć Rozdział 4 po przeczytaniu tego rozdziału.

---

### 3.1 Testowanie mutacyjne

#### 3.1.1 Czym jest mutant?

> ✏️ **Wskazówka:** Wyjaśnij intuicję na przykładzie. Jedno zdanie definicji + jedno zdanie przykładu.

Mutant to wersja programu, która różni się od oryginału jedną małą, celową zmianą — na przykład zmianą znaku `>` na `>=` w warunku, usunięciem wywołania metody, albo zamianą operatora dodawania na odejmowanie. Zmiana ta jest wprowadzana automatycznie przez narzędzie zgodnie z predefiniowaną regułą — *operatorem mutacyjnym*. Sam mutant nie jest błędem, który faktycznie wystąpił w kodzie — jest sztuczną symulacją błędu, służącą do sprawdzenia, czy testy byłyby zdolne do jego wykrycia.

*[Do uzupełnienia: przykład konkretnego mutanta — fragment kodu oryginalnego i zmutowanego.]*

#### 3.1.2 Zabicie mutanta i mutation score

> ✏️ **Wskazówka:** Wyjaśnij związek między mutantem a testem. Mutation score jako wynik końcowy.

Mutant zostaje „zabity", gdy co najmniej jeden test z zestawu wykryje różnicę w zachowaniu między programem oryginalnym a mutantem — na przykład, gdy zmiana operatora powoduje, że wynik obliczeń jest inny, co wykrywa asercja w teście. Jeżeli żaden test nie wykryje zmiany, mutant „przeżywa", co informuje o tym, że ten fragment kodu nie jest odpowiednio pokryty przez testy.

Mutation score to stosunek liczby zabitych mutantów do wszystkich mutantów, które się skompilowały. Im wyższy wynik, tym silniejszy zestaw testów. Mutation score wynoszący 80% oznacza, że 80% wprowadzonych celowych błędów zostało wykrytych przez istniejące testy.

#### 3.1.3 Equivalent mutant i duplicate mutant

> ✏️ **Wskazówka:** To są dwa główne problemy testowania mutacyjnego — warto je wyraźnie odróżnić.

**Equivalent mutant** to mutant, który wprawdzie różni się od oryginału syntaktycznie, ale zachowuje się identycznie — żaden test nie jest w stanie go zabić, bo semantycznie robi to samo co oryginalny program. Przykładem jest zamiana `i = i + 1` na `i += 1` — obie formy mają ten sam efekt. Equivalent mutanty są szczególnie kosztowne, bo zwiększają liczbę mutantów wymagających analizy, nie wnosząc żadnej informacji o jakości testów.

**Duplicate mutant** to mutant, który wywołuje dokładnie taki sam profil testowy co inny mutant — te same testy kończą się niepowodzeniem, te same przechodzą. Duplikaty sztucznie zawyżają rozmiar zbioru mutantów i fałszują statystyki, sugerując większą różnorodność niż ta, która faktycznie istnieje.

#### 3.1.4 Proces testowania mutacyjnego

> ✏️ **Wskazówka:** Opisz sekwencję kroków — od kodu do raportu. Można użyć listy numerowanej.

Standardowy proces testowania mutacyjnego przebiega następująco:

1. Narzędzie mutacyjne analizuje kod źródłowy i generuje zbiór mutantów na podstawie dostępnych operatorów.
2. Każdy mutant jest kompilowany; te, które nie skompilują się poprawnie, są odrzucane.
3. Dla każdego skompilowanego mutanta uruchamiany jest zestaw testów jednostkowych.
4. Rejestrowane jest, które testy nie przechodzą — na tej podstawie mutant jest klasyfikowany jako zabity lub żywy.
5. Obliczany jest mutation score oraz generowany raport wskazujący na przeżałe mutanty.

*[Do uzupełnienia: opcjonalnie diagram procesu lub przykładowy raport PIT.]*

---

### 3.2 Klasyczne operatory mutacyjne — narzędzie PIT

#### 3.2.1 Czym jest PIT?

> ✏️ **Wskazówka:** Krótki opis — co to jest, dla jakiego języka, dlaczego jest standardem.

PIT (*Pitest*) to narzędzie do testowania mutacyjnego dla języka Java, które stało się de facto standardem w tej dziedzinie. W odróżnieniu od wcześniejszych narzędzi działających na poziomie kodu źródłowego, PIT operuje na skompilowanym bytecode JVM, co zapewnia mu wydajność i niezależność od środowiska kompilacji. PIT integruje się z systemami budowania Maven i Gradle, generuje raporty HTML i obsługuje testy JUnit oraz TestNG.

#### 3.2.2 Typy zmian w grupie ALL

> ✏️ **Wskazówka:** Opisz kategorie zmian bez wchodzenia w implementację. Tabela jest wystarczająca — dodaj krótki komentarz przed nią.

Grupa operatorów „ALL" w PIT obejmuje kilkanaście kategorii zmian w kodzie. Można je podzielić na cztery główne klasy:

**Zmiany warunków logicznych** — negacja warunków (`==` na `!=`), zamiana operatorów granicznych (`<` na `<=`), usunięcie całych warunków zastąpionych przez `true` lub `false`.

**Zmiany operatorów arytmetycznych i bitowych** — zamiana operatorów `+`, `-`, `*`, `/`, `%`, `&`, `|`, `^`, `<<`, `>>`.

**Zmiany wartości zwracanych** — zastąpienie wartości zwracanej przez metodę wartościami domyślnymi: `null`, `0`, `false`, `true`, pusty string, pusta kolekcja.

**Usunięcia wywołań** — usunięcie wywołań metod void, które nie mają bezpośredniego efektu na wartość zwracaną.

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

#### 3.2.3 Ograniczenia klasycznych operatorów

> ✏️ **Wskazówka:** To jest uzasadnienie dla badania. Napisz 2–3 zdania.

Katalog operatorów PIT jest kompletny w odniesieniu do prostych zmian syntaktycznych, ale z natury ograniczony do reguł przewidzianych przez twórców narzędzia. Nie uwzględnia on bardziej subtelnych typów błędów, takich jak brakujące null-checki, niepoprawna kolejność operacji, błędy w inicjalizacji obiektów czy niepoprawne obsługi wyjątków — typów zmian, które mogą być częstsze w prawdziwych defektach oprogramowania. Ta luka uzasadnia poszukiwanie dodatkowych źródeł reguł mutacyjnych, takich jak modele językowe.

---

### 3.3 Duże modele językowe w inżynierii oprogramowania

#### 3.3.1 Czym są LLM?

> ✏️ **Wskazówka:** Dwa zdania wyjaśniające intuicję — bez matematyki transformerów.

Duże modele językowe (ang. *Large Language Models*, LLM) to systemy uczenia maszynowego trenowane na bardzo dużych zbiorach tekstu — w tym kodu źródłowego — w celu modelowania zależności statystycznych między tokenami. W praktyce oznacza to, że model „nauczył się" wzorców języka programowania, typowych struktur kodu, konwencji i często popełnianych błędów na podstawie miliardów linii kodu z publicznych repozytoriów.

*[Do uzupełnienia: krótki przegląd najważniejszych modeli — GPT-4, Claude, Gemini, modele open-source jak CodeLlama. Literatura: Chen et al. 2021 (Codex).]*

#### 3.3.2 Zastosowania LLM w inżynierii oprogramowania

> ✏️ **Wskazówka:** Lista 4–5 zastosowań z jednozdaniowym komentarzem każde.

LLM znalazły szerokie zastosowanie w różnych aspektach inżynierii oprogramowania:

- **Generowanie kodu** — narzędzia takie jak GitHub Copilot potrafią automatycznie uzupełniać fragmenty kodu na podstawie kontekstu i komentarzy.
- **Automatyczne naprawianie błędów (APR)** — LLM są stosowane do sugerowania poprawek dla znanych defektów, często z wyższą skutecznością niż tradycyjne metody symboliczne.
- **Code review** — modele są w stanie identyfikować potencjalne problemy w kodzie poddanym przeglądowi.
- **Generowanie testów jednostkowych** — LLM potrafią automatycznie generować zestawy testów dla nowych fragmentów kodu.
- **Analiza podatności bezpieczeństwa** — modele wykrywają wzorce kodu potencjalnie narażone na ataki.

*[Do uzupełnienia: 1–2 literaturowe odniesienia do zastosowań w SE.]*

#### 3.3.3 LLM jako generator zmian w kodzie — szanse i ograniczenia

> ✏️ **Wskazówka:** Wyważ: LLM dają nowe możliwości, ale mają ograniczenia (niedeterminizm, halucynacje). Oboje są ważne dla Twojej pracy.

Z perspektywy niniejszej pracy LLM traktowany jest jako *generator hipotez mutacyjnych*: model otrzymuje kontekst kodu i instrukcję wygenerowania realistycznej zmiany symulującej błąd, a w odpowiedzi zwraca zmodyfikowany fragment kodu wraz z opisem reguły, którą zastosował. Kluczową zaletą tego podejścia jest to, że reguła jest *indukcyjna* — wynika z wzorców zaobserwowanych w danych, a nie z ręcznej specyfikacji eksperta.

Jednak LLM mają istotne ograniczenia w tym kontekście. Są niedeterministyczne — dla tego samego wejścia mogą generować różne odpowiedzi, co utrudnia reprodukowalność eksperymentów. Mogą generować kod, który nie kompiluje się lub jest semantycznie niepoprawny (*halucynacje*). Wreszcie, nie mają gwarancji, że wygenerowana zmiana faktycznie symuluje realny błąd — może to być zmiana arbitralna, nieistotna z perspektywy testowania. Te ograniczenia są adresowane w protokole eksperymentu przez filtrację kompilowalności i weryfikację przez testy.

---

### 3.4 Repozytoria rzeczywistych błędów

#### 3.4.1 Czym są repozytoria bugów?

> ✏️ **Wskazówka:** Definicja + po co w ogóle istnieją takie repozytoria w badaniach.

Repozytoria rzeczywistych błędów to kuratowane zbiory defektów oprogramowania wyekstrahowanych z historii repozytoriów kodu. Każdy wpis zawiera zazwyczaj wersję kodu sprzed i po naprawie, opis błędu oraz zestaw testów wykrywających dany defekt. Są one używane w badaniach naukowych jako standaryzowane zestawy danych umożliwiające porównywanie różnych technik naprawy, wykrywania i analizy błędów w kontrolowanych warunkach.

#### 3.4.2 Defects4J — główny zbiór danych

> ✏️ **Wskazówka:** Opisz dataset konkretnie — ile bugów, jakie projekty, jakie metadane są dostępne.

Defects4J (Just et al., 2014) to jedno z najszerzej stosowanych repozytoriów błędów dla języka Java w badaniach nad testowaniem oprogramowania. Zawiera ponad 800 aktywnych, ręcznie zweryfikowanych defektów pochodzących z rzeczywistych projektów open-source, m.in.:

| Projekt | Opis | Liczba błędów (przykładowo) |
|---|---|---|
| Apache Commons Lang | Narzędzia dla klas Java | ~65 |
| Apache Commons Math | Biblioteka matematyczna | ~106 |
| Joda-Time | Obsługa dat i czasu | ~27 |
| JFreeChart | Biblioteka wykresów | ~26 |
| Closure Compiler | Kompilator JavaScript | ~176 |

Dla każdego błędu dostępne są:
- wersja kodu `buggy` (przed naprawą) i `fixed` (po naprawie),
- lista plików źródłowych zmodyfikowanych przy naprawie,
- zbiór testów wyzwalających (*triggering tests*) — testy, które nie przechodzą dla wersji buggy, ale przechodzą dla fixed,
- interfejs CLI (`defects4j checkout`, `compile`, `test`) umożliwiający reprodukcję każdego błędu.

#### 3.4.3 Dlaczego Defects4J jest dobrym punktem odniesienia?

> ✏️ **Wskazówka:** Uzasadnij wybór tego datasetu. Co konkretnie z niego używasz w eksperymencie (FailBug).

Defects4J jest odpowiednim zbiorem danych dla niniejszego badania z kilku powodów. Po pierwsze, każdy błąd ma zdefiniowany zbiór testów wyzwalających (`FailBug`), który stanowi punkt odniesienia dla metryki proximity — pozwala to na obliczenie metryki *proximity* dla wygenerowanych mutantów przez bezpośrednie porównanie zbiorów testów. Po drugie, dostępne są narzędzia CLI zapewniające reprodukowalność — każdy błąd można „odtworzyć" w kontrolowanym środowisku przez `defects4j checkout` i uruchomić na nim testy. Po trzecie, Defects4J jest szeroko stosowany w literaturze, co ułatwia porównanie wyników z innymi pracami.

---

## Rozdział 4 — Założenia eksperymentu

### 4.1 Materiał badawczy — dataset i kryteria selekcji

> ✏️ **Wskazówka:** Podaj konkretnie: jaki dataset, ile bugów, jaki język, jakie kryteria wyboru.
> Bez wyników — tylko co i dlaczego wybrałeś.

Eksperymenty przeprowadzono na zbiorze błędów z repozytorium Defects4J dla języka Java. Do badania wybrano **N = [uzupełnić]** błędów z następujących projektów: *[lista projektów]*.

Kryteria selekcji błędu do zbioru badawczego:

1. **Kompilowalność bazowa** — projekt buduje się poprawnie (`defects4j compile` bez błędów) dla wersji `buggy` bez modyfikacji konfiguracji.
2. **Istnienie testów wyzwalających** — wersja `buggy` musi posiadać co najmniej jeden test wyzwalający (`|FailBug| ≥ 1`), który stanowi punkt odniesienia dla metryki proximity.
3. **Akceptowalny czas testów** — łączny czas uruchomienia testów dla wersji `buggy` nie przekracza 10 minut, co jest kryterium wykonalności przy testowaniu dziesiątek mutantów per bug.
4. **Ograniczony zakres zmiany** — błąd dotyczy co najwyżej [np. 3] plików źródłowych, co ogranicza zakres kontekstu przekazywanego do LLM.

### 4.2 Narzędzia i środowisko techniczne

> ✏️ **Wskazówka:** Tabela narzędzi + krótki opis środowiska uruchomieniowego.

| Narzędzie | Wersja | Rola w eksperymencie |
|---|---|---|
| Defects4J CLI | [wersja] | Checkout, compile, test dla każdego mutanta |
| PIT (Pitest) | [wersja] | Generacja mutantów klasycznych (ALL) |
| *[model LLM, np. GPT-4o]* | [wersja API] | Generacja mutantów LLM + opisy reguł |
| *[model embeddingowy]* | [wersja] | Wektoryzacja opisów reguł do klasteryzacji |
| *[algorytm klasteryzacji]* | — | Grupowanie mutantów LLM w operatory |
| Python 3.x | [wersja] | Automatyzacja pipeline'u (`podman_defects4j.py`) |
| Podman | [wersja] | Kontener z środowiskiem Defects4J |

Wszystkie operacje na kodzie projektu (checkout, kompilacja, testy) wykonywane są wewnątrz kontenera Podman o nazwie `defects4j-container`, przez `podman exec`. Zapewnia to izolację środowiska i reprodukowalność wyników niezależnie od konfiguracji maszyny hosta.

### 4.3 Jednostka analizy — MutantRecord

> ✏️ **Wskazówka:** Wyjaśnij, że wszystkie dane z eksperymentu sprowadzają się do jednego schematu.
> To jest fundamentalne dla zrozumienia jak liczysz metryki.

Każdy mutant wygenerowany w eksperymencie — zarówno przez LLM, jak i przez PIT — zapisywany jest jako ujednolicony rekord danych (`MutantRecord`) w formacie JSON. Schemat ten jest wspólny dla obu źródeł, co umożliwia obliczenie wszystkich metryk z jednego strumienia danych bez konieczności utrzymywania osobnych pipeline'ów analitycznych.

```json
{
  "id": "Lang-1-llm-042",
  "source": "LLM",
  "project": "Lang",
  "bug_id": 1,
  "file": "src/main/java/.../StringUtils.java",
  "location": {
    "class": "StringUtils",
    "method": "isEmpty",
    "line": 234
  },
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

Pola specyficzne dla mutantów LLM: `rule_description`, `operator_cluster_id`, `pit_match_label`.  
Pola specyficzne dla mutantów PIT: `pit_mutator_type`.  
Pole `proximity` obliczane jest jako Jaccard(`failing_tests_set`, `FailBug`) po uruchomieniu testów.

### 4.4 Generacja mutantów LLM

> ✏️ **Wskazówka:** Opisz protokół — co dajesz modelowi, co od niego dostajesz, jak to zapisujesz.
> Szczegóły techniczne promptu możesz dopisać po ustaleniu finalnej wersji.

Dla każdego wybranego błędu (wersja `buggy`) generacja mutantów LLM przebiega według następującego protokołu:

**Przygotowanie kontekstu:**  
Wyeksportowanie zmodyfikowanych plików źródłowych za pomocą `defects4j export -p modified.classes`. Ekstrakcja fragmentu kodu wokół miejsca zmiany (kontekst ±20 linii). Opcjonalnie: dołączenie `fix diff` jako przykładu stylu zmiany.

**Konstrukcja promptu:**  
*[Opis struktury promptu — do uzupełnienia po ustaleniu finalnej wersji. Powinna zawierać: instrukcję generowania K realistycznych wariantów błędu, żądanie opisu reguły mutacyjnej dla każdej zmiany, żądanie formatu diff.]*

**Parametry generacji:**  
- Liczba mutantów per bug: K = *[np. 10–20]*  
- Temperatura: *[np. 0.8]*  
- Seed: stały dla reprodukowalności  
- Model: *[nazwa modelu i wersja]*

**Zbieranie i parsowanie odpowiedzi:**  
Każda odpowiedź modelu jest parsowana w celu ekstrakcji: patcha (unified diff) i opisu reguły mutacyjnej. Odpowiedzi, których nie da się sparsować, są odrzucane z dokumentacją przyczyny.

**Zapis:**  
Każdy pomyślnie sparsowany mutant jest zapisywany jako `MutantRecord` z `source="LLM"` i `rule_description` uzupełnionym z odpowiedzi modelu.

### 4.5 Generacja mutantów PIT

> ✏️ **Wskazówka:** Opisz konfigurację PIT i jak mapujesz wyniki do MutantRecord.

Dla każdego wybranego projektu uruchamiane jest narzędzie PIT z konfiguracją:
- `mutators = ALL` — pełny zestaw operatorów
- `targetClasses` — klasy zmodyfikowane w danym błędzie (z `modified.classes`)
- `targetTests` — wszystkie testy w projekcie

PIT generuje raport XML zawierający listę mutantów wraz z informacją o typie operatora, lokalizacji i wyniku testów. Każdy mutant PIT jest mapowany do `MutantRecord` z `source="PIT"` i `pit_mutator_type` uzupełnionym z raportu.

### 4.6 Kompilacja i uruchomienie testów

> ✏️ **Wskazówka:** Opisz procedurę dla KAŻDEGO mutanta (LLM i PIT).
> Podaj timeouty — to jest ważne dla reprodukowalności.

Dla każdego mutanta (niezależnie od źródła) stosowany jest następujący protokół weryfikacji:

```
1. Skopiuj plik z patchem do kontenera (podman cp)
2. Utwórz kopię zapasową oryginalnego pliku (.orig)
3. Zastosuj patch (patch -p1)
4. defects4j compile  [timeout: 900 s]
   → zapisz: compile ∈ {0, 1}, compile_error_type
5. Jeśli compile = 1:
     defects4j test -r  [timeout: 1800 s]
     → zapisz: failing_tests_set, killed, tests_run_count
6. Przywróć oryginalny plik z kopii zapasowej
7. Oblicz proximity = Jaccard(failing_tests_set, FailBug)
8. Zapisz kompletny MutantRecord
```

Operacje backup (`cp do .orig`) i restore (`mv .orig`) są realizowane przez `backup_file_in_container` i `restore_file_in_container` z `podman_defects4j.py`. W przypadku błędu na dowolnym kroku, restore jest wywoływane w bloku `finally`, gwarantując integralność środowiska przed kolejnym mutantem.

### 4.7 Klasteryzacja mutantów LLM w operatory

> ✏️ **Wskazówka:** Opisz CO robisz (nie jak technicznie). Wynik = operator = klaster z nazwą.

Po zebraniu wszystkich `MutantRecord` z `source="LLM"` przeprowadzana jest klasteryzacja w celu grupowania podobnych reguł mutacyjnych w spójne operatory LLM:

1. **Wektoryzacja opisów** — pole `rule_description` każdego mutanta LLM jest wektoryzowane modelem embeddingowym *[nazwa]*, tworząc reprezentację numeryczną semantyki opisu.
2. **Klasteryzacja** — wektory grupowane są algorytmem *[HDBSCAN / k-means]* z parametrami *[do uzupełnienia]*. Każdy klaster odpowiada jednemu operatorowi LLM.
3. **Definicja operatora** — każdy klaster opisywany jest przez: nazwę (przypisywaną ręcznie), opis reguły (centroid opisów) oraz 2–3 przykładowe patche.
4. **Ręczna weryfikacja** — dwóch niezależnych oceniających przegląda klastry i weryfikuje spójność semantyczną każdego operatora.
5. **Zapis** — pole `operator_cluster_id` w każdym `MutantRecord` jest aktualizowane identyfikatorem klastra.

### 4.8 Automatyczne dopasowanie operatora LLM do katalogu PIT

> ✏️ **Wskazówka:** Opisz algorytm A1 (Jaccard) i A2 (heurystyki AST) + jak z nich korzystasz razem.

Każdy operator LLM (klaster) jest automatycznie klasyfikowany jako `NEW`, `PARTIAL` lub `EXISTING` w odniesieniu do katalogu PIT. Klasyfikacja odbywa się w dwóch krokach:

**Krok A1 — podobieństwo profilu testowego (metoda podstawowa)**

Dla każdego mutanta LLM z niepustym `failing_tests_set` obliczane jest podobieństwo Jaccarda z każdym mutantem PIT w tym samym projekcie:

```
J(FailLLM, FailPIT_j) = |FailLLM ∩ FailPIT_j| / |FailLLM ∪ FailPIT_j|
```

Etykieta mutanta LLM na podstawie maksymalnego J:
- `EXISTING` — `max(J) ≥ 0.9` (bardzo podobne zachowanie testowe)
- `PARTIAL` — `max(J) ∈ [0.4, 0.9)` (częściowe pokrycie)
- przejdź do A2 — `max(J) < 0.4` (brak podobnego mutanta PIT)

**Krok A2 — typ zmiany (metoda zastępcza)**

Jeśli A1 nie rozstrzyga (brak podobnego mutanta PIT lub pusty `failing_tests_set`), typ zmiany klasyfikowany jest heurystycznie na podstawie analizy patcha:

| Wzorzec zmiany | Etykieta |
|---|---|
| Zamiana operatora arytmetycznego (`+`, `-`, `*`, `/`) | `EXISTING` |
| Negacja lub zamiana operatora relacyjnego (`<`, `>`, `==`) | `EXISTING` |
| Zamiana wartości zwracanej (`return x` → `return null/0`) | `EXISTING` |
| Usunięcie wywołania metody void | `EXISTING` |
| Usunięcie sprawdzenia null / guard clause | `NEW` |
| Zmiana kolejności wywołań lub inicjalizacji | `NEW` |
| Modyfikacja warunków złożonych (`A && B` → `A`) | `NEW` |
| Zmiana obsługi wyjątków | `NEW` |
| Inne typy zmian nieobecne w katalogu PIT | `NEW` |

**Etykieta operatora (klastra)**

Operator LLM otrzymuje etykietę na podstawie rozkładu etykiet jego mutantów:
- `NEW` — ≥ 50% mutantów klastra ma etykietę `NEW`
- `EXISTING` — ≥ 50% mutantów klastra ma etykietę `EXISTING`
- `PARTIAL` — pozostałe przypadki

### 4.9 Definicje metryk

> ✏️ **Wskazówka:** Formalna lista wszystkich metryk używanych w sekcjach 4.2 i 4.3.
> Każda metryka = wzór + jedna zdanie interpretacji.

| Metryka | Wzór | Interpretacja |
|---|---|---|
| **% nowych operatorów** | `#NEW / #total_operators` | Odsetek operatorów LLM bez odpowiednika w PIT |
| **Compile rate (kompilowalność)** | `#compile=1 / #all` | Odsetek mutantów, które kompilują się poprawnie |
| **Mutation score** | `#killed / #compiled` | Odsetek skompilowanych mutantów wykrytych przez testy |
| **Proximity** | `\|FailMut ∩ FailBug\| / \|FailMut ∪ FailBug\|` | Behawioralne podobieństwo mutanta do rzeczywistego błędu (0–1) |
| **Duplicate rate** | `#duplicates / #all` | Odsetek mutantów z identycznym `failing_tests_set` co inny mutant |
| **Equivalent rate** | `#(compile=1, killed=0) / #compiled` | Przybliżenie odsetka mutantów semantycznie równoważnych |
| **Liczba zastosowań** | `#mutants_per_operator` | Średnia liczba miejsc w kodzie, gdzie dana reguła ma zastosowanie |

---

---

## Rozdział 5 — Wyniki

> ✏️ **Wskazówka:** Tylko fakty i liczby — bez interpretacji. Każdą tabelę uzupełnij po eksperymencie.

### 5.1 Statystyki ogólne eksperymentu

*[Do uzupełnienia po eksperymencie]*

| Statystyka | Wartość |
|---|---|
| Liczba projektów | |
| Liczba analizowanych błędów (N) | |
| Liczba mutantów LLM wygenerowanych łącznie | |
| Liczba mutantów PIT wygenerowanych łącznie | |
| Mutanty LLM — skompilowane poprawnie | |
| Mutanty PIT — skompilowane poprawnie | |
| Mutanty LLM — przekazane do testów | |
| Mutanty PIT — przekazane do testów | |
| Mutanty LLM — zabite | |
| Mutanty PIT — zabite | |
| Łączny czas eksperymentu | |

### 5.2 Wyniki dla Tezy 1 — nowość operatorów

*[Do uzupełnienia po eksperymencie — liczba klastrów, rozkład etykiet, przykłady operatorów NEW]*

| Etykieta | Liczba operatorów | % operatorów |
|---|---|---|
| NEW | | |
| PARTIAL | | |
| EXISTING | | |
| **Razem** | | |

*[Do uzupełnienia: tabela z przykładami 2–3 operatorów NEW — nazwa, opis reguły, przykładowy patch, liczba mutantów w klastrze]*

### 5.3 Wyniki dla Tezy 2 — bliskość do rzeczywistych błędów

*[Do uzupełnienia po eksperymencie — statystyki opisowe, opcjonalnie wykres boxplot]*

| Statystyka | LLM | PIT |
|---|---|---|
| Mediana Proximity | | |
| Średnia Proximity | | |
| Odchylenie standardowe | | |
| Q1 (25. percentyl) | | |
| Q3 (75. percentyl) | | |
| Odsetek mutantów z Proximity > 0.5 | | |
| Wynik testu statystycznego (Mann-Whitney U) | | |
| Mutation score | | |

### 5.4 Wyniki dla Tezy 3 — wydajność operatorów

*[Do uzupełnienia po eksperymencie — porównanie metryk dla operatorów LLM EXISTING/PARTIAL vs matched PIT]*

| Metryka | LLM (all) | PIT (all) | LLM (EXISTING/PARTIAL) | Matched PIT |
|---|---|---|---|---|
| Mutation score | | | | |
| Compile rate | | | | |
| Duplicate rate | | | | |
| Equivalent rate | | | | |
| Mediana Proximity | | | | |
| Średnia liczba zastosowań | | | | |

---

---

## Rozdział 6 — Opracowanie wyników

> ✏️ **Wskazówka:** Tu łączysz liczby z sensem. Co znaczą wyniki w kontekście każdej tezy?

### 6.1 Interpretacja wyników dla Tezy 1

> ✏️ **Wskazówka:** Odpowiedz na pytania: ile % jest NEW, co to oznacza, jakie są przykłady nowych reguł i co je odróżnia od PIT.

*[Do uzupełnienia po eksperymencie]*

Odsetek operatorów sklasyfikowanych jako NEW wynosi [X]%, co oznacza, że LLM wygenerował reguły mutacyjne nieposiadające odpowiednika w katalogu PIT „ALL" dla [X]% wszystkich indukowalnych klas zmian. *[Zinterpretuj w kontekście: wysoki % → LLM rzeczywiście rozszerza przestrzeń mutacji; niski % → LLM replikuje głównie znane wzorce.]*

Wśród operatorów NEW wyróżnić można następujące klasy zmian, nieobecne w PIT: *[lista z opisami przykładów].* Operator X (*[nazwa]*) generuje mutanty polegające na *[opis reguły]*, czego żaden z operatorów grupy ALL nie realizuje, ponieważ *[uzasadnienie]*.

Compile rate dla mutantów LLM wynosi [X]% wobec [Y]% dla PIT. *[Zinterpretuj: wyższy compile rate PIT wynika z faktu, że PIT operuje na bytecode i zawsze generuje syntaktycznie poprawny kod; LLM może generować zmiany naruszające typy lub składnię Javy.]*

### 6.2 Interpretacja wyników dla Tezy 2

> ✏️ **Wskazówka:** Porównaj mediany proximity, wyjaśnij co to znaczy. Uwaga: wyższy mutation score nie zawsze = lepszy mutant.

*[Do uzupełnienia po eksperymencie]*

Mediana proximity dla mutantów LLM wynosi [X], wobec [Y] dla mutantów PIT. *[Zinterpretuj: jeśli LLM > PIT — mutanty LLM wywołują bardziej zbliżone reakcje zestawu testów do tych wywoływanych przez rzeczywiste błędy, co sugeruje wyższy realizm generowanych mutantów.]*

Ważnym zastrzeżeniem interpretacyjnym jest relacja między mutation score a proximity. Wysoki mutation score może paradoksalnie wskazywać na mutanty łatwe do wykrycia — trywialnie różne od oryginału — a nie na mutanty realistyczne. *[Jeśli LLM ma niższy mutation score ale wyższą proximity — wyjaśnij że to potencjalnie korzystny wynik: mutanty LLM są trudniejsze do wykrycia, ale bardziej zbliżone do realnych bugów.]*

Test statystyczny (Mann-Whitney U) *[wynik testu i interpretacja p-value]*.

### 6.3 Interpretacja wyników dla Tezy 3

> ✏️ **Wskazówka:** Skupiasz się na porównaniu LLM vs matched PIT (tylko pary EXISTING/PARTIAL).
> Interpretuj każdą metrykę osobno, potem wyciągnij wniosek zbiorczy.

*[Do uzupełnienia po eksperymencie]*

W porównaniu bezpośrednim operatorów LLM z ich klasycznymi odpowiednikami PIT (N = [liczba par]):

- **Duplicate rate:** LLM osiąga [X]% wobec [Y]% dla PIT. *[Zinterpretuj: niższy duplicate rate LLM sugeruje większą różnorodność wygenerowanych mutantów w obrębie tego samego operatora.]*
- **Compile rate:** LLM [X]% vs PIT [Y]%. *[Jeśli niższy dla LLM — koszt wynikający z generacji nieskompilowanych wariantów; jeśli porównywalny — LLM nie generuje znaczącej liczby błędów składniowych.]*
- **Proximity (mediana):** LLM [X] vs PIT [Y]. *[Zinterpretuj w kontekście Tezy 2.]*
- **Equivalent rate:** LLM [X]% vs PIT [Y]%. *[Niższy equivalent rate LLM oznaczałby, że LLM generuje mniej semantycznie neutralnych mutantów.]*
- **Liczba zastosowań:** LLM [X] vs PIT [Y]. *[Wyższa liczba zastosowań oznacza, że reguła LLM ma szersze zastosowanie w kodzie.]*

Łącznie wyniki dla Tezy 3 sugerują, że *[wniosek zbiorczy]*.

---

---

## Rozdział 7 — Wnioski z eksperymentu

### 7.1 Wnioski dla Tezy 1

> ✏️ **Wskazówka:** Jedno zdanie: czy teza potwierdzona, częściowo potwierdzona, czy odrzucona.
> Następnie 2–3 zdania: co dokładnie wiesz po eksperymencie, czego nie wiesz.

*[Do uzupełnienia po eksperymencie]*

**Odpowiedź na Tezę 1:** *[Np.: „Teza 1 została potwierdzona. LLM wygenerował X operatorów sklasyfikowanych jako NEW, co stanowi Y% wszystkich indukowalnych operatorów. Oznacza to, że …"]*

### 7.2 Wnioski dla Tezy 2

*[Do uzupełnienia po eksperymencie]*

**Odpowiedź na Tezę 2:** *[Np.: „Teza 2 została częściowo potwierdzona. Mediana proximity mutantów LLM była istotnie wyższa niż dla PIT (X vs Y, p < 0.05), jednak różnica dotyczyła głównie projektów …"]*

### 7.3 Wnioski dla Tezy 3

*[Do uzupełnienia po eksperymencie]*

**Odpowiedź na Tezę 3:** *[Np.: „Teza 3 nie została jednoznacznie potwierdzona. Operatory LLM osiągnęły niższy duplicate rate, jednak niższy compile rate wskazuje na wyższy koszt operacyjny …"]*

### 7.4 Zagrożenia dla rzetelności wyników

> ✏️ **Wskazówka:** Napisz krótko i uczciwie — to jest standardowy element prac empirycznych.
> Każde zagrożenie = jedna lub dwie linijki.

- **Zależność od datasetu:** Wyniki mogą nie generalizować się poza projekty Defects4J Java; inne języki lub domeny mogą wykazywać inne rozkłady metryk.
- **Niedeterminizm LLM:** Zmiana wersji modelu, temperatury lub formatu promptu wpływa na generowane mutanty. Wszystkie parametry zostały zalogowane, jednak wyniki mogą być trudne do odtworzenia w przyszłości po aktualizacji modelu.
- **Heurystyka etykietowania NEW/EXISTING:** Klasyfikacja operatorów opiera się na arbitralnych progach Jaccarda i heurystykach AST, a nie na formalnej klasyfikacji semantycznej. Progi te są arbitralne i mogą nie uchwycić wszystkich przypadków granicznych.
- **Przybliżenie equivalent rate:** Mutant niezabity przez żaden test nie musi być semantycznie równoważny — może po prostu nie być pokryty przez testy. Metryka ta jest traktowana jako przybliżenie, nie jako dokładna miara.
- **Zakres ręcznej weryfikacji klastrów:** Ręczna weryfikacja 2 oceniających jest subiektywna i może nie obejmować wszystkich klastrów granicznych.

---

## Podsumowanie

### Cel i zakres pracy — przypomnienie

> ✏️ **Wskazówka:** 2–3 zdania przypominające cel pracy. Nie przepisuj Wstępu — podsumuj.

Niniejsza praca postawiła sobie za cel empiryczną weryfikację, czy duże modele językowe są w stanie generować wartościowe operatory mutacyjne wykraczające poza klasyczny katalog PIT. W ramach jednego kompleksowego eksperymentu na zbiorze [N] błędów z Defects4J wygenerowano i przeanalizowano [łączna liczba] mutantów LLM oraz [liczba] mutantów PIT, zbierając dane umożliwiające odpowiedź na trzy tezy badawcze.

### Najważniejsze wyniki

> ✏️ **Wskazówka:** 3–5 liczb. Każdy wynik = jedno zdanie z wartością i jednozdaniową interpretacją.

*[Do uzupełnienia po eksperymencie]*

- **T1 (nowość):** *[X]%* wygenerowanych operatorów LLM nie posiadało odpowiednika w katalogu PIT „ALL", co wskazuje na *[interpretacja]*.
- **T2 (bliskość do rzeczywistych błędów):** Mediana proximity mutantów LLM wyniosła *[X]* wobec *[Y]* dla PIT, a różnica była *[istotna/nieistotna statystycznie]*, co sugeruje *[interpretacja]*.
- **T3 (wydajność):** W porównaniu bezpośrednim operator-do-operatora, LLM osiągnął *[X]*% duplicate rate wobec *[Y]*% dla PIT, przy *[wyższym/niższym/porównywalnym]* compile rate.

### Ograniczenia badania

> ✏️ **Wskazówka:** 3–4 zdania. Bądź uczciwy — każda dobra praca naukowa ma ograniczenia.

Badanie jest ograniczone do języka Java i projektów dostępnych w Defects4J, co może ograniczać generalizowalność wyników na inne języki i domeny aplikacyjne. Zastosowana heurystyka etykietowania operatorów jako NEW/PARTIAL/EXISTING jest oparta na arbitralnych progach Jaccarda i heurystykach AST, a nie na formalnej klasyfikacji semantycznej. Ponadto niedeterministyczna natura LLM oznacza, że wyniki eksperymentu są związane z konkretną wersją i konfiguracją użytego modelu.

### Kierunki dalszych badań

> ✏️ **Wskazówka:** 3–4 konkretne kierunki — krótkie, ale specyficzne.

- **Rozszerzenie na inne języki** — przeprowadzenie analogicznego eksperymentu dla Pythona (QuixBugs, ConDefects) i JavaScript w celu zbadania, czy wyniki są językowo specyficzne.
- **Automatyzacja klasteryzacji** — zastąpienie ręcznej weryfikacji klastrów automatyczną walidacją z użyciem LLM jako sędziego spójności semantycznej opisów reguł.
- **Porównanie modeli LLM** — zbadanie, czy różne modele (GPT-4, Claude, Gemini, CodeLlama) indukują różne zestawy operatorów i który z nich osiąga najwyższą proximity.
- **Formalna klasyfikacja semantyczna** — opracowanie metodologii klasyfikacji opartej na AST diff zamiast heurystyk tekstowych, co zwiększyłoby precyzję etykietowania NEW/EXISTING.

---

## Bibliografia

> ✏️ **Wskazówka:** Uzupełnij format zgodnie z wymaganiami uczelni. Poniżej lista pozycji z APA-podobnym formatem.

1. Just, R., Jalali, D., & Ernst, M. D. (2014). *Defects4J: A Database of Existing Faults to Enable Controlled Testing Studies for Java Programs.* Proceedings of ISSTA 2014, San Jose, CA.

2. Jia, Y., & Harman, M. (2011). *An Analysis and Survey of the Development of Mutation Testing.* IEEE Transactions on Software Engineering, 37(5), 649–678.

3. Papadakis, M., Kintis, M., Zhang, J., Jia, Y., Le Traon, Y., & Harman, M. (2019). *Mutation Testing Advances: An Analysis and Survey.* Advances in Computers, 112, 275–378.

4. DeMillo, R. A., Lipton, R. J., & Sayward, F. G. (1978). *Hints on Test Data Selection: Help for the Practicing Programmer.* IEEE Computer, 11(4), 34–41.

5. PIT Mutation Testing. (n.d.). https://pitest.org/quickstart/mutators/

6. Chen, M., Tworek, J., Jun, H., Yuan, Q., et al. (2021). *Evaluating Large Language Models Trained on Code.* arXiv:2107.03374.

7. Fan, A., Gokkaya, B., Harman, M., Lyubarskiy, M., Sengupta, S., Yoo, S., & Zhang, J. Y. (2023). *Large Language Models for Software Engineering: Survey and Open Problems.* arXiv:2310.03533.

8. *[Pozycje dotyczące LLM i mutation testing — do uzupełnienia po przeglądzie literatury, np. prace o MutationGPT, ChatMut, itp.]*

9. *[Pozycja dotycząca HDBSCAN lub wybranego algorytmu klasteryzacji]*

10. *[Pozycja dotycząca wybranego modelu embeddingowego]*

---

> 📌 **Proponowana kolejność pisania rozdziałów:**
> 1. Rozdział 2 (pipeline + tezy) — gotowe powyżej
> 2. Rozdział 4.1 (założenia eksperymentu) — gotowe powyżej
> 3. Implementacja eksperymentu (`notebooks/`)
> 4. Rozdział 4.2 (wyniki — uzupełnij tabele)
> 5. Rozdział 4.3–4.4 (interpretacja i wnioski)
> 6. Rozdział 3 (teoria)
> 7. Rozdział 1 — Wstęp (doprecyzowanie)
> 8. Streszczenie (jako ostatnie)
