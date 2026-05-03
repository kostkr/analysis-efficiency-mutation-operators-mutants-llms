"""pit/generator.py — minimal PIT CLI mutant generator.

Design goal
-----------
Do the minimum necessary work:
1. run PIT once for a class,
2. read ``mutations.xml``,
3. map PIT entries back to source lines when possible,
4. save every reported mutation in the standard mutant JSON shape.

This module tries to reconstruct source-level single-line mutants when that can
be done with a deterministic local transformation.  For operators that still
cannot be reconstructed precisely, it falls back conservatively instead of
inventing unrelated source edits.
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from ..base import BaseGenerator, GeneratorJob, PITConfig
from .xml_parser import parse_mutation_entries

if TYPE_CHECKING:
    from ...container import Defects4J
    from ...mutant import Mutant

_PIT_MAIN = "org.pitest.mutationtest.commandline.MutationCoverageReport"


class PITGenerator(BaseGenerator):
    """Generate mutants using the PIT CLI inside the Defects4J container."""

    def __init__(self, config: PITConfig, d4j: "Defects4J") -> None:
        self.config = config
        self.d4j = d4j
        self._classpath_cache: dict[str, str] = {}
        self._src_dir_cache: dict[str, str] = {}
        self._tests_cache: dict[str, str] = {}
        self._entry_cache: dict[tuple[str, str], list[dict]] = {}
        self._source_cache: dict[tuple[str, str], list[str]] = {}
        self._javap_cache: dict[tuple[str, str], str] = {}
        self._line_map_cache: dict[tuple[str, str], dict[str, dict[int, int]]] = {}

    def generate(self, job: GeneratorJob, compile_first: bool = True) -> list["Mutant"]:
        """Run PIT for *job.class_fqn* and return one Mutant per PIT XML entry."""
        t0 = time.perf_counter()

        if compile_first:
            clean_cmd = self._clean_compile_cmd(job.container_path)
            _, _, rc = self.d4j.exec(clean_cmd, timeout=180)
            if rc != 0:
                print(f"[PITGenerator] defects4j compile failed for {job.class_fqn}")
                return []

        try:
            classpath = self._classpath(job.container_path)
            src_dir = self._source_dir(job.container_path)
            tests = self._resolve_target_tests(job)
        except RuntimeError as exc:
            print(f"[PITGenerator] defects4j export failed for {job.class_fqn}: {exc}")
            return []

        report_dir = f"{job.container_path}/target/pit-reports-{self._safe_name(job.class_fqn)}"
        cmd = self._build_cli_cmd(
            class_fqn=job.class_fqn,
            classpath=classpath,
            src_dir=src_dir,
            report_dir=report_dir,
            target_tests=tests,
        )

        out, err, rc = self.d4j.exec(
            f"cd {job.container_path} && {cmd}",
            timeout=self.config.timeout_s,
        )
        gen_time = round(time.perf_counter() - t0, 2)

        if rc != 0:
            short = (err or out or "").strip()[-800:]
            print(f"[PITGenerator] PIT CLI failed for {job.class_fqn} (rc={rc}):\n{short}")
            return []

        xml_raw, _, xml_rc = self.d4j.exec(f"cat {report_dir}/mutations.xml 2>/dev/null")
        if xml_rc != 0 or not xml_raw.strip():
            print(f"[PITGenerator] mutations.xml not found for {job.class_fqn}")
            return []

        entries = parse_mutation_entries(xml_raw)
        self._entry_cache[(job.container_path, job.class_fqn)] = entries

        mutants = self._mutants_from_entries(job, entries)
        if mutants:
            per_mutant = round(gen_time / len(mutants), 2)
            for m in mutants:
                m.gen_time_s = per_mutant
        return mutants

    def raw_method_entry_count(self, container_path: str, class_fqn: str, method_name: str) -> int:
        """Return how many PIT XML entries were reported for one method."""
        entries = self._raw_entries(container_path, class_fqn)
        if not method_name:
            return len(entries)
        return sum(1 for item in entries if item.get("mutated_method") == method_name)

    def _mutants_from_entries(self, job: GeneratorJob, entries: list[dict]) -> list["Mutant"]:
        from ...mutant import Mutant

        source_lines = self._source_lines(job.container_path, job.filepath)
        line_maps = self._method_line_maps(job.container_path, job.class_fqn)
        mutants: list[Mutant] = []
        seen_counts: dict[tuple[int, str, str], int] = {}

        for item in entries:
            method_name = item.get("mutated_method", "")
            if job.method_name and method_name != job.method_name:
                continue

            mutator = item.get("mutator", "")
            description = item.get("description", "")
            raw_line = int(item.get("line", 0) or 0)
            index = int(item.get("index", -1))
            mapped_line = self._map_index_to_source_line(method_name, index, raw_line, line_maps)
            line_no = mapped_line if mapped_line > 0 else raw_line
            precode = self._line_text(source_lines, line_no)
            if not precode and raw_line != line_no:
                precode = self._line_text(source_lines, raw_line)
                if precode:
                    line_no = raw_line
            if not precode and job.method_start <= mapped_line <= job.method_end:
                precode = self._line_text(source_lines, mapped_line)
                if precode:
                    line_no = mapped_line
            if not precode:
                fallback_line, fallback_text = self._nearest_code_line(source_lines, line_no or raw_line)
                if fallback_text:
                    line_no = fallback_line
                    precode = fallback_text

            count_key = (line_no, raw_line, f"{item.get('rule', 'PIT')}|{description}")
            occurrence = seen_counts.get(count_key, 0)
            seen_counts[count_key] = occurrence + 1

            switch_line_no, switch_precode, switch_aftercode, switch_rule = self._reconstruct_switch_mutation(
                source_lines=source_lines,
                job=job,
                item=item,
            )
            if switch_aftercode and switch_precode:
                line_no = switch_line_no
                precode = switch_precode
                aftercode = switch_aftercode
                rule = switch_rule or item.get("rule", "PIT")
            else:
                aftercode, rule = self._reconstruct_source_mutation(
                    precode=precode,
                    item=item,
                    occurrence=occurrence,
                )
                if (not aftercode or aftercode == precode) and source_lines:
                    alt_line, alt_precode, alt_aftercode, alt_rule = self._search_nearby_source_mutation(
                        source_lines=source_lines,
                        base_line=line_no or raw_line,
                        item=item,
                        occurrence=occurrence,
                    )
                    if alt_aftercode and alt_precode and alt_aftercode != alt_precode:
                        line_no = alt_line
                        precode = alt_precode
                        aftercode = alt_aftercode
                        rule = alt_rule or rule
            if not aftercode:
                aftercode = precode or description.strip() or item.get("rule", "PIT")
            if not rule:
                rule = item.get("rule", "PIT")

            mutants.append(
                Mutant(
                    id=len(mutants) + 1,
                    filepath=job.filepath or item.get("filepath", ""),
                    line=line_no,
                    precode=precode,
                    aftercode=aftercode,
                    rule=rule,
                    gen_time_s=0.0,
                    pit_mutator=mutator,
                    pit_description=description,
                    pit_status=item.get("status", ""),
                    pit_detected=bool(item.get("detected", False)),
                    pit_tests_run=int(item.get("number_of_tests_run", 0)),
                    pit_killing_test=item.get("killing_test", ""),
                    pit_index=index,
                    pit_indexes=list(item.get("indexes", [])),
                    pit_blocks=list(item.get("blocks", [])),
                    pit_method=method_name,
                    pit_method_description=item.get("method_description", ""),
                )
            )

        return mutants

    def _reconstruct_source_mutation(self, precode: str, item: dict, occurrence: int) -> tuple[str, str]:
        rule = item.get("rule", "PIT")
        description = (item.get("description", "") or "").strip()
        line = precode or ""
        if not line:
            return "", rule

        if rule == "Conditionals Boundary":
            candidates = self._conditionals_boundary_candidates(line)
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Conditionals Boundary Mutator", line, chosen)

        if rule == "Math":
            candidates = self._math_candidates(line, description)
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Math Mutator", line, chosen)

        if rule == "Negate Conditionals":
            candidates = self._negate_conditionals_candidates(line)
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Negate Conditionals Mutator", line, chosen)

        if rule.startswith("Remove Conditional Mutator"):
            const = "true" if rule.endswith("IF") else "false"
            candidates = self._remove_conditional_candidates(line, const)
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff(rule, line, chosen)

        if rule == "Null Return Vals":
            chosen = self._null_return_candidate(line)
            return chosen, self._rule_with_diff("Null Return Vals Mutator", line, chosen)

        if rule == "Inline Constant":
            candidates = self._inline_constant_candidates(line, description)
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Inline Constant Mutator", line, chosen)

        if rule == "Increments":
            candidates = self._increment_candidates(line)
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Increments Mutator", line, chosen)

        if rule == "Remove Increments":
            candidates = self._remove_increment_candidates(line)
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Remove Increments Mutator", line, chosen)

        if rule == "Non Void Method Call":
            candidates = self._method_call_candidates(line, description, mode="default")
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Non Void Method Call Mutator", line, chosen)

        if rule == "Naked Receiver":
            candidates = self._method_call_candidates(line, description, mode="receiver")
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Naked Receiver Mutator", line, chosen)

        if rule == "Argument Propagation":
            candidates = self._method_call_candidates(line, description, mode="argument")
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Argument Propagation Mutator", line, chosen)

        if rule == "Constructor Call":
            candidates = self._constructor_call_candidates(line, description)
            chosen = self._pick_candidate(candidates, occurrence)
            return chosen, self._rule_with_diff("Constructor Call Mutator", line, chosen)

        return description.strip() or line, rule

    def _search_nearby_source_mutation(
        self,
        source_lines: list[str],
        base_line: int,
        item: dict,
        occurrence: int,
        radius: int = 6,
    ) -> tuple[int, str, str, str]:
        if not source_lines:
            return 0, "", "", ""
        start = max(1, base_line - radius)
        end = min(len(source_lines), base_line + radius)
        candidates: list[tuple[int, str, str, str, int]] = []
        for line_no in range(start, end + 1):
            precode = self._line_text(source_lines, line_no)
            if not precode:
                continue
            aftercode, rule = self._reconstruct_source_mutation(precode, item, occurrence)
            if aftercode and aftercode != precode:
                candidates.append((line_no, precode, aftercode, rule, abs(line_no - base_line)))
        if not candidates:
            return 0, "", "", ""
        candidates.sort(key=lambda item: (item[4], item[0]))
        best = candidates[0]
        return best[0], best[1], best[2], best[3]

    def _reconstruct_switch_mutation(
        self,
        source_lines: list[str],
        job: GeneratorJob,
        item: dict,
    ) -> tuple[int, str, str, str]:
        rule = item.get("rule", "")
        if not (rule.startswith("Remove Switch Mutator") or rule == "Switch"):
            return 0, "", "", ""

        if not source_lines or job.method_end < job.method_start:
            return 0, "", "", ""

        method_lines = [
            (line_no, self._line_text(source_lines, line_no))
            for line_no in range(job.method_start, min(job.method_end, len(source_lines)) + 1)
        ]
        method_lines = [(line_no, text) for line_no, text in method_lines if text]
        if not method_lines:
            return 0, "", "", ""

        description = (item.get("description", "") or "").strip()
        if rule.startswith("Remove Switch Mutator"):
            case_value = self._parse_remove_switch_case_value(description)
            if case_value is None:
                return 0, "", "", ""
            case_line_no, case_line = self._find_case_line(method_lines, case_value)
            if not case_line:
                return 0, "", "", ""
            replacement = self._replacement_case_literal(case_value, method_lines)
            aftercode = self._replace_case_literal(case_line, replacement)
            if not aftercode or aftercode == case_line:
                return 0, "", "", ""
            return (
                case_line_no,
                case_line,
                aftercode,
                self._rule_with_diff(rule, case_line, aftercode),
            )

        switch_line_no, switch_line = self._find_switch_line(method_lines)
        first_case_line_no, first_case_line = self._find_first_case_line(method_lines)
        if not switch_line or not first_case_line:
            return 0, "", "", ""

        first_literal = self._extract_case_literal(first_case_line)
        if not first_literal:
            return 0, "", "", ""
        aftercode = re.sub(r"\bswitch\s*\([^)]*\)", f"switch ({first_literal})", switch_line, count=1)
        if not aftercode or aftercode == switch_line:
            return 0, "", "", ""
        return (
            switch_line_no,
            switch_line,
            aftercode,
            self._rule_with_diff("Switch Mutator", switch_line, aftercode),
        )

    def _safe_name(self, text: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", text)

    def _pick_candidate(self, candidates: list[str], occurrence: int) -> str:
        unique = [c for c in candidates if c and c.strip()]
        if not unique:
            return ""
        idx = occurrence if occurrence < len(unique) else len(unique) - 1
        return unique[idx]

    def _rule_with_diff(self, label: str, before: str, after: str) -> str:
        if not after or after == before:
            return label
        before_tokens = self._tokenize_symbols(before)
        after_tokens = self._tokenize_symbols(after)
        for b, a in zip(before_tokens, after_tokens):
            if b != a:
                return f"{label} ({b} → {a})"
        return label

    def _tokenize_symbols(self, text: str) -> list[str]:
        return re.findall(r"==|!=|>=|<=|&&|\|\||[+\-*/%<>]|\w+|'.'|\"[^\"]*\"", text)

    def _conditionals_boundary_candidates(self, line: str) -> list[str]:
        matches = list(re.finditer(r"(?<![<>=!])(?:>=|<=|>|<)(?![<>=])", line))
        swap = {">": ">=", "<": "<=", ">=": ">", "<=": "<"}
        out: list[str] = []
        for m in matches:
            old = m.group(0)
            new = swap.get(old)
            if not new:
                continue
            out.append(line[:m.start()] + new + line[m.end():])
        return out

    def _math_candidates(self, line: str, description: str) -> list[str]:
        targets = []
        if "addition with subtraction" in description.lower():
            targets.append(("+", "-"))
        if "subtraction with addition" in description.lower():
            targets.append(("-", "+"))
        out: list[str] = []
        for old, new in targets:
            for start, end in self._binary_operator_spans(line, old):
                out.append(line[:start] + new + line[end:])
        return out

    def _binary_operator_spans(self, line: str, operator: str) -> list[tuple[int, int]]:
        spans: list[tuple[int, int]] = []
        in_single = False
        in_double = False
        for i, ch in enumerate(line):
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            if in_single or in_double or ch != operator:
                continue
            prev = line[i - 1] if i > 0 else ""
            nxt = line[i + 1] if i + 1 < len(line) else ""
            if operator == "+" and nxt == operator:
                continue
            if operator == "-" and nxt == operator:
                continue
            if prev in "([=,+-*/%&|!?:<" or prev == "":
                continue
            spans.append((i, i + 1))
        return spans

    def _extract_condition(self, line: str) -> tuple[int, int, str]:
        head = re.search(r"\b(if|while)\s*\(", line)
        if not head:
            return -1, -1, ""
        start = head.end() - 1
        depth = 0
        for idx in range(start, len(line)):
            if line[idx] == "(":
                depth += 1
            elif line[idx] == ")":
                depth -= 1
                if depth == 0:
                    return start + 1, idx, line[start + 1:idx]
        return -1, -1, ""

    def _top_level_condition_parts(self, cond: str) -> list[tuple[int, int]]:
        parts: list[tuple[int, int]] = []
        depth = 0
        start = 0
        i = 0
        while i < len(cond):
            ch = cond[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif depth == 0 and cond.startswith("&&", i):
                parts.append((start, i))
                start = i + 2
                i += 1
            elif depth == 0 and cond.startswith("||", i):
                parts.append((start, i))
                start = i + 2
                i += 1
            i += 1
        parts.append((start, len(cond)))
        return parts

    def _negate_condition_atom(self, atom: str) -> str:
        text = atom.strip()
        ops = [("==", "!="), ("!=", "=="), (">=", "<"), ("<=", ">"), (">", "<="), ("<", ">=")]
        for old, new in ops:
            m = re.search(rf"(?<![<>=!]){re.escape(old)}(?![<>=])", text)
            if m:
                return text[:m.start()] + new + text[m.end():]
        if text.startswith("!"):
            return text[1:].strip()
        return f"!({text})"

    def _negate_conditionals_candidates(self, line: str) -> list[str]:
        cond_start, cond_end, cond = self._extract_condition(line)
        if not cond:
            return []
        out: list[str] = []
        for a, b in self._top_level_condition_parts(cond):
            atom = cond[a:b]
            neg = self._negate_condition_atom(atom)
            out.append(line[:cond_start] + cond[:a] + neg + cond[b:] + line[cond_end:])
        if not out:
            out.append(line[:cond_start] + self._negate_condition_atom(cond) + line[cond_end:])
        return out

    def _remove_conditional_candidates(self, line: str, const: str) -> list[str]:
        cond_start, cond_end, cond = self._extract_condition(line)
        if not cond:
            return []
        parts = self._top_level_condition_parts(cond)
        out: list[str] = []
        if len(parts) <= 1:
            out.append(line[:cond_start] + const + line[cond_end:])
            return out
        for a, b in parts:
            out.append(line[:cond_start] + cond[:a] + const + cond[b:] + line[cond_end:])
        return out

    def _null_return_candidate(self, line: str) -> str:
        m = re.match(r"(\s*return\s+).+?(\s*;.*)$", line)
        if not m:
            return ""
        return f"{m.group(1)}null{m.group(2)}"

    def _inline_constant_candidates(self, line: str, description: str) -> list[str]:
        m = re.search(r"Substituted\s+(.+?)\s+with\s+(.+)$", description)
        if not m:
            return []
        old = m.group(1).strip()
        new = m.group(2).strip()
        pattern = re.compile(rf"(?<![\w.]){re.escape(old)}(?![\w.])")
        matches = list(pattern.finditer(line))
        return [line[:mm.start()] + new + line[mm.end():] for mm in matches]

    def _increment_candidates(self, line: str) -> list[str]:
        out: list[str] = []
        for m in re.finditer(r"\+\s*1\b", line):
            out.append(line[:m.start()] + "- 1" + line[m.end():])
        for m in re.finditer(r"-\s*1\b", line):
            out.append(line[:m.start()] + "+ 1" + line[m.end():])
        return out

    def _remove_increment_candidates(self, line: str) -> list[str]:
        out: list[str] = []
        for m in re.finditer(r"\s*[+-]\s*1\b", line):
            out.append(line[:m.start()] + line[m.end():])
        return out

    def _method_call_candidates(self, line: str, description: str, mode: str) -> list[str]:
        method = description.split("::")[-1].strip()
        if not method:
            return []
        method = method.split()[0]
        spans = self._find_call_spans(line, method)
        out: list[str] = []
        for start, end, receiver, args in spans:
            replacement = ""
            if mode == "receiver":
                replacement = receiver or ""
            elif mode == "argument":
                replacement = args[0].strip() if args else (receiver or "")
            else:
                replacement = self._default_call_replacement(method, receiver)
            if replacement is None:
                continue
            out.append(line[:start] + replacement + line[end:])
        return out

    def _find_call_spans(self, line: str, method: str) -> list[tuple[int, int, str, list[str]]]:
        spans: list[tuple[int, int, str, list[str]]] = []
        token = f"{method}("
        i = 0
        while True:
            idx = line.find(token, i)
            if idx < 0:
                break
            open_idx = idx + len(method)
            end = self._find_matching_paren(line, open_idx)
            if end < 0:
                break
            start = idx
            receiver = ""
            if idx > 0 and line[idx - 1] == '.':
                start = idx - 1
                j = start - 1
                while j >= 0 and line[j] not in " =([{,+-*/%!&|?:;":
                    j -= 1
                receiver = line[j + 1:start]
                start = j + 1
            args = self._split_args(line[open_idx + 1:end])
            spans.append((start, end + 1, receiver.strip(), args))
            i = end + 1
        return spans

    def _find_matching_paren(self, text: str, open_idx: int) -> int:
        depth = 0
        for idx in range(open_idx, len(text)):
            if text[idx] == '(':
                depth += 1
            elif text[idx] == ')':
                depth -= 1
                if depth == 0:
                    return idx
        return -1

    def _split_args(self, text: str) -> list[str]:
        parts: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(text):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == ',' and depth == 0:
                parts.append(text[start:i].strip())
                start = i + 1
        tail = text[start:].strip()
        return parts + ([tail] if tail else [])

    def _default_call_replacement(self, method: str, receiver: str) -> str | None:
        boolean_methods = {"startsWith", "equals", "isEmpty", "isBlank", "isDigits", "isInfinite", "isAllZeros", "isDigit"}
        int_methods = {"indexOf", "length", "compareTo"}
        float_methods = {"doubleValue", "floatValue"}
        char_methods = {"charAt"}
        object_methods = {"createBigDecimal", "createBigInteger", "createDouble", "createFloat", "createInteger", "createLong", "getMantissa", "toString", "valueOf"}
        if method in boolean_methods:
            return "false"
        if method in int_methods:
            return "0"
        if method in float_methods:
            return "0.0"
        if method in char_methods:
            return "'\\0'"
        if method == "append":
            return receiver or "null"
        if method in object_methods:
            return "null"
        return "null"

    def _constructor_call_candidates(self, line: str, description: str) -> list[str]:
        if "NumberFormatException::<init>" in description:
            return [re.sub(r"new\s+NumberFormatException\([^)]*\)", "new NumberFormatException()", line)]
        if "StringBuilder::<init>" in description:
            return [re.sub(r"new\s+StringBuilder\(\)", 'new StringBuilder("")', line)]
        return []

    def _parse_remove_switch_case_value(self, description: str) -> int | None:
        match = re.search(r"case value\s+(-?\d+)", description)
        if not match:
            return None
        return int(match.group(1))

    def _find_case_line(self, method_lines: list[tuple[int, str]], case_value: int) -> tuple[int, str]:
        literals = self._case_value_literals(case_value)
        for literal in literals:
            pattern = re.compile(rf"\bcase\s+{re.escape(literal)}\s*:")
            for line_no, text in method_lines:
                if pattern.search(text):
                    return line_no, text
        return 0, ""

    def _find_switch_line(self, method_lines: list[tuple[int, str]]) -> tuple[int, str]:
        for line_no, text in method_lines:
            if re.search(r"\bswitch\s*\(", text):
                return line_no, text
        return 0, ""

    def _find_first_case_line(self, method_lines: list[tuple[int, str]]) -> tuple[int, str]:
        for line_no, text in method_lines:
            if re.search(r"\bcase\s+.+\s*:", text):
                return line_no, text
        return 0, ""

    def _extract_case_literal(self, line: str) -> str:
        match = re.search(r"\bcase\s+(.+?)\s*:", line)
        return (match.group(1).strip() if match else "")

    def _replacement_case_literal(self, case_value: int, method_lines: list[tuple[int, str]]) -> str:
        used_literals = {self._extract_case_literal(text) for _, text in method_lines}
        if 0 <= case_value <= 0x10FFFF:
            for candidate in ("'_'", "'~'", "'\\0'", "'\\uFFFF'"):
                if candidate not in used_literals:
                    return candidate
        for candidate in ("-999999", "999999"):
            if candidate not in used_literals:
                return candidate
        return "-999999"

    def _replace_case_literal(self, line: str, replacement: str) -> str:
        return re.sub(r"(\bcase\s+)(.+?)(\s*:)", rf"\1{replacement}\3", line, count=1)

    def _case_value_literals(self, case_value: int) -> list[str]:
        literals = [str(case_value)]
        if 32 <= case_value <= 126:
            char = chr(case_value)
            escaped = {
                "\\": r"\\",
                "'": r"\'",
                "\n": r"\n",
                "\r": r"\r",
                "\t": r"\t",
                "\0": r"\0",
            }.get(char, char)
            literals.insert(0, f"'{escaped}'")
        return literals

    def _source_lines(self, container_path: str, filepath: str) -> list[str]:
        cache_key = (container_path, filepath)
        cached = self._source_cache.get(cache_key)
        if cached is not None:
            return cached

        src_raw, _, _ = self.d4j.exec(f"cat {container_path}/{filepath} 2>/dev/null")
        lines = src_raw.splitlines() if src_raw else []
        self._source_cache[cache_key] = lines
        return lines

    def _line_text(self, source_lines: list[str], line_no: int) -> str:
        if 1 <= line_no <= len(source_lines):
            return source_lines[line_no - 1].rstrip("\r\n").strip()
        return ""

    def _nearest_code_line(self, source_lines: list[str], line_no: int, radius: int = 3) -> tuple[int, str]:
        if not source_lines:
            return 0, ""
        if line_no < 1:
            line_no = 1
        if line_no > len(source_lines):
            line_no = len(source_lines)

        def clean(idx: int) -> str:
            text = source_lines[idx - 1].rstrip("\r\n").strip()
            if not text:
                return ""
            if text in {"{", "}", "};", ")", "};"}:
                return ""
            if text.startswith(("//", "/*", "*", "*/")):
                return ""
            return text

        direct = clean(line_no)
        if direct:
            return line_no, direct

        for dist in range(1, radius + 1):
            for candidate in (line_no - dist, line_no + dist):
                if 1 <= candidate <= len(source_lines):
                    text = clean(candidate)
                    if text:
                        return candidate, text
        return 0, ""

    def _classpath(self, container_path: str) -> str:
        cached = self._classpath_cache.get(container_path)
        if cached is not None:
            return cached
        lines = self.d4j.export(container_path, "cp.test")
        cp = next((l for l in reversed(lines) if ":" in l), "")
        if not cp:
            raise RuntimeError(f"empty cp.test for {container_path}")
        self._classpath_cache[container_path] = cp
        return cp

    def _source_dir(self, container_path: str) -> str:
        cached = self._src_dir_cache.get(container_path)
        if cached is not None:
            return cached
        lines = self.d4j.export(container_path, "dir.src.classes")
        rel = (lines[-1] if lines else "src/main/java").strip()
        abs_dir = rel if rel.startswith("/") else f"{container_path}/{rel}"
        self._src_dir_cache[container_path] = abs_dir
        return abs_dir

    def _resolve_target_tests(self, job: GeneratorJob) -> str:
        if self.config.target_tests:
            return self.config.target_tests

        cache_key = job.container_path
        cached = self._tests_cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            lines = self.d4j.export(job.container_path, "tests.relevant")
            tests = [
                l for l in lines
                if l and "." in l and not l.startswith("Running") and not l.startswith("/")
            ]
            if tests:
                result = ",".join(tests)
                self._tests_cache[cache_key] = result
                return result
        except RuntimeError:
            pass

        pkg = ".".join(job.class_fqn.split(".")[:3])
        result = f"{pkg}.*"
        self._tests_cache[cache_key] = result
        return result

    def _build_cli_cmd(
        self,
        class_fqn: str,
        classpath: str,
        src_dir: str,
        report_dir: str,
        target_tests: str,
    ) -> str:
        return (
            f'java -cp "\\${{PIT_CLI_CP}}:{classpath}"'
            f" {_PIT_MAIN}"
            f' --reportDir "{report_dir}"'
            f' --targetClasses "{class_fqn}"'
            f' --targetTests "{target_tests}"'
            f' --sourceDirs "{src_dir}"'
            f" --outputFormats XML"
            f" --timestampedReports false"
            f' --mutators "{self.config.mutators}"'
            f" --skipFailingTests true"
            f" --failWhenNoMutations false"
            f" --verbose false"
        )

    def _raw_entries(self, container_path: str, class_fqn: str) -> list[dict]:
        cache_key = (container_path, class_fqn)
        cached = self._entry_cache.get(cache_key)
        if cached is not None:
            return cached

        report_dir = f"{container_path}/target/pit-reports"
        xml_raw, _, xml_rc = self.d4j.exec(f"cat {report_dir}/mutations.xml 2>/dev/null")
        if xml_rc != 0 or not xml_raw.strip():
            self._entry_cache[cache_key] = []
            return []

        entries = parse_mutation_entries(xml_raw)
        self._entry_cache[cache_key] = entries
        return entries

    def _method_line_maps(self, container_path: str, class_fqn: str) -> dict[str, dict[int, int]]:
        cache_key = (container_path, class_fqn)
        cached = self._line_map_cache.get(cache_key)
        if cached is not None:
            return cached

        javap_text = self._javap_output(container_path, class_fqn)
        maps = self._parse_javap_index_line_maps(javap_text)
        self._line_map_cache[cache_key] = maps
        return maps

    def _javap_output(self, container_path: str, class_fqn: str) -> str:
        cache_key = (container_path, class_fqn)
        cached = self._javap_cache.get(cache_key)
        if cached is not None:
            return cached

        classpath = self._classpath(container_path)
        bin_dir = classpath.split(":", 1)[0]
        out, err, rc = self.d4j.exec(
            f"javap -classpath {bin_dir} -c -l {class_fqn}",
            timeout=60,
        )
        if rc != 0:
            raise RuntimeError(f"javap failed for {class_fqn}: {(err or out).strip()[:300]}")
        self._javap_cache[cache_key] = out
        return out

    def _map_index_to_source_line(
        self,
        method_name: str,
        index: int,
        fallback_line: int,
        line_maps: dict[str, dict[int, int]],
    ) -> int:
        idx_map = line_maps.get(method_name, {})
        if index < 0 or not idx_map:
            return fallback_line
        return idx_map.get(index, fallback_line)

    @staticmethod
    def _parse_javap_index_line_maps(javap_text: str) -> dict[str, dict[int, int]]:
        result: dict[str, dict[int, int]] = {}

        current_method: str | None = None
        in_code = False
        in_lines = False
        ins_offsets: list[int] = []
        line_entries: list[tuple[int, int]] = []

        def finalize() -> None:
            nonlocal current_method, ins_offsets, line_entries
            if current_method and ins_offsets and line_entries:
                ordered_lines = sorted(line_entries)
                idx_map: dict[int, int] = {}
                pos = 0
                current_line = ordered_lines[0][1]
                for idx, offset in enumerate(ins_offsets):
                    while pos + 1 < len(ordered_lines) and ordered_lines[pos + 1][0] <= offset:
                        pos += 1
                        current_line = ordered_lines[pos][1]
                    idx_map.setdefault(idx, current_line)
                    idx_map[offset] = current_line
                result[current_method] = idx_map
            ins_offsets = []
            line_entries = []

        for raw in javap_text.splitlines():
            line = raw.rstrip()
            method_match = re.match(
                r"\s*(?:public|protected|private).*?\s+(\w+)\([^)]*\)(?:\s+throws\s+.*)?;\s*$",
                line,
            )
            if method_match:
                finalize()
                current_method = method_match.group(1)
                in_code = False
                in_lines = False
                continue

            if current_method is None:
                continue

            if line.strip() == "Code:":
                in_code = True
                in_lines = False
                continue

            if line.strip() == "LineNumberTable:":
                in_code = False
                in_lines = True
                continue

            if in_code:
                m = re.match(r"\s*(\d+):", line)
                if m:
                    ins_offsets.append(int(m.group(1)))
                continue

            if in_lines:
                m = re.match(r"\s*line\s+(\d+):\s+(\d+)", line)
                if m:
                    line_entries.append((int(m.group(2)), int(m.group(1))))
                    continue
                if line.strip().startswith("LocalVariableTable:"):
                    finalize()
                    current_method = None
                    in_code = False
                    in_lines = False
                    continue

        finalize()
        return result


    def _clean_compile_cmd(self, container_path: str) -> str:
        return (
            f"cd {container_path} && "
            f"git reset --hard -q >/dev/null 2>&1 || true && "
            f"rm -rf target/pit-reports target/pit-reports-* && "
            f"defects4j compile 2>&1"
        )
