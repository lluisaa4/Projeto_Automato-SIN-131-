# Sistema de Teoria da Computacao

Projeto em Python com interface grafica Tkinter para trabalhar com conceitos
fundamentais de Teoria da Computacao:

- entrada e validacao de AFN;
- conversao AFN -> AFD por construcao de subconjuntos;
- simulacao de aceitacao de palavras no AFD;
- minimizacao de AFD por refinamento de particoes;
- conversao bidirecional entre gramatica regular e automato finito.

O projeto nao usa bibliotecas de terceiros e nao usa modulos prontos para
processamento de linguagens regulares.

## Estrutura

```text
sistema_teoria_computacao/
  main.py
  backend/
    automata.py     # AFN, AFD, determinizacao, simulacao e minimizacao
    grammar.py      # Gramatica regular e conversoes GR <-> AF
    parsers.py      # Parsers textuais manuais, sem expressoes regulares
    errors.py       # Excecoes de validacao e parsing
  frontend/
    app.py          # Interface grafica Tkinter
```

## Requisitos

- Python 3.10 ou superior.
- Tkinter habilitado na instalacao do Python.

No Windows, a instalacao oficial do Python normalmente ja inclui Tkinter.

## Como compilar/verificar

Abra um terminal na pasta do projeto:

```powershell
cd caminhoArquivo
python -m compileall .
```

Esse comando compila os arquivos `.py` para bytecode e aponta erros de sintaxe.

```powershell
cd caminhoArquivo
& 'caminhoArquivo\dependencies\python\python.exe' -m compileall .
```

## Como executar

Na mesma pasta:

```powershell
python main.py
```

A janela abre com exemplos preenchidos. Voce pode substituir os campos e usar os
botoes de conversao, simulacao e minimizacao.

## Formatos aceitos

### AFN

Estados e alfabeto podem ser separados por virgula, espaco, ponto e virgula ou
quebra de linha.

```text
Estados: q0, q1, q2
Alfabeto: a, b
Inicial: q0
Finais: q2
```

Transicoes:

```text
q0,epsilon -> q1,q2
q1,a -> q1
q1,b -> q2
q2,b -> q2
```

Tambem sao aceitos `eps` e `lambda` para epsilon.

### Palavra

Para alfabetos com simbolos de um caractere, a palavra pode ser digitada sem
espacos:

```text
abba
```

Para simbolos com mais de um caractere, separe por espacos:

```text
id + id
```

Palavra vazia pode ser deixada em branco ou escrita como `epsilon`.

### Gramatica regular

```text
Nao-terminais: S, A
Terminais: a, b
Inicial: S

Producoes:
S -> a S | b A | epsilon
A -> a S | b
```

Tambem e aceito o formato compacto quando nao houver ambiguidade:

```text
S -> aS | bA | epsilon
```

## Observacoes de implementacao

- O AFN aceita transicoes epsilon, mas epsilon nunca pertence ao alfabeto.
- A determinizacao cria estados do AFD como subconjuntos dos estados do AFN.
- A minimizacao completa o AFD, remove estados inalcançaveis e aplica
  refinamento de particoes ate estabilizar.
- A conversao AF -> GR usa o AFD atual e gera uma gramatica regular equivalente.
