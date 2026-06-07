# Sistema de Teoria da Computacao

Projeto em Python com interface grafica Tkinter para trabalhar com conceitos
fundamentais da Teoria da Computacao.

O sistema permite:

- entrada e validacao de AFN;
- conversao AFN -> AFD por construcao de subconjuntos;
- simulacao de aceitacao de palavras no AFD;
- minimizacao de AFD por refinamento de particoes;
- conversao bidirecional entre gramatica regular e automato finito;
- visualizacao grafica dos automatos gerados;
- salvamento dos diagramas dos automatos em imagem PNG.

O projeto nao usa bibliotecas prontas voltadas para processamento de linguagens
regulares. As bibliotecas externas utilizadas sao apenas para visualizacao
grafica dos automatos.

## Estrutura

```text
sistema_teoria_computacao/
  main.py
  backend/
    automata.py     # AFN, AFD, determinizacao, simulacao, minimizacao e imagens Graphviz
    grammar.py      # Gramatica regular e conversoes GR <-> AF
    parsers.py      # Parsers textuais manuais, sem expressoes regulares
    errors.py       # Excecoes de validacao e parsing
  frontend/
    app.py          # Interface grafica Tkinter
  output_graphs/    # Imagens PNG geradas automaticamente pelos automatos
```

## Requisitos

- Python 3.10 ou superior.
- Tkinter habilitado na instalacao do Python.
- Pillow, usado para carregar e exibir imagens na interface.
- Graphviz, usado para gerar os diagramas dos automatos.

No Windows, a instalacao oficial do Python normalmente ja inclui Tkinter.

Para que os diagramas sejam gerados corretamente, tambem e necessario instalar
o Graphviz no sistema operacional e deixar o executavel `dot` disponivel no
`PATH`.

## Instalacao das dependencias

Abra um terminal na pasta do projeto e execute:

```powershell
python -m pip install pillow graphviz
```

Caso o comando `python` nao esteja disponivel, use o executavel Python instalado
na sua maquina.

## Como compilar/verificar

Abra um terminal na pasta do projeto:

```powershell
cd caminhoArquivo
python -m compileall .
```

Esse comando compila os arquivos `.py` para bytecode e aponta erros de sintaxe.

## Como executar

Na mesma pasta:

```powershell
python main.py
```

A janela abre com exemplos preenchidos. Voce pode substituir os campos e usar os
botoes de conversao, simulacao, minimizacao, conversao entre AF e GR e geracao
de diagramas.

## Funcionalidades da interface

A interface possui duas abas principais:

- `AFN / AFD`: entrada do AFN, conversao para AFD, simulacao de palavra,
  minimizacao do AFD e conversao de AFD para gramatica regular.
- `Gramatica Regular`: entrada de uma gramatica regular, conversao para
  automato finito e geracao de gramatica a partir do AFD atual.

A area lateral exibe:

- resultado textual das operacoes;
- diagrama visual do automato;
- botao para salvar a imagem PNG gerada.

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
- A minimizacao completa o AFD, remove estados inalcancaveis e aplica
  refinamento de particoes ate estabilizar.
- A conversao GR -> AF cria um AFN equivalente e tambem permite gerar o AFD
  correspondente.
- A conversao AF -> GR usa o AFD atual e gera uma gramatica regular equivalente.
- Os diagramas sao gerados com Graphviz e exibidos na interface com Pillow.