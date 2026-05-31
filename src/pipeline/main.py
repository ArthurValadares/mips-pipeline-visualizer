from importlib.resources import files
from pathlib import Path

import click
from lark import Lark, Transformer

from .ast_nodes import RType, IType, MemType, JType, HaltType, InstructionNode
from .graph import SimulatorGraph, PipelineConfig
from .svg import SVGRenderer

GRAMMAR_PATH = files("pipeline").joinpath("grammar.lark")


class MIPSBuilder(Transformer):
    def __init__(self):
        super().__init__()
        self.index = 0
        self.current_label = None

    def label(self, tokens):
        # Apenas salva o label, a instrução subsequente irá consumi-lo
        self.current_label = str(tokens[0])
        return None

    def r_type(self, tokens):
        op, rd, rs, rt = [str(t) for t in tokens]
        inst = RType(
            op=op, rd=rd, rs=rs, rt=rt, index=self.index, label=self.current_label
        )
        self._advance()
        return inst

    def i_type(self, tokens):
        op, rt, rs, imm = [str(t) for t in tokens]
        inst = IType(
            op=op, rt=rt, rs=rs, imm=imm, index=self.index, label=self.current_label
        )
        self._advance()
        return inst

    def j_type(self, tokens):
        op, target = [str(t) for t in tokens]
        inst = JType(op=op, target=target, index=self.index, label=self.current_label)
        self._advance()
        return inst

    def halt_inst(self, tokens):
        inst = HaltType(op="halt", index=self.index, label=self.current_label)
        self._advance()
        return inst

    def nop_inst(self, tokens):
        inst = HaltType(op="nop", index=self.index, label=self.current_label)
        self._advance()
        return inst

    def mem_type(self, tokens):
        op, rt, imm, rs = [str(t) for t in tokens]
        inst = MemType(
            op=op, rt=rt, rs=rs, imm=imm, index=self.index, label=self.current_label
        )
        self._advance()
        return inst

    def _advance(self):
        self.index += 1
        self.current_label = None


@click.command()
@click.argument("input_file", type=click.File("r"))
@click.argument("output", type=click.File("w"))
@click.option(
    "--config", default="pipeline.yml", help="Arquivo de configuração do pipeline"
)
@click.option(
    "--forwarding/--no-forwarding",
    default=True,
    help="Habilita ou desabilita o encaminhamento de dados (Data Forwarding)",
)
def main(input_file, output, config, forwarding):
    text = input_file.read()

    # 1. Carrega Gramática
    with open(GRAMMAR_PATH, "r") as f:
        parser = Lark(f.read(), start="start", parser="lalr", transformer=MIPSBuilder())

    # 2. Parsing Robusto
    tree = parser.parse(text)
    instructions = [
        child for child in tree.children if isinstance(child, InstructionNode)
    ]

    # 3. Configuração e Grafo (Passando a flag capturada do terminal)
    pipeline_cfg = PipelineConfig(config)
    graph = SimulatorGraph(instructions, pipeline_cfg, forwarding=forwarding)
    graph.schedule()

    # Extrair apenas o nome do arquivo ignorando o caminho da pasta
    filename = Path(input_file.name).name

    # 4. Renderização Declarativa (Agora aceitando nome do ficheiro)
    renderer = SVGRenderer(graph.blocks, filename=filename)
    output.write(renderer.render())

    estado_fwd = "HABILITADO" if forwarding else "DESABILITADO"
    click.echo(f"✓ Gerado: {output.name} com Blocos Básicos (Forwarding: {estado_fwd})")


if __name__ == "__main__":
    main()
