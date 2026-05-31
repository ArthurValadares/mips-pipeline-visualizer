# MIPS Pipeline Visualizer

Um simulador e gerador de diagramas SVG para execução de instruções MIPS em um pipeline clássico de 5 estágios (IF, ID, EX, MEM, WB).

Esta ferramenta analisa código Assembly MIPS, constrói uma Árvore de Sintaxe Abstrata (AST), calcula o escalonamento de ciclos (resolvendo dependências de dados RAW) e gera um gráfico de Gantt renderizado em SVG mostrando a evolução temporal das instruções, bolhas (*stalls*) e blocos básicos.

## Funcionalidades

* **Parser Customizado:** Utiliza a biblioteca `Lark` para interpretar o Assembly MIPS de forma robusta a partir de um arquivo de gramática (`grammar.lark`).
* **Resolução de Conflitos (Data Hazards):** Detecta dependências do tipo RAW (Read After Write) e injeta bolhas de forma automática.
* **Data Forwarding Configurável:** Habilite ou desabilite o encaminhamento de dados (caminhos EX/EX e MEM/EX) através de uma simples *flag* na CLI.
* **Latências Customizáveis:** Defina a latência de execução (estágio EX) para instruções específicas usando um arquivo de configuração YAML.
* **Renderização Declarativa em SVG:** Separação limpa entre lógica e apresentação através do uso de `Jinja2` para desenhar gráficos responsivos e precisos do pipeline.
* **Agrupamento por Blocos Básicos:** Separa visualmente o código em blocos lógicos baseados em *labels* e *branches*.

## Tecnologias Utilizadas

* **Python 3.8+**
* **Poetry** (Gerenciamento de dependências)
* **Lark** (Parsing de gramática)
* **Jinja2** (Templating do SVG)
* **Click** (Interface de Linha de Comando)
* **PyYAML** (Configuração de latências)
* **NetworkX** (Estruturação de grafos de fluxo)

## Instalação

Como este projeto utiliza o [Poetry](https://python-poetry.org/) para o gerenciamento de pacotes e ambientes virtuais, o processo de instalação é simples e direto.

1. Clone o repositório:

    ```bash
    git clone [https://github.com/seu-usuario/mips-pipeline-visualizer.git](https://github.com/seu-usuario/mips-pipeline-visualizer.git)
    cd mips-pipeline-visualizer
    ```

2. Instale as dependências via Poetry:

    ```bash
    poetry install
    ```

## Como Usar

A ferramenta funciona via Interface de Linha de Comando (CLI). Você precisa fornecer um arquivo com o código assembly de entrada e o caminho de destino do arquivo SVG.

### Uso Básico

Execute o módulo principal passando o arquivo de entrada e a saída desejada:

```bash
poetry run python -m src.pipeline.main input_code.s output_diagram.svg
```

### Opções da CLI

* `--config`: Especifique um arquivo YAML customizado para latências (o padrão é `pipeline.yml`).
* `--forwarding` / `--no-forwarding`: Habilita ou desabilita o *Data Forwarding*. O comportamento padrão é habilitado (`--forwarding`).

**Exemplo com Forwarding desabilitado e configuração customizada:**

```bash
poetry run python -m src.pipeline.main input.s output.svg --config my_latencies.yml --no-forwarding
```

## Configuração de Latência (YAML)

O simulador permite definir ciclos extras de execução para instruções complexas (como multiplicações ou divisões de ponto flutuante). Crie um arquivo `pipeline.yml` (ou outro nome e passe via flag `--config`):

```yaml
units:
  integer: 2
  float: 1
  memory: 1

latencies:
  default: 1
  mul: 3
  div: 10
  lw: 2
  l.d: 3

```

*Nota: A latência padrão para operações não listadas é 1 ciclo.*

## Estrutura do Projeto

Abaixo está o descritivo dos principais componentes arquiteturais da ferramenta:

```text
.
├── src/
│   └── pipeline/
│       ├── main.py       # Ponto de entrada (CLI Click, Parser Lark e orquestração)
│       ├── ast_nodes.py  # Classes de nós de instruções (RType, IType, etc) e os templates Jinja2 (SVG)
│       ├── graph.py      # Lógica central: cálculo de stalls, hazards (com e sem forwarding) e criação de blocos
│       └── svg.py        # Classe SVGRenderer que organiza os blocos renderizados num grid unificado
├── grammar.lark          # Definição da gramática MIPS (regras EBNF interpretadas pelo Lark)
├── pyproject.toml        # Configurações do Poetry e dependências
├── LICENSE
└── README.md

```

## Funcionamento Interno

1. **Parsing:** O `Lark` lê a gramática e o texto de entrada. O `MIPSBuilder` transforma os tokens da gramática em instâncias fortemente tipadas do arquivo `ast_nodes.py` (`RType`, `IType`, `MemType`, etc).
2. **Escalonamento Temporal (Scheduling):** O `SimulatorGraph` agrupa as instruções em `BasicBlocks`. Ele itera pelas instruções simulando a passagem dos ciclos IF e ID, procurando conflitos RAW (analisando `get_sources()` da instrução atual contra `get_dests()` das anteriores).
3. **Stalls e Forwarding:** Se o *forwarding* está ativo, o *stall* só ocorre se a dependência não puder ser resolvida a tempo para o estágio de EX. Se estiver inativo, a instrução dependente fica paralisada em ID até que a produtora alcance o Write-Back (WB).
4. **Renderização:** A classe `SVGRenderer` utiliza os templates atrelados aos *decorators* de cada nó de instrução para injetar as dimensões exatas num grid geométrico do SVG.

## Como Contribuir

Contribuições são muito bem-vindas! Se você encontrar um bug, quiser propor uma melhoria na representação visual ou adicionar suporte a novas instruções:

1. Faça um *Fork* do projeto
2. Crie uma *Branch* para sua *Feature* (`git checkout -b feature/MinhaNovaFeature`)
3. Faça o *Commit* das suas alterações (`git commit -m 'Adiciona suporte à instrução X'`)
4. Faça o *Push* para a Branch (`git push origin feature/MinhaNovaFeature`)
5. Abra um *Pull Request*

## Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.
