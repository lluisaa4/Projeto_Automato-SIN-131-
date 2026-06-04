from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

from .errors import ValidationError


EPSILON = ""
EPSILON_ALIASES = {"epsilon", "eps", "lambda"}


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip()
    if value.lower() in EPSILON_ALIASES:
        return EPSILON
    return value


def display_symbol(symbol: str) -> str:
    return "epsilon" if symbol == EPSILON else symbol


def _unique_name(base_name: str, used_names: Set[str]) -> str:
    if base_name not in used_names:
        return base_name
    index = 1
    while True:
        candidate = f"{base_name}_{index}"
        if candidate not in used_names:
            return candidate
        index += 1


def _format_subset(states: FrozenSet[str]) -> str:
    if not states:
        return "{}"
    return "{" + ",".join(sorted(states)) + "}"


@dataclass
class SimulationStep:
    index: int
    source: str
    symbol: str
    target: Optional[str]


@dataclass
class SimulationResult:
    accepted: bool
    path: List[str]
    steps: List[SimulationStep]
    message: str


@dataclass
class NFA:
    states: Set[str]
    alphabet: Set[str]
    transitions: Dict[Tuple[str, str], Set[str]]
    initial_state: str
    final_states: Set[str]

    def __post_init__(self) -> None:
        self.states = {state.strip() for state in self.states if state.strip()}
        self.alphabet = {normalize_symbol(symbol) for symbol in self.alphabet if symbol.strip()}
        self.initial_state = self.initial_state.strip()
        self.final_states = {state.strip() for state in self.final_states if state.strip()}

        normalized_transitions: Dict[Tuple[str, str], Set[str]] = {}
        for (source, symbol), targets in self.transitions.items():
            key = (source.strip(), normalize_symbol(symbol))
            normalized_targets = {target.strip() for target in targets if target.strip()}
            if key in normalized_transitions:
                normalized_transitions[key].update(normalized_targets)
            else:
                normalized_transitions[key] = normalized_targets
        self.transitions = normalized_transitions

    def validate(self) -> None:
        if not self.states:
            raise ValidationError("O AFN deve possuir pelo menos um estado.")
        if EPSILON in self.alphabet:
            raise ValidationError("O simbolo epsilon nao pode fazer parte do alfabeto.")
        if not self.initial_state:
            raise ValidationError("O estado inicial nao pode ficar vazio.")
        if self.initial_state not in self.states:
            raise ValidationError("O estado inicial deve pertencer ao conjunto de estados.")
        if not self.final_states.issubset(self.states):
            invalid = sorted(self.final_states - self.states)
            raise ValidationError(f"Estados finais inexistentes: {', '.join(invalid)}.")

        for (source, symbol), targets in self.transitions.items():
            if source not in self.states:
                raise ValidationError(f"Transicao com estado de origem inexistente: {source}.")
            if symbol != EPSILON and symbol not in self.alphabet:
                raise ValidationError(
                    f"Transicao usa simbolo '{display_symbol(symbol)}' fora do alfabeto."
                )
            if not targets:
                raise ValidationError(f"Transicao {source},{display_symbol(symbol)} sem destino.")
            missing_targets = targets - self.states
            if missing_targets:
                raise ValidationError(
                    "Transicao aponta para estados inexistentes: "
                    + ", ".join(sorted(missing_targets))
                    + "."
                )

    def epsilon_closure(self, source_states: Iterable[str]) -> Set[str]:
        closure = set(source_states)
        stack = list(closure)

        while stack:
            state = stack.pop()
            for target in self.transitions.get((state, EPSILON), set()):
                if target not in closure:
                    closure.add(target)
                    stack.append(target)

        return closure

    def move(self, source_states: Iterable[str], symbol: str) -> Set[str]:
        result: Set[str] = set()
        for state in source_states:
            result.update(self.transitions.get((state, symbol), set()))
        return result

    def to_dfa(self) -> "DFA":
        self.validate()

        alphabet = set(self.alphabet)
        start_subset = frozenset(self.epsilon_closure({self.initial_state}))
        pending_subsets: List[FrozenSet[str]] = [start_subset]
        discovered_subsets: Set[FrozenSet[str]] = {start_subset}

        dfa_states: Set[str] = set()
        dfa_final_states: Set[str] = set()
        dfa_transitions: Dict[Tuple[str, str], str] = {}

        # Construcao por subconjuntos: cada estado do AFD representa um conjunto
        # de estados do AFN alcancaveis apos consumir a mesma palavra.
        while pending_subsets:
            current_subset = pending_subsets.pop(0)
            current_label = _format_subset(current_subset)
            dfa_states.add(current_label)

            if set(current_subset) & self.final_states:
                dfa_final_states.add(current_label)

            for symbol in sorted(alphabet):
                moved_states = self.move(current_subset, symbol)
                next_subset = frozenset(self.epsilon_closure(moved_states))
                next_label = _format_subset(next_subset)
                dfa_transitions[(current_label, symbol)] = next_label

                if next_subset not in discovered_subsets:
                    discovered_subsets.add(next_subset)
                    pending_subsets.append(next_subset)

        dfa = DFA(
            states=dfa_states,
            alphabet=alphabet,
            transitions=dfa_transitions,
            initial_state=_format_subset(start_subset),
            final_states=dfa_final_states,
        )
        dfa.validate()
        return dfa


