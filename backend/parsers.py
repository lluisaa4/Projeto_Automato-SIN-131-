from typing import Dict, List, Sequence, Set, Tuple

from .automata import EPSILON, NFA, normalize_symbol
from .errors import ParseError
from .grammar import Production, RegularGrammar


def _split_items(text: str, delimiters: Sequence[str]) -> List[str]:
    items: List[str] = []
    current = []
    delimiter_set = set(delimiters)

    for char in text.replace("\r", "\n"):
        if char in delimiter_set:
            token = "".join(current).strip()
            if token:
                items.append(token)
            current = []
        else:
            current.append(char)

    token = "".join(current).strip()
    if token:
        items.append(token)
    return items


def parse_set(text: str, field_name: str, allow_empty: bool = False) -> Set[str]:
    items = _split_items(text, [",", ";", "\n", "\t", " "])
    if not items and not allow_empty:
        raise ParseError(f"O campo '{field_name}' nao pode ficar vazio.")
    return set(items)


def parse_word(text: str, alphabet: Set[str]) -> List[str]:
    value = text.strip()
    if not value or normalize_symbol(value) == EPSILON:
        return []

    if any(char.isspace() for char in value):
        symbols = value.split()
    elif all(len(symbol) == 1 for symbol in alphabet):
        symbols = list(value)
    elif value in alphabet:
        symbols = [value]
    else:
        raise ParseError(
            "Nao foi possivel separar a palavra em simbolos. "
            "Use espacos entre simbolos quando o alfabeto tiver itens com mais de um caractere."
        )

    invalid = [symbol for symbol in symbols if symbol not in alphabet]
    if invalid:
        raise ParseError("Palavra contem simbolos fora do alfabeto: " + ", ".join(invalid) + ".")
    return symbols


def parse_nfa(
    states_text: str,
    alphabet_text: str,
    transitions_text: str,
    initial_text: str,
    final_text: str,
) -> NFA:
    states = parse_set(states_text, "estados")
    alphabet = parse_set(alphabet_text, "alfabeto", allow_empty=True)
    initial_state = initial_text.strip()
    final_states = parse_set(final_text, "estados finais", allow_empty=True)
    transitions = _parse_transitions(transitions_text)

    nfa = NFA(
        states=states,
        alphabet=alphabet,
        transitions=transitions,
        initial_state=initial_state,
        final_states=final_states,
    )
    nfa.validate()
    return nfa


def _parse_transitions(text: str) -> Dict[Tuple[str, str], Set[str]]:
    transitions: Dict[Tuple[str, str], Set[str]] = {}
    lines = _split_items(text, ["\n", ";"])

    for line in lines:
        if line.strip().startswith("#"):
            continue
        source, symbol, targets = _parse_transition_line(line)
        transitions.setdefault((source, symbol), set()).update(targets)

    return transitions


def _parse_transition_line(line: str) -> Tuple[str, str, Set[str]]:
    separator_index = line.find("->")
    separator_size = 2
    if separator_index < 0:
        separator_index = line.find("=")
        separator_size = 1

    if separator_index >= 0:
        left = line[:separator_index].strip()
        right = line[separator_index + separator_size :].strip()
    else:
        parts = line.split()
        if len(parts) != 3:
            raise ParseError(
                "Transicao invalida. Use o formato: origem,simbolo -> destino1,destino2."
            )
        left = parts[0] + "," + parts[1]
        right = parts[2]

    if "," in left:
        left_parts = [item.strip() for item in left.split(",") if item.strip()]
    elif ":" in left:
        left_parts = [item.strip() for item in left.split(":") if item.strip()]
    else:
        left_parts = left.split()

    if len(left_parts) != 2:
        raise ParseError(
            "Lado esquerdo da transicao invalido. Use origem,simbolo ou origem simbolo."
        )

    source = left_parts[0]
    symbol = normalize_symbol(left_parts[1])
    targets = parse_set(right, "destinos da transicao")
    return source, symbol, targets


def parse_regular_grammar(
    nonterminals_text: str,
    terminals_text: str,
    start_text: str,
    productions_text: str,
) -> RegularGrammar:
    nonterminals = parse_set(nonterminals_text, "nao-terminais")
    terminals = parse_set(terminals_text, "terminais", allow_empty=True)
    start_symbol = start_text.strip()
    productions = _parse_productions(productions_text, terminals, nonterminals)

    grammar = RegularGrammar(
        nonterminals=nonterminals,
        terminals=terminals,
        productions=productions,
        start_symbol=start_symbol,
    )
    grammar.validate()
    return grammar


def _parse_productions(
    text: str, terminals: Set[str], nonterminals: Set[str]
) -> Dict[str, List[Production]]:
    lines = _split_items(text, ["\n", ";"])
    productions: Dict[str, List[Production]] = {}

    for line in lines:
        if line.strip().startswith("#"):
            continue

        arrow_index = line.find("->")
        arrow_size = 2
        if arrow_index < 0:
            arrow_index = line.find("=")
            arrow_size = 1
        if arrow_index < 0:
            raise ParseError("Producao invalida. Use o formato: S -> a A | epsilon.")

        lhs = line[:arrow_index].strip()
        rhs = line[arrow_index + arrow_size :].strip()
        if not lhs or not rhs:
            raise ParseError("Producao com lado esquerdo ou direito vazio.")

        alternatives = [item.strip() for item in rhs.split("|") if item.strip()]
        if not alternatives:
            raise ParseError(f"Producao de {lhs} nao possui alternativas.")

        productions.setdefault(lhs, [])
        for alternative in alternatives:
            productions[lhs].append(_parse_production_rhs(alternative, terminals, nonterminals))

    if not productions:
        raise ParseError("Informe pelo menos uma producao da gramatica.")
    return productions


def _parse_production_rhs(
    text: str, terminals: Set[str], nonterminals: Set[str]
) -> Production:
    if normalize_symbol(text) == EPSILON:
        return Production(None, None)

    tokens = text.split()
    if len(tokens) == 1:
        token = tokens[0]
        if token in terminals:
            return Production(token, None)
        terminal, nonterminal = _split_compact_rhs(token, terminals, nonterminals)
        return Production(terminal, nonterminal)

    if len(tokens) == 2:
        terminal, nonterminal = tokens
        return Production(terminal, nonterminal)

    raise ParseError(
        "Alternativa invalida. Use epsilon, um terminal, ou terminal seguido de nao-terminal."
    )


def _split_compact_rhs(
    text: str, terminals: Set[str], nonterminals: Set[str]
) -> Tuple[str, str]:
    for terminal in sorted(terminals, key=len, reverse=True):
        if text.startswith(terminal):
            suffix = text[len(terminal) :]
            if suffix in nonterminals:
                return terminal, suffix

    raise ParseError(
        "Alternativa compacta invalida: "
        + text
        + ". Use espaco, por exemplo: a A."
    )
