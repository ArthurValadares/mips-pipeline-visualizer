import functools
from typing import List

import networkx as nx
import yaml

from .ast_nodes import InstructionNode


class PipelineConfig:
    def __init__(self, yaml_path: str = "pipeline.yml"):
        try:
            with open(yaml_path, "r") as f:
                data = yaml.safe_load(f)
                self.latencies = data.get("latencies", {})
        except FileNotFoundError:
            self.latencies = {"default": 1}

    def get_latency(self, op: str) -> int:
        return self.latencies.get(op.lower(), self.latencies.get("default", 1))


class BasicBlock:
    def __init__(self, name: str):
        self.name = name
        self.instructions: List[InstructionNode] = []


class SimulatorGraph:
    def __init__(
        self,
        instructions: List[InstructionNode],
        config: PipelineConfig,
        forwarding: bool = True,
    ):
        self.instructions = instructions
        self.config = config
        self.forwarding = forwarding
        self.cfg = nx.DiGraph()
        self.blocks: List[BasicBlock] = []
        self._build_basic_blocks()

    def _build_basic_blocks(self):
        """Divide instruções em um conjunto de diagramas/blocos baseado em labels e branches"""
        current_block = BasicBlock("entry")
        self.blocks.append(current_block)

        for inst in self.instructions:
            if inst.label:
                current_block = BasicBlock(inst.label)
                self.blocks.append(current_block)

            current_block.instructions.append(inst)

            if inst.is_branch:
                current_block = BasicBlock(f"after_{inst.index}")
                self.blocks.append(current_block)

    @functools.lru_cache(maxsize=None)
    def calculate_stall(self, current_idx: int, dep_idx: int) -> int:
        """
        Uso do decorador de cache: Evita recálculo se a dependência
        do nó A no nó B já foi resolvida em outro branch de análise.
        """
        curr = self.instructions[current_idx]
        dep = self.instructions[dep_idx]

        if self.forwarding:
            # Lógica COM Forwarding (EX/EX e MEM/EX)
            # O dado precisa estar pronto no ciclo em que o EX da instrução atual inicia.
            latency = self.config.get_latency(dep.op)
            required_ex_start = dep.c_ex + latency

            # O ciclo EX normal de 'curr' sem stalls começaria logo após o seu ID
            curr_ex_start = curr.c_id + 1

            if curr_ex_start >= required_ex_start:
                return 0
            return required_ex_start - curr_ex_start
        else:
            # Lógica SEM Forwarding
            # Sem forwarding, o dado deve ser lido dos registradores (no estágio ID).
            # Para isso, a instrução produtora precisa estar no estágio de WB.
            # Assumimos o comportamento MIPS clássico: Escrita na primeira metade do ciclo,
            # Leitura na segunda metade. Assim, o ID pode ocorrer no mesmo ciclo do WB.
            # O estágio WB ocorre em c_ex + 2.
            required_id_cycle = dep.c_ex + 2

            if curr.c_id >= required_id_cycle:
                return 0
            return required_id_cycle - curr.c_id

    def schedule(self):
        for i, inst in enumerate(self.instructions):
            if i == 0:
                inst.c_if = 0
            else:
                inst.c_if = self.instructions[i - 1].c_if + 1

            inst.c_id = inst.c_if + 1

            # Checar RAW nas 3 instruções anteriores
            max_stall = 0
            for j in range(max(0, i - 3), i):
                prev = self.instructions[j]
                if set(inst.get_sources()) & set(prev.get_dests()):
                    stall = self.calculate_stall(i, j)
                    max_stall = max(max_stall, stall)

            inst.bubbles = max_stall
            inst.c_ex = inst.c_id + 1 + max_stall