@dataclass
class DFA:
    states: Set[str]
    alphabet: Set[str]
    transitions: Dict[Tuple[str, str], str]
    initial_state: str
    final_states: Set[str]

    def __post_init__(self) -> None:
        self.states = {state.strip() for state in self.states if state.strip()}
        self.alphabet = {normalize_symbol(symbol) for symbol in self.alphabet if symbol.strip()}
        self.initial_state = self.initial_state.strip()
        self.final_states = {state.strip() for state in self.final_states if state.strip()}

        normalized_transitions: Dict[Tuple[str, str], str] = {}
        for (source, symbol), target in self.transitions.items():
            normalized_transitions[(source.strip(), normalize_symbol(symbol))] = target.strip()
        self.transitions = normalized_transitions

    def validate(self) -> None:
        if not self.states:
            raise ValidationError("O AFD deve possuir pelo menos um estado.")
        if EPSILON in self.alphabet:
            raise ValidationError("O simbolo epsilon nao pode fazer parte do alfabeto do AFD.")
        if self.initial_state not in self.states:
            raise ValidationError("O estado inicial do AFD deve pertencer ao conjunto de estados.")
        if not self.final_states.issubset(self.states):
            invalid = sorted(self.final_states - self.states)
            raise ValidationError(f"Estados finais inexistentes no AFD: {', '.join(invalid)}.")

        for (source, symbol), target in self.transitions.items():
            if source not in self.states:
                raise ValidationError(f"AFD possui origem inexistente: {source}.")
            if symbol not in self.alphabet:
                raise ValidationError(f"AFD usa simbolo fora do alfabeto: {symbol}.")
            if target not in self.states:
                raise ValidationError(f"AFD aponta para destino inexistente: {target}.")

    def transition(self, state: str, symbol: str) -> Optional[str]:
        return self.transitions.get((state, symbol))

    def complete(self) -> "DFA":
        self.validate()
        states = set(self.states)
        transitions = dict(self.transitions)
        trap_state = _unique_name("TRAP", states)
        needs_trap = False

        for state in sorted(states):
            for symbol in sorted(self.alphabet):
                if (state, symbol) not in transitions:
                    transitions[(state, symbol)] = trap_state
                    needs_trap = True

        if needs_trap:
            states.add(trap_state)
            for symbol in sorted(self.alphabet):
                transitions[(trap_state, symbol)] = trap_state

        return DFA(
            states=states,
            alphabet=set(self.alphabet),
            transitions=transitions,
            initial_state=self.initial_state,
            final_states=set(self.final_states),
        )

    def reachable_states(self) -> Set[str]:
        reachable = {self.initial_state}
        stack = [self.initial_state]

        while stack:
            state = stack.pop()
            for symbol in self.alphabet:
                target = self.transitions.get((state, symbol))
                if target is not None and target not in reachable:
                    reachable.add(target)
                    stack.append(target)

        return reachable

    def remove_unreachable(self) -> "DFA":
        reachable = self.reachable_states()
        transitions = {
            key: target
            for key, target in self.transitions.items()
            if key[0] in reachable and target in reachable
        }
        return DFA(
            states=reachable,
            alphabet=set(self.alphabet),
            transitions=transitions,
            initial_state=self.initial_state,
            final_states=self.final_states & reachable,
        )

    def minimize(self) -> Tuple["DFA", Dict[str, Set[str]]]:
        complete_dfa = self.complete().remove_unreachable()

        final_group = set(complete_dfa.final_states)
        non_final_group = complete_dfa.states - complete_dfa.final_states
        partitions: List[Set[str]] = []
        if final_group:
            partitions.append(final_group)
        if non_final_group:
            partitions.append(non_final_group)

        def canonical(groups: List[Set[str]]) -> List[Tuple[str, ...]]:
            return sorted(tuple(sorted(group)) for group in groups)

        # Refinamento de particoes: dois estados continuam no mesmo grupo apenas
        # se, para cada simbolo, transitam para grupos equivalentes.
        while True:
            group_index: Dict[str, int] = {}
            for index, group in enumerate(partitions):
                for state in group:
                    group_index[state] = index

            refined_partitions: List[Set[str]] = []
            for group in partitions:
                buckets: Dict[Tuple[int, ...], Set[str]] = {}
                for state in sorted(group):
                    signature = tuple(
                        group_index[complete_dfa.transitions[(state, symbol)]]
                        for symbol in sorted(complete_dfa.alphabet)
                    )
                    buckets.setdefault(signature, set()).add(state)

                for signature in sorted(buckets):
                    refined_partitions.append(buckets[signature])

            if canonical(refined_partitions) == canonical(partitions):
                partitions = refined_partitions
                break
            partitions = refined_partitions

        initial_group = next(
            group for group in partitions if complete_dfa.initial_state in group
        )
        ordered_groups = [initial_group]
        ordered_groups.extend(
            sorted(
                (group for group in partitions if group is not initial_group),
                key=lambda item: tuple(sorted(item)),
            )
        )

        old_to_new: Dict[str, str] = {}
        mapping: Dict[str, Set[str]] = {}
        for index, group in enumerate(ordered_groups):
            new_state = f"M{index}"
            mapping[new_state] = set(group)
            for state in group:
                old_to_new[state] = new_state

        minimized_transitions: Dict[Tuple[str, str], str] = {}
        minimized_final_states: Set[str] = set()

        for new_state, old_group in mapping.items():
            representative = sorted(old_group)[0]
            if old_group & complete_dfa.final_states:
                minimized_final_states.add(new_state)
            for symbol in sorted(complete_dfa.alphabet):
                target = complete_dfa.transitions[(representative, symbol)]
                minimized_transitions[(new_state, symbol)] = old_to_new[target]

        minimized = DFA(
            states=set(mapping.keys()),
            alphabet=set(complete_dfa.alphabet),
            transitions=minimized_transitions,
            initial_state=old_to_new[complete_dfa.initial_state],
            final_states=minimized_final_states,
        )
        minimized.validate()
        return minimized, mapping

    def simulate(self, word: Sequence[str]) -> SimulationResult:
        self.validate()
        current_state = self.initial_state
        path = [current_state]
        steps: List[SimulationStep] = []

        for index, symbol in enumerate(word, start=1):
            if symbol not in self.alphabet:
                raise ValidationError(f"Simbolo '{symbol}' nao pertence ao alfabeto do AFD.")

            next_state = self.transitions.get((current_state, symbol))
            steps.append(
                SimulationStep(
                    index=index,
                    source=current_state,
                    symbol=symbol,
                    target=next_state,
                )
            )

            if next_state is None:
                return SimulationResult(
                    accepted=False,
                    path=path,
                    steps=steps,
                    message="Palavra rejeitada: transicao ausente no AFD.",
                )

            current_state = next_state
            path.append(current_state)

        accepted = current_state in self.final_states
        return SimulationResult(
            accepted=accepted,
            path=path,
            steps=steps,
            message="Palavra aceita." if accepted else "Palavra rejeitada.",
        )


