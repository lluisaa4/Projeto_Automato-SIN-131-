from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from .automata import DFA, NFA
from .errors import ValidationError


@dataclass(frozen=True)
class Production:
    terminal: Optional[str]
    next_nonterminal: Optional[str] = None

    def is_epsilon(self) -> bool:
        return self.terminal is None and self.next_nonterminal is None

    def as_text(self) -> str:
        if self.is_epsilon():
            return "epsilon"
        if self.next_nonterminal is None:
            return str(self.terminal)
        return f"{self.terminal} {self.next_nonterminal}"


@dataclass
class RegularGrammar:
    nonterminals: Set[str]
    terminals: Set[str]
    productions: Dict[str, List[Production]]
    start_symbol: str

    def __post_init__(self) -> None:
        self.nonterminals = {item.strip() for item in self.nonterminals if item.strip()}
        self.terminals = {item.strip() for item in self.terminals if item.strip()}
        self.start_symbol = self.start_symbol.strip()

        normalized: Dict[str, List[Production]] = {}
        for lhs, productions in self.productions.items():
            key = lhs.strip()
            normalized[key] = list(productions)
        self.productions = normalized

    def validate(self) -> None:
        if not self.nonterminals:
            raise ValidationError("A gramatica deve possuir pelo menos um nao-terminal.")
        if self.start_symbol not in self.nonterminals:
            raise ValidationError("O simbolo inicial da gramatica deve ser nao-terminal.")

        for lhs, productions in self.productions.items():
            if lhs not in self.nonterminals:
                raise ValidationError(f"Producao usa nao-terminal inexistente: {lhs}.")
            if not productions:
                raise ValidationError(f"Nao-terminal {lhs} possui lista de producoes vazia.")

            for production in productions:
                if production.is_epsilon():
                    continue
                if production.terminal not in self.terminals:
                    raise ValidationError(
                        f"Producao de {lhs} usa terminal inexistente: {production.terminal}."
                    )
                if (
                    production.next_nonterminal is not None
                    and production.next_nonterminal not in self.nonterminals
                ):
                    raise ValidationError(
                        "Producao de "
                        + lhs
                        + " aponta para nao-terminal inexistente: "
                        + str(production.next_nonterminal)
                        + "."
                    )

    def to_nfa(self) -> NFA:
        self.validate()

        states = set(self.nonterminals)
        final_state = "FINAL_GR"
        counter = 1
        while final_state in states:
            final_state = f"FINAL_GR_{counter}"
            counter += 1
        states.add(final_state)

        final_states = {final_state}
        transitions: Dict[Tuple[str, str], Set[str]] = {}

        for lhs, productions in self.productions.items():
            for production in productions:
                if production.is_epsilon():
                    final_states.add(lhs)
                elif production.next_nonterminal is None:
                    transitions.setdefault((lhs, production.terminal or ""), set()).add(final_state)
                else:
                    transitions.setdefault((lhs, production.terminal or ""), set()).add(
                        production.next_nonterminal
                    )

        nfa = NFA(
            states=states,
            alphabet=set(self.terminals),
            transitions=transitions,
            initial_state=self.start_symbol,
            final_states=final_states,
        )
        nfa.validate()
        return nfa

    @classmethod
    def from_dfa(cls, dfa: DFA) -> "RegularGrammar":
        dfa = dfa.remove_unreachable()
        dfa.validate()

        ordered_states = [dfa.initial_state]
        ordered_states.extend(state for state in sorted(dfa.states) if state != dfa.initial_state)

        state_to_nonterminal: Dict[str, str] = {}
        used_nonterminals: Set[str] = set()
        for index, state in enumerate(ordered_states):
            if index == 0:
                candidate = "S"
            else:
                candidate = f"A{index}"
            while candidate in used_nonterminals:
                candidate = candidate + "_"
            state_to_nonterminal[state] = candidate
            used_nonterminals.add(candidate)

        productions: Dict[str, List[Production]] = {
            nonterminal: [] for nonterminal in state_to_nonterminal.values()
        }

        for state in ordered_states:
            lhs = state_to_nonterminal[state]
            if state in dfa.final_states:
                productions[lhs].append(Production(None, None))

            for symbol in sorted(dfa.alphabet):
                target = dfa.transitions.get((state, symbol))
                if target is None:
                    continue
                target_nonterminal = state_to_nonterminal[target]
                productions[lhs].append(Production(symbol, target_nonterminal))
                if target in dfa.final_states:
                    productions[lhs].append(Production(symbol, None))

        deduplicated: Dict[str, List[Production]] = {}
        for lhs, items in productions.items():
            seen = set()
            deduplicated[lhs] = []
            for production in items:
                key = (production.terminal, production.next_nonterminal)
                if key not in seen:
                    seen.add(key)
                    deduplicated[lhs].append(production)

        grammar = cls(
            nonterminals=set(state_to_nonterminal.values()),
            terminals=set(dfa.alphabet),
            productions=deduplicated,
            start_symbol=state_to_nonterminal[dfa.initial_state],
        )
        grammar.validate()
        return grammar


def format_regular_grammar(grammar: RegularGrammar) -> str:
    lines = [
        "Gramatica Regular",
        f"Nao-terminais: {', '.join(sorted(grammar.nonterminals))}",
        f"Terminais: {', '.join(sorted(grammar.terminals))}",
        f"Inicial: {grammar.start_symbol}",
        "Producoes:",
    ]

    for lhs in sorted(grammar.productions):
        rhs = " | ".join(production.as_text() for production in grammar.productions[lhs])
        lines.append(f"  {lhs} -> {rhs}")

    return "\n".join(lines)
