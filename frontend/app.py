import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from PIL import Image, ImageTk

from backend.automata import (
    DFA,
    NFA,
    format_dfa,
    format_minimization_mapping,
    format_nfa,
    format_simulation,
    generate_graphviz_image,
)
from backend.errors import ValidationError
from backend.grammar import RegularGrammar, format_regular_grammar
from backend.parsers import parse_nfa, parse_regular_grammar, parse_word


class TheoryApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Sistema de Teoria da Computacao")
        self.geometry("1080x760")
        self.minsize(980, 680)

        self.current_nfa: Optional[NFA] = None
        self.current_dfa: Optional[DFA] = None
        self.current_minimized_dfa: Optional[DFA] = None
        self.current_grammar: Optional[RegularGrammar] = None
        self._photo_image: Optional[ImageTk.PhotoImage] = None
        self._display_image: Optional[Image.Image] = None

        self._configure_style()
        self._build_interface()
        self._load_examples()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.configure("TButton", padding=(10, 6))
        style.configure("TLabel", padding=(2, 2))
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))

    def _build_interface(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        notebook = ttk.Notebook(main_pane)
        self.automata_tab = ttk.Frame(notebook)
        self.grammar_tab = ttk.Frame(notebook)
        notebook.add(self.automata_tab, text="AFN / AFD")
        notebook.add(self.grammar_tab, text="Gramatica Regular")
        main_pane.add(notebook, weight=3)

        right_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=5)

        output_frame = ttk.LabelFrame(right_pane, text="Resultado")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.output_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        right_pane.add(output_frame, weight=2)

        image_frame = ttk.LabelFrame(right_pane, text="Diagrama do Automato")
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(0, weight=1)
        self._image_canvas = tk.Canvas(image_frame, background="#f8f8f8", highlightthickness=0)
        self._image_canvas.grid(row=0, column=0, sticky="nsew")
        self._img_scroll_x = ttk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=self._image_canvas.xview)
        self._img_scroll_y = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self._image_canvas.yview)
        self._image_canvas.configure(
            xscrollcommand=self._img_scroll_x.set,
            yscrollcommand=self._img_scroll_y.set,
        )
        self._img_scroll_x.grid(row=1, column=0, sticky="ew")
        self._img_scroll_y.grid(row=0, column=1, sticky="ns")
        self._canvas_image_id = None
        save_image_frame = ttk.Frame(image_frame)
        save_image_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(
            save_image_frame,
            text="Salvar Imagem",
            command=self.save_automaton_image,
        ).pack(side=tk.LEFT)
        right_pane.add(image_frame, weight=3)

        self._build_automata_tab()
        self._build_grammar_tab()

    def _build_automata_tab(self) -> None:
        tab = self.automata_tab
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(2, weight=1)

        ttk.Label(tab, text="Estados").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.states_entry = ttk.Entry(tab)
        self.states_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(tab, text="Alfabeto").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.alphabet_entry = ttk.Entry(tab)
        self.alphabet_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=4)

        transitions_frame = ttk.LabelFrame(tab, text="Transicoes do AFN")
        transitions_frame.columnconfigure(0, weight=1)
        transitions_frame.rowconfigure(0, weight=1)
        transitions_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)
        self.transitions_text = scrolledtext.ScrolledText(
            transitions_frame, height=12, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.transitions_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        ttk.Label(tab, text="Estado inicial").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.initial_entry = ttk.Entry(tab)
        self.initial_entry.grid(row=3, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(tab, text="Estados finais").grid(row=4, column=0, sticky="w", padx=8, pady=4)
        self.final_entry = ttk.Entry(tab)
        self.final_entry.grid(row=4, column=1, sticky="ew", padx=8, pady=4)

        word_frame = ttk.LabelFrame(tab, text="Simulacao")
        word_frame.columnconfigure(1, weight=1)
        word_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        ttk.Label(word_frame, text="Palavra").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.word_entry = ttk.Entry(word_frame)
        self.word_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        buttons = ttk.Frame(tab)
        buttons.grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        buttons.columnconfigure((0, 1, 2, 3), weight=1)

        ttk.Button(
            buttons,
            text="Converter AFN -> AFD",
            command=self.convert_nfa_to_dfa,
        ).grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        ttk.Button(
            buttons,
            text="Simular palavra",
            command=self.simulate_word,
        ).grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        ttk.Button(
            buttons,
            text="Minimizar AFD",
            command=self.minimize_dfa,
        ).grid(row=0, column=2, sticky="ew", padx=3, pady=3)
        ttk.Button(
            buttons,
            text="AFD -> GR",
            command=self.generate_grammar_from_current_dfa,
        ).grid(row=0, column=3, sticky="ew", padx=3, pady=3)

    def _build_grammar_tab(self) -> None:
        tab = self.grammar_tab
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(3, weight=1)

        ttk.Label(tab, text="Nao-terminais").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.nonterminals_entry = ttk.Entry(tab)
        self.nonterminals_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(tab, text="Terminais").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.terminals_entry = ttk.Entry(tab)
        self.terminals_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(tab, text="Inicial").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.grammar_start_entry = ttk.Entry(tab)
        self.grammar_start_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=4)

        productions_frame = ttk.LabelFrame(tab, text="Producoes")
        productions_frame.columnconfigure(0, weight=1)
        productions_frame.rowconfigure(0, weight=1)
        productions_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)
        self.productions_text = scrolledtext.ScrolledText(
            productions_frame, height=14, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.productions_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        buttons = ttk.Frame(tab)
        buttons.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        buttons.columnconfigure((0, 1), weight=1)

        ttk.Button(
            buttons,
            text="Converter GR -> AF",
            command=self.convert_grammar_to_automata,
        ).grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        ttk.Button(
            buttons,
            text="Gerar GR do AFD atual",
            command=self.generate_grammar_from_current_dfa,
        ).grid(row=0, column=1, sticky="ew", padx=3, pady=3)

    def _load_examples(self) -> None:
        self.states_entry.insert(0, "q0, q1, q2")
        self.alphabet_entry.insert(0, "a, b")
        self.transitions_text.insert(
            "1.0",
            "\n".join(
                [
                    "q0,epsilon -> q1,q2",
                    "q1,a -> q1",
                    "q1,b -> q2",
                    "q2,b -> q2",
                ]
            ),
        )
        self.initial_entry.insert(0, "q0")
        self.final_entry.insert(0, "q2")
        self.word_entry.insert(0, "ab")

        self.nonterminals_entry.insert(0, "S, A")
        self.terminals_entry.insert(0, "a, b")
        self.grammar_start_entry.insert(0, "S")
        self.productions_text.insert(
            "1.0",
            "\n".join(
                [
                    "S -> a S | b A | epsilon",
                    "A -> a S | b",
                ]
            ),
        )

        self._write_output(
            "Sistema pronto.\n\n"
            "Formatos principais:\n"
            "  Transicao: q0,a -> q1,q2\n"
            "  Epsilon: epsilon, eps ou lambda\n"
            "  Producao: S -> a A | b | epsilon\n"
            "  Palavra com simbolos longos: use espacos, exemplo id + id"
        )

    def _read_transitions(self) -> str:
        return self.transitions_text.get("1.0", tk.END)

    def _read_productions(self) -> str:
        return self.productions_text.get("1.0", tk.END)

    def _write_output(self, text: str) -> None:
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.configure(state=tk.NORMAL)

    def _update_automaton_image(self, automata_list, filename: str = "automaton") -> None:

        try:
            # Normalizar entrada: aceitar um unico automato ou lista de tuplas
            if not isinstance(automata_list, list):
                automata_list = [(automata_list, filename, "")]

            images = []
            for automaton, fname, title in automata_list:
                path = generate_graphviz_image(automaton, filename=fname, title=title)
                images.append(Image.open(path))

            # Combinar imagens verticalmente com margem entre elas
            margin = 20
            total_width = max(img.width for img in images)
            total_height = sum(img.height for img in images) + margin * (len(images) - 1)

            combined = Image.new("RGB", (total_width, total_height), color=(248, 248, 248))
            y_offset = 0
            for img in images:
                combined.paste(img, (0, y_offset))
                y_offset += img.height + margin

            # Reduz a imagem mantendo boa qualidade
            scale = 0.7

            combined = combined.resize(
                (
                    int(combined.width * scale),
                    int(combined.height * scale)
                ),
                Image.Resampling.LANCZOS
)

            self._display_image = combined.copy()
            self._photo_image = ImageTk.PhotoImage(combined)
            self._image_canvas.delete("all")
            self._canvas_image_id = self._image_canvas.create_image(
                0, 0, anchor="nw", image=self._photo_image
            )
            self._image_canvas.configure(
                scrollregion=(0, 0, combined.width, combined.height)
            )
        except Exception as exc:
            self._display_image = None
            self._image_canvas.delete("all")
            self._image_canvas.create_text(
                10, 10, anchor="nw", text=f"Erro ao gerar imagem:\n{exc}",
                fill="red", font=("Consolas", 9)
            )

    def save_automaton_image(self) -> None:
        if self._display_image is None:
            messagebox.showwarning(
                "Sem imagem",
                "Nenhum diagrama disponivel para salvar.\n"
                "Gere um automato antes de salvar a imagem.",
            )
            return

        file_path = filedialog.asksaveasfilename(
            title="Salvar imagem do automato",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Todos os arquivos", "*.*")],
        )
        if not file_path:
            return

        try:
            self._display_image.save(file_path, format="PNG")
            messagebox.showinfo("Sucesso", f"Imagem salva em:\n{file_path}")
        except OSError as exc:
            messagebox.showerror("Erro ao salvar", f"Nao foi possivel salvar a imagem:\n{exc}")

    def _show_error(self, error: Exception) -> None:
        messagebox.showerror("Entrada invalida", str(error))
        self._write_output("Erro:\n" + str(error))

    def _ensure_current_dfa(self) -> DFA:
        if self.current_dfa is None:
            self.convert_nfa_to_dfa(show_success=False)
        if self.current_dfa is None:
            raise ValidationError("Nenhum AFD disponivel.")
        return self.current_dfa

    def convert_nfa_to_dfa(self, show_success: bool = True) -> None:
        try:
            nfa = parse_nfa(
                states_text=self.states_entry.get(),
                alphabet_text=self.alphabet_entry.get(),
                transitions_text=self._read_transitions(),
                initial_text=self.initial_entry.get(),
                final_text=self.final_entry.get(),
            )
            dfa = nfa.to_dfa()
            self.current_nfa = nfa
            self.current_dfa = dfa
            self.current_minimized_dfa = None

            output = format_nfa(nfa) + "\n\n" + format_dfa(dfa, "AFD equivalente")
            self._write_output(output)
            self._update_automaton_image([
                (nfa, "afn", "AFN"),
                (dfa, "afd", "AFD equivalente"),
            ])
            if show_success:
                messagebox.showinfo("Conversao concluida", "AFN convertido para AFD.")
        except ValidationError as error:
            self._show_error(error)

    def simulate_word(self) -> None:
        try:
            dfa = self._ensure_current_dfa()
            word = parse_word(self.word_entry.get(), dfa.alphabet)
            result = dfa.simulate(word)
            self._write_output(format_dfa(dfa, "AFD usado na simulacao") + "\n\n" + format_simulation(result))
        except ValidationError as error:
            self._show_error(error)

    def minimize_dfa(self) -> None:
        try:
            dfa = self._ensure_current_dfa()
            minimized, mapping = dfa.minimize()
            self.current_minimized_dfa = minimized
            self.current_dfa = minimized
            self._write_output(
                format_minimization_mapping(mapping)
                + "\n\n"
                + format_dfa(minimized, "AFD minimizado")
            )
            self._update_automaton_image([
                (dfa, "afd_antes", "AFD antes da minimizacao"),
                (minimized, "afd_minimizado", "AFD minimizado"),
            ])
            messagebox.showinfo("Minimizacao concluida", "AFD minimizado com sucesso.")
        except ValidationError as error:
            self._show_error(error)

    def convert_grammar_to_automata(self) -> None:
        try:
            grammar = parse_regular_grammar(
                nonterminals_text=self.nonterminals_entry.get(),
                terminals_text=self.terminals_entry.get(),
                start_text=self.grammar_start_entry.get(),
                productions_text=self._read_productions(),
            )
            nfa = grammar.to_nfa()
            dfa = nfa.to_dfa()
            self.current_grammar = grammar
            self.current_nfa = nfa
            self.current_dfa = dfa
            self.current_minimized_dfa = None

            self._write_output(
                format_regular_grammar(grammar)
                + "\n\n"
                + format_nfa(nfa)
                + "\n\n"
                + format_dfa(dfa, "AFD equivalente")
            )
            self._update_automaton_image([
                (nfa, "afn_gr", "AFN (da Gramatica)"),
                (dfa, "afd_gr", "AFD equivalente"),
            ])
            messagebox.showinfo("Conversao concluida", "Gramatica convertida para automato.")
        except ValidationError as error:
            self._show_error(error)

    def generate_grammar_from_current_dfa(self) -> None:
        try:
            dfa = self._ensure_current_dfa()
            grammar = RegularGrammar.from_dfa(dfa)
            self.current_grammar = grammar
            self._fill_grammar_fields(grammar)
            self._write_output(format_dfa(dfa, "AFD de origem") + "\n\n" + format_regular_grammar(grammar))
            messagebox.showinfo("Conversao concluida", "Gramatica regular gerada a partir do AFD.")
        except ValidationError as error:
            self._show_error(error)

    def _fill_grammar_fields(self, grammar: RegularGrammar) -> None:
        self.nonterminals_entry.delete(0, tk.END)
        self.nonterminals_entry.insert(0, ", ".join(sorted(grammar.nonterminals)))

        self.terminals_entry.delete(0, tk.END)
        self.terminals_entry.insert(0, ", ".join(sorted(grammar.terminals)))

        self.grammar_start_entry.delete(0, tk.END)
        self.grammar_start_entry.insert(0, grammar.start_symbol)

        self.productions_text.delete("1.0", tk.END)
        lines = []
        for lhs in sorted(grammar.productions):
            rhs = " | ".join(item.as_text() for item in grammar.productions[lhs])
            lines.append(f"{lhs} -> {rhs}")
        self.productions_text.insert("1.0", "\n".join(lines))


def run_app() -> None:
    app = TheoryApp()
    app.mainloop()