def format_nfa(nfa: NFA) -> str:
    lines = [
        "AFN",
        f"Estados: {', '.join(sorted(nfa.states))}",
        f"Alfabeto: {', '.join(sorted(nfa.alphabet))}",
        f"Inicial: {nfa.initial_state}",
        f"Finais: {', '.join(sorted(nfa.final_states)) or '(nenhum)'}",
        "Transicoes:",
    ]
    for (source, symbol), targets in sorted(nfa.transitions.items()):
        lines.append(
            f"  {source}, {display_symbol(symbol)} -> {', '.join(sorted(targets))}"
        )
    return "\n".join(lines)


def format_dfa(dfa: DFA, title: str = "AFD") -> str:
    lines = [
        title,
        f"Estados: {', '.join(sorted(dfa.states))}",
        f"Alfabeto: {', '.join(sorted(dfa.alphabet))}",
        f"Inicial: {dfa.initial_state}",
        f"Finais: {', '.join(sorted(dfa.final_states)) or '(nenhum)'}",
        "Transicoes:",
    ]
    for source in sorted(dfa.states):
        for symbol in sorted(dfa.alphabet):
            target = dfa.transitions.get((source, symbol))
            if target is not None:
                lines.append(f"  {source}, {symbol} -> {target}")
    return "\n".join(lines)


def format_minimization_mapping(mapping: Dict[str, Set[str]]) -> str:
    lines = ["Mapeamento da minimizacao:"]
    for new_state in sorted(mapping):
        lines.append(f"  {new_state} = {', '.join(sorted(mapping[new_state]))}")
    return "\n".join(lines)


def format_simulation(result: SimulationResult) -> str:
    lines = ["Simulacao no AFD", result.message, "Caminho: " + " -> ".join(result.path)]
    if result.steps:
        lines.append("Passos:")
        for step in result.steps:
            target = step.target if step.target is not None else "(sem transicao)"
            lines.append(f"  {step.index}. {step.source}, {step.symbol} -> {target}")
    else:
        lines.append("Palavra vazia: nenhum simbolo consumido.")
    return "\n".join(lines)
