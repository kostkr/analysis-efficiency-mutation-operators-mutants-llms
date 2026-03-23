# LLM-Mutants: Analysis of the effectiveness of generating mutation operators (mutants) using large language models

This document contains the planned research and methodology for a master's thesis entitled "LLM-Mutants: Analysis of the effectiveness of generating mutation operators (mutants) via large language models." The primary goal is to investigate whether large language models (LLMs) can induce new, meaningful mutation operators, evaluate their quality compared to classical mutation operators (e.g., PIT "ALL"), and measure how closely LLM-generated mutants resemble real bugs.

# [LLM-Mutants] Analiza efektywności generowania Operatorów mutacyjnych (Mutantów) poprzez duże modele jezykowe

## Definicji

- **Obecnie znane operatory mutacyjne** -  opisane w [pitest](https://pitest.org/quickstart/mutators/) jako "ALL" group. To będą "klasyczne" operatory mutacyjne do porównania.

- **Operator LLM (LLM‑mutator)** – reguła zmiany kodu wyindukowana przez LLM (opis tekstowy + przykład zmiany), którą można zastosować do wielu miejsc w kodzie, by tworzyć mutanty. (W przeciwieństwie do PIT, nie jest to gotowy, wcześniej zdefiniowany mutator).

- **Mutant** – wersja programu zawierająca drobną, zaprojektowaną zmianę w kodzie, mającą na celu sprawdzenie siły zestawu testów.

- **Zabicie (kill)** – zdarzenie, gdy istniejące testy wykrywają różnicę w zachowaniu między oryginalną wersją a mutantem.
- 
- **Mutation score** – odsetek zabitych mutantów w danym zbiorze wygenerowanych mutantów; im wyższy, tym silniejszy zestaw testów.

- **Equivalent mutant** – mutant, który nie zmienia programu w sposób wykrywalny przez testy, zwiększa koszt analizy bez dodawania nowej informacji.

- **Duplicate mutant=** – mutant, który jest semantycznie taki sam jak inny mutant, mimo że patch wygląda inaczej. Powoduje sztuczne zawyżenie liczby mutantów.

- **Kompilowalność** – procent wygenerowanych mutantów, które się kompilują.

- **Bliskość do prawdziwego błędu (proximity)** – miara określająca, na ile mutant przypomina rzeczywisty błąd. Może być mierzona przez podobieństwo behawioralne (porównanie testów, które nie przechodzą dla bugu i mutanta) oraz semantyczne (B25 lub embedding model) (które byłoby lepsze?).

- **Bliski klasyczny odpowiedni”** – operator z PIT (grupa "ALL"), który jest najbardziej podobny do operatora wygenerowanego przez LLM; sposób dokładnego dopasowania wymaga jeszcze ustalenia.

**Repozytoria usterek** (Datasets) rzeczywistych bugów:
- [Defects4J](https://github.com/rjust/defects4j) (ok. 854 aktywnych bugów w nowszych wydaniach)
- [ConDefects](https://github.com/appmlk/ConDefects) (1254 bugów Java, dodatkowo Python)
- [QuixBugs](https://github.com/jkoppel/QuixBugs) (40 zadań, Python/Java)

## Plan badania

**Cel:** sprawdzić, czy duże modele językowe (LLM) mogą wygenerować nowe reguły mutacyjne (operatorów LLM),
których nie ma w klasycznej liście PIT (grupa "ALL") oraz ocenić ich jakość względem klasycznych operatorów.

1. **Generacja mutacji przez LLM**
   - Dla wybranych bugów z Datasets poprosić LLM o wygenerowanie mutacji wraz z opisem zasady mutacji (opis tekstowy).
   - Dla każdej wygenerowanej mutacji zapisać metadane: opis zasady, patch, lokalizacja w kodzie.

2. **Klasteryzacja mutacji w operatory LLM**
   - Grupowanie podobnych mutacji według opisu zasady i wzorca edycji (można użyć embedding modelu do policzenia podobieństwa).
   - Zdefiniowanie każdego klastra jako pojedynczego operatora LLM (opis reguły + przykładowe zastosowania).

3. **Porównanie z klasycznymi operatorami PIT**
   - Dla każdego operatora LLM sprawdzić, czy istnieje "bliski klasyczny odpowiednik" w PIT (typ zmiany, efekt semantyczny.).
   - Brak dopasowania → operator LLM traktowany jako potencjalnie nowy operator mutacyjny.

4. **Filtracja mutantów LLM (przed analizą)**
   - Sprawdzenie kompilowalności: skompilować każdy mutant i odfiltrować te, które się nie kompilują (zachować powody odrzutu).
   - Usunięcie duplikatów semantycznych: wykryć i usunąć semantyczne duplikaty (np. porównanie AST, clustering na embeddingach kodu lub heurystyki porównawcze).
   - Dokumentować liczbę i przyczyny odrzuconych mutantów; te statystyki będą raportowane jako koszt generacji operatorów LLM.

5. **Walidacja techniczna operatorów LLM**
   - Kompilowalność (po filtracji): wygenerować mutanty na podstawie reguły i sprawdzić, jaki % kompiluje się poprawnie.
   - Powtarzalność / użyteczność: ocenić, czy regułę da się zastosować wielokrotnie w różnych miejscach i projektach (liczba zastosowań).

## Tezy badawcze
Tu opisany plan badania dla poszczególnych tez badawczych.

### Czy da się generować inne niż obecnie znane operatory mutacyjne za pomocą LLM?

Metryki odpowiadające na tę tezę:
- **% nowych operatorów** – odsetek operatorów LLM bez odpowiednika w PIT "ALL".
- **Kompilowalność** – procent kompilujących się mutantów wygenerowanych przez daną regułę.
- **Liczba zastosowań** – jak często reguła ma sensowne zastosowanie w kodzie różnych projektów (Duplicate mutant, Equivalent mutant).

### Czy operatory LLM są bliższe prawdziwym usterkom?

Metryki odpowiadające na tę tezę:
- **Bliskość do prawdziwego błędu** – podobieństwo profilu PASS/FAIL mutanta i podobieństwo semantyczne.
- **Mutation score** – odsetek mutantów wykrywanych przez testy dla operatorów LLM vs odpowiedniki PIT.

### Czy operatory LLM są bardziej wydajne od „bliskich" klasycznych odpowiedników?

Metryki odpowiadające na tę tezę:
- **Mutation score** operatorów LLM vs ich „bliskich klasycznych odpowiedników" z PIT.
- **Kompilowalność** – porównanie odsetka kompilujących się mutantów: LLM vs PIT.
- **Duplicate rate** – odsetek duplikatów semantycznych wśród mutantów: LLM vs PIT.
- **Liczba zastosowań** – średnia liczba miejsc w kodzie, gdzie dana reguła ma zastosowanie: LLM vs PIT.
