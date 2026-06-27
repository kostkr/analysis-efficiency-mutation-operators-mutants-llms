"""Generate pipeline diagrams for thesis chapter 7."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams['font.family'] = 'DejaVu Sans'

OUTPUT_DIR = '/Users/douher/IdeaProjects/DP/diploma/images'

H = 0.8
GAP = 0.35


def box(ax, cx, cy, w, h, text, color='#E3F2FD', edge='#1976D2', fs=8):
    x, y = cx - w/2, cy - h/2
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                       facecolor=color, edgecolor=edge, linewidth=1.8)
    ax.add_patch(p)
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs, fontweight='bold')


def arr(ax, cx, y1, y2):
    ax.annotate('', xy=(cx, y2 + 0.03), xytext=(cx, y1 - 0.03),
                arrowprops=dict(arrowstyle='->', lw=1.6, color='#424242'))


def arr_diag(ax, x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2 + 0.03), xytext=(x1, y1 - 0.03),
                arrowprops=dict(arrowstyle='->', lw=1.6, color='#424242'))


def generate_diagram_1():
    cx = 5.5
    pcx, lcx = 2.8, 8.2
    W_common = 5.8
    W_branch = 4.5

    fig, ax = plt.subplots(figsize=(11, 13.2))
    ax.set_xlim(0, 11)
    ax.set_ylim(3.0, 16)
    ax.axis('off')

    # --- COMMON PART ---
    y = 15.3
    common = [
        ('Przetwarzanie po kolei wszystkich defektów\n(843 aktywnych defektów ze zbioru Defect4j)', H),
        ('Wyznaczenie listy zmodyfikowanych klas\n(defects4j export -p classes.modified)', H),
        ('Wyznaczenie listy zmodyfikowanych linii kodu\n(diff pomiędzy buggy a fixed)', H),
        ('Określenie metod i bloków statycznych\n(zawierających zmienione linie)', H),
        ('Przygotowanie listy fragmentów kodu do generowania mutantów\n(identycznej dla PIT i LLM)', H),
    ]
    colors_common = [
        ('#FFF8E1', '#F9A825'),
        ('#E3F2FD', '#1976D2'),
        ('#E3F2FD', '#1976D2'),
        ('#E3F2FD', '#1976D2'),
        ('#E3F2FD', '#1976D2'),
        ('#E3F2FD', '#1976D2'),
        ('#E8F5E9', '#388E3C'),
    ]

    for i, ((text, h), (color, edge)) in enumerate(zip(common, colors_common)):
        box(ax, cx, y, W_common, h, text, color=color, edge=edge, fs=8)
        bot = y - h/2
        if i < len(common) - 1:
            arr(ax, cx, bot, bot - GAP)
        y -= (h + GAP)

    split_y = y + GAP + common[-1][1]/2
    split_bot = split_y - common[-1][1]/2

    # --- LABELS ---
    label_y = split_bot - GAP - 0.15
    ax.text(pcx, label_y, 'PIT (x1)', ha='center', fontsize=12, fontweight='bold', color='#7B1FA2')
    ax.text(lcx, label_y, 'LLM (x2)', ha='center', fontsize=12, fontweight='bold', color='#2E7D32')
    arr_diag(ax, cx - 1.2, split_bot, pcx + 0.5, label_y + 0.15)
    arr_diag(ax, cx + 1.2, split_bot, lcx - 0.5, label_y + 0.15)

    # --- PIT COLUMN ---
    pit = [
        ('Kompilacja całego projektu\n(defects4j compile)', H),
        ('Grupowanie fragmentów kodu według klas\n(dla każdej klasy wspólna generacja --targetClass)', H),
        ('Generacja mutantów dla każdej klasy\n(linia + kod przed + kod po + reguła + metadane)', H),
        ('Oznaczenie duplikatów mutantów\n(duplikaty syntaktyczne)', H),
        ('Zapis wyników do pliku\n\\${defect_name}/mutants/classic.json\n(id, filepath, precode, aftercode, rule, gen_time_s, dublicate)', H),
    ]

    py = label_y - 0.6
    for i, (text, h) in enumerate(pit):
        box(ax, pcx, py, W_branch, h, text, color='#F3E5F5', edge='#7B1FA2', fs=8)
        bot = py - h/2
        if i < len(pit) - 1:
            arr(ax, pcx, bot, bot - GAP)
        py -= (h + GAP)

    # --- LLM COLUMN ---
    llm = [
        ('Przygotowanie promptu z fragmentem kodu\n(liczba linij kodu == oczekiwana liczba mutantów)', H),
        ('Wysłanie zapytania do serwera LLM\n(prompt + konfiguracja generacji)', H),
        ('Parsowanie odpowiedzi do json z mutantami\n(usuwane są tagi generacji) ', H),
        ('Oznaczenie duplikatów mutantów\n(duplikaty syntaktyczne)', H),
        ('Zapis wyników do pliku\n\\${defect_name}/mutants/\\${model_name}.json\n(id, filepath, precode, aftercode, rule, gen_time_s, dublicate)', H),
    ]

    ly = label_y - 0.6
    for i, (text, h) in enumerate(llm):
        box(ax, lcx, ly, W_branch, h, text, color='#E8F5E9', edge='#2E7D32', fs=8)
        bot = ly - h/2
        if i < len(llm) - 1:
            arr(ax, lcx, bot, bot - GAP)
        ly -= (h + GAP)

    fig.tight_layout()
    path = f'{OUTPUT_DIR}/pipeline-generacja-mutantow.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  {path}')


def generate_diagram_2():
    """Przebieg eksperymentu: weryfikacja mutantów."""
    W = 5.8

    steps = [
        ('Przetwarzanie po kolei wszystkich defektów\n(843 aktywnych defektów ze zbioru Defect4j)', H, '#FFF8E1', '#F9A825'),
        ('Uruchamianie testów na wersji fixed\n(suite_profile + lista relewantnych testów)', H, '#E3F2FD', '#1976D2'),
        ('Uruchamianie testów na wersji buggy\n(bug_profile + lista testów wykrywających defekt)', H, '#E3F2FD', '#1976D2'),
        ('Wczytanie nie duplikowanych mutantów\n(classic.json + gemma4.json + qwen3.6.json)', H, '#FFF8E1', '#F9A825'),
        ('Utworzenie 10 kopii checkout fixed\n(pula workerów do równoległego wykonania)', H, '#E3F2FD', '#1976D2'),
        ('Podmiana linii w pliku źródłowym\n(precode -> aftercode w konkretnej linii)', H, '#E8EAF6', '#303F9F'),
        ('Kompilacja projektu ze zmianą\n(jeśli błąd -> compiled=false, następny mutant)', H, '#E8EAF6', '#303F9F'),
        ('Uruchomienie relewantnych testów defects4j test -r\n(timeout = min(config, max(160s, 0.038s × N_testów)))', H, '#E8EAF6', '#303F9F'),
        ('Zebranie wyników\n(failing_tests, compile_time_s, test_time_s)', H, '#E8EAF6', '#303F9F'),
        ('Przywrócenie oryginalnego pliku źródłowego\n(reset workera jeśli compile_fail lub timeout)', H, '#E8EAF6', '#303F9F'),
        ('Zapis wyników do \\${defect_name}/results/{mutant_name}.json\n(mutant_id, compiled, failing_tests, test_time_s)', H, '#FFF8E1', '#F9A825'),
        ('Podsumowanie metryk dla defektu \\${defect_name}/meta.json\n(suite_profile, bug_profile, statystyki)', H, '#FFF8E1', '#F9A825'),
    ]

    total_h = sum(h for _, h, _, _ in steps) + len(steps) * GAP + 0.8
    fig, ax = plt.subplots(figsize=(8, total_h - 0.7))
    ax.set_xlim(0, 8)
    ax.set_ylim(0.7, total_h)
    ax.axis('off')

    cx = 3.5
    y = total_h - 0.5

    positions = []
    for i, (text, h, color, edge) in enumerate(steps):
        box(ax, cx, y, W, h, text, color=color, edge=edge, fs=8)
        positions.append((y, h))
        bot = y - h/2
        if i < len(steps) - 1:
            arr(ax, cx, bot, bot - GAP)
        y -= (h + GAP)

    # Loop: square arrow going from bottom back up to top (right side)
    # Shows that steps 5-10 repeat for each non-duplicate mutant
    loop_top = positions[5][0]  # top of first loop step
    loop_bot = positions[10][0]  # bottom of last loop step
    rx = cx + W/2 + 0.3   # start point right of boxes
    rx2 = rx + 0.7         # how far right the line goes

    # Square path: bottom-right → top-right → arrow back to top step
    ax.plot([rx, rx, rx2], [loop_bot, loop_bot, loop_bot],
            color='#303F9F', lw=2, solid_capstyle='round')
    ax.plot([rx2, rx2], [loop_bot, loop_top],
            color='#303F9F', lw=2, solid_capstyle='round')
    # Arrow pointing left back into top of loop
    ax.annotate('', xy=(rx, loop_top),
                xytext=(rx2, loop_top),
                arrowprops=dict(arrowstyle='->', lw=2, color='#303F9F'))

    # Label next to vertical line
    ax.text(rx2 + 0.15, (loop_top + loop_bot) / 2,
            'dla każdego\nnieduplikowanego\nmutanta',
            fontsize=8, fontweight='bold', color='#303F9F', va='center', ha='left')

    fig.tight_layout()
    path = f'{OUTPUT_DIR}/pipeline-przebieg-eksperymentu.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  {path}')


if __name__ == '__main__':
    print('Generating diagrams:')
    generate_diagram_1()
    generate_diagram_2()
    print('Done.')
