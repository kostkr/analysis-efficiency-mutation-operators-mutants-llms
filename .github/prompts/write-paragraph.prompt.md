---
name: write-paragraph
description: Pisanie samodzielnych akapitów lub krótkich podrozdziałów pracy dyplomowej po polsku w formalnym, akademickim stylu. Każdy tekst musi być semantycznie niezależny i kompletny, bez odwołań do innych sekcji pracy.
argument-hint: "Wklej PLAN, DANE oraz FRAGMENT (TO DO lub akapit do poprawy)"
---

# Skill Pisanie akapitów do pracy dyplomowej po polsku

## Cel

Zadaniem tego skillu jest generowanie akapitów lub krótkich podrozdziałów pracy dyplomowej po polsku w **formalnym stylu akademickim**, odpowiednim dla pracy licencjackiej, inżynierskiej lub magisterskiej. Tekst powinien być precyzyjny, rzeczowy i jednoznaczny, bez kolokwializmów oraz bez struktur typowych dla stylu popularnonaukowego lub eseistycznego.

Każdy wygenerowany fragment musi być kompletny informacyjnie. Czytelnik powinien być w stanie zrozumieć definicję, znaczenie oraz rolę opisywanego pojęcia wyłącznie na podstawie tej sekcji, bez konieczności sięgania do innych części pracy.

## Terminologia

W tekście należy pozostawiać wybrane terminy techniczne w języku angielskim, takie jak *mutation testing*, *mutant*, *compilation*, *duplicate mutation*, *equivalent mutant*.

Przy pierwszym użyciu terminu angielskiego należy dodać krótkie, rzeczowe wyjaśnienie po polsku w nawiasie. W dalszej części tekstu należy konsekwentnie stosować ustalone nazewnictwo, bez wprowadzania synonimów ani parafraz.

## Zasady niezależności sekcji

Każdy akapit lub podrozdział musi stanowić samodzielną jednostkę treściową. Tekst nie może:
- zawierać odwołań do innych rozdziałów ani sekcji,
- zakładać znajomości terminów niezdefiniowanych w danej części,
- sugerować dalszej analizy w innym fragmencie pracy.

Wszelkie informacje niezbędne do zrozumienia omawianego zagadnienia muszą być zawarte wyłącznie w tej sekcji.

## Styl i konstrukcja tekstu

Każdy fragment powinien być zbudowany logicznie i spójnie, z zachowaniem akademickiego tonu. Zalecany układ treści obejmuje:
- zwięzłe wprowadzenie przedstawiające zakres i sens omawianego pojęcia,
- precyzyjną definicję techniczną dostosowaną do kontekstu pracy dyplomowej,
- listę punktowaną porządkującą kluczowe aspekty metodologiczne lub praktyczne,
- krótki akapit podsumowujący, zamykający tok rozumowania bez stosowania wyróżnionych etykiet.

Nie należy rozpoczynać zdań od konstrukcji składających się z dwóch słów zakończonych kropką lub dwukropkiem.

## Ograniczenia treści

Tekst nie może:
- zaczynać się od ogólnikowych formuł typu „Dla przeprowadzenia badania” ani „W niniejszym rozdziale”,
- zawierać przykładów kodu, pseudokodu ani opisów scenariuszy wykonania,
- wprowadzać wzorów matematycznych, formalnych definicji metryk ani oznaczeń zbiorów,
- zawierać cytowań, przypisów ani bibliografii,
- wprowadzać danych liczbowych, jeśli nie zostały jednoznacznie dostarczone przez użytkownika.

W przypadku braku wymaganych informacji należy jawnie zastosować oznaczenie [DO UZUPEŁNIENIA].

## Spójność z dostarczonym tekstem

Wygenerowany tekst musi być spójny znaczeniowo z dostarczonym fragmentem pracy. Należy:
- uzupełniać wyłącznie miejsca oznaczone jako TO DO,
- przeredagowywać tylko fragmenty wskazane przez użytkownika,
- zachować przyjętą terminologię i założenia metodologiczne.

W przypadku wykrycia niejednoznaczności należy przyjąć interpretację dominującą w dostarczonym materiale, bez wprowadzania nowych założeń.

## Format odpowiedzi

Tekst należy zapisać w Markdown.

Akapity powinny być zwarte i formalne, a listy punktowane stosowane wyłącznie w celu zwiększenia przejrzystości argumentacji. Na końcu każdej sekcji należy dodać krótki akapit podsumowujący, bez nagłówków typu „Wnioski”.

## Dane wejściowe od użytkownika

Użytkownik dostarcza trzy bloki:
- PLAN określający zakres merytoryczny sekcji,
- DANE zawierające informacje techniczne lub kontekst badawczy,
- FRAGMENT obejmujący aktualny tekst lub miejsca oznaczone jako TO DO.

## Sposób działania

Na podstawie dostarczonych materiałów:
- analizowana jest kompletność oraz formalność stylu,
- identyfikowane są elementy wymagające doprecyzowania,
- generowany jest wyłącznie tekst zgodny z PLANEM i FRAGMENTEM.

Zakres treści nie może być rozszerzany poza zadane ramy.

## Kontrola jakości

Na końcu odpowiedzi należy dodać krótką checklistę obejmującą:
- ocenę formalnego, akademickiego charakteru tekstu,
- zgodność treści z planem i dostarczonym fragmentem,
- potwierdzenie braku metryk, wzorów, przykładów oraz bibliografii.

---

# TERAZ: Wygeneruj odpowiedź na podstawie wklejonych bloków [PLAN], [DANE], [FRAGMENT].
