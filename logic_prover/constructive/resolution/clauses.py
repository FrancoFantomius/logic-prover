"""Prefixed literal and clause data structures and matrix-path clausification for intuitionistic resolution."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Set, FrozenSet, Sequence

from logic_prover.core.ast import (
    Formula,
    Term,
    Variable,
)
from logic_prover.core.parser import to_string
from logic_prover.core.substitutions import substitute_formula
from logic_prover.constructive.common import (
    _is_falsum,
    normalize_formula,
)
from logic_prover.constructive.prefix import (
    PrefixConstant,
    PrefixVariable,
    Prefix,
    PrefixSubstitution,
)
from logic_prover.constructive.matrix import (
    FormulaTree,
)


@dataclass(frozen=True, slots=True)
class PrefixedLiteral:
    """A signed atomic proposition annotated with a Kripke world prefix.

    Args:
        prefix (Prefix): Kripke world prefix sequence.
        polarity (int): Polar truth value (1 = premise / true, 0 = goal / false).
        atom (Formula): Atomic proposition AST node.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant
        >>> from logic_prover.constructive.resolution.clauses import PrefixedLiteral
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> lit = PrefixedLiteral(prefix=Prefix((PrefixConstant("c0"),)), polarity=1, atom=p)
        >>> lit.polarity
        1
    """

    prefix: Prefix
    polarity: int
    atom: Formula

    def negate(self) -> PrefixedLiteral:
        """Returns the complementary prefixed literal with toggled polarity.

        Returns:
            PrefixedLiteral: Complementary literal with inverted polarity.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.prefix import Prefix
            >>> from logic_prover.constructive.resolution.clauses import PrefixedLiteral
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> lit = PrefixedLiteral(prefix=Prefix(), polarity=1, atom=p)
            >>> lit.negate().polarity
            0
        """
        return PrefixedLiteral(prefix=self.prefix, polarity=1 - self.polarity, atom=self.atom)

    def substitute(self, subst: PrefixSubstitution) -> PrefixedLiteral:
        """Applies a prefix substitution to the literal's prefix.

        Args:
            subst (PrefixSubstitution): The prefix substitution to apply.

        Returns:
            PrefixedLiteral: New literal with instantiated prefix.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.prefix import Prefix, PrefixVariable, PrefixConstant, PrefixSubstitution
            >>> from logic_prover.constructive.resolution.clauses import PrefixedLiteral
            >>> v = PrefixVariable("V1")
            >>> c = PrefixConstant("c1")
            >>> lit = PrefixedLiteral(prefix=Prefix((v,)), polarity=1, atom=PredicateApp("P", 0, ()))
            >>> subst = PrefixSubstitution().bind(v, (c,))
            >>> inst = lit.substitute(subst)
            >>> str(inst.prefix)
            'c1'
        """
        return PrefixedLiteral(
            prefix=subst.apply(self.prefix),
            polarity=self.polarity,
            atom=self.atom,
        )

    def substitute_terms(self, term_subst: Dict[Variable, Term]) -> PrefixedLiteral:
        """Applies a first-order term substitution to the formula atom in this literal.

        Args:
            term_subst (Dict[Variable, Term]): Mapping from individual variables to replacement terms.

        Returns:
            PrefixedLiteral: New literal instance with substituted atom.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Variable, Constant
            >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant
            >>> from logic_prover.constructive.resolution.clauses import PrefixedLiteral
            >>> x = Variable(1)
            >>> a = Constant("a")
            >>> p_x = PredicateApp("P", 1, (x,))
            >>> lit = PrefixedLiteral(Prefix((PrefixConstant("c0"),)), 1, p_x)
            >>> inst = lit.substitute_terms({x: a})
            >>> isinstance(inst.atom, PredicateApp)
            True
        """
        if not term_subst:
            return self
        return PrefixedLiteral(
            prefix=self.prefix,
            polarity=self.polarity,
            atom=substitute_formula(self.atom, term_subst),
        )

    def variables(self) -> Set[PrefixVariable]:
        """Returns the set of prefix variables occurring in this literal.

        Returns:
            Set[PrefixVariable]: Set of prefix variables in the literal.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.prefix import Prefix, PrefixVariable
            >>> from logic_prover.constructive.resolution.clauses import PrefixedLiteral
            >>> v = PrefixVariable("V1")
            >>> lit = PrefixedLiteral(prefix=Prefix((v,)), polarity=0, atom=PredicateApp("P", 0, ()))
            >>> len(lit.variables())
            1
        """
        return self.prefix.variables()

    def constants(self) -> Set[PrefixConstant]:
        """Returns the set of prefix constants occurring in this literal.

        Returns:
            Set[PrefixConstant]: Set of prefix constants in the literal.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant
            >>> from logic_prover.constructive.resolution.clauses import PrefixedLiteral
            >>> c = PrefixConstant("c0")
            >>> lit = PrefixedLiteral(prefix=Prefix((c,)), polarity=0, atom=PredicateApp("P", 0, ()))
            >>> len(lit.constants())
            1
        """
        return self.prefix.constants()

    def to_string(self) -> str:
        """Returns a string representation of the signed prefixed literal.

        Returns:
            str: Formatted literal string (e.g. 'P^1:c0.V1').

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant
            >>> from logic_prover.constructive.resolution.clauses import PrefixedLiteral
            >>> lit = PrefixedLiteral(prefix=Prefix((PrefixConstant("c0"),)), polarity=1, atom=PredicateApp("P", 0, ()))
            >>> lit.to_string()
            'P^1:c0'
        """
        atom_str = to_string(self.atom) if not _is_falsum(self.atom) else "_bot"
        return f"{atom_str}^{self.polarity}:{self.prefix}"

    def __str__(self) -> str:
        """Returns the string representation.

        Returns:
            str: Formatted literal string.
        """
        return self.to_string()


@dataclass(frozen=True, slots=True)
class PrefixedClause:
    """An immutable disjunction of prefixed signed literals.

    Args:
        literals (FrozenSet[PrefixedLiteral], default=frozenset()): The set of literals.

    Example:
        >>> from logic_prover.constructive.resolution.clauses import PrefixedClause
        >>> empty_c = PrefixedClause()
        >>> empty_c.is_empty()
        True
    """

    literals: FrozenSet[PrefixedLiteral] = field(default_factory=frozenset)

    def __len__(self) -> int:
        """Returns the number of literals in the clause.

        Returns:
            int: Number of literals.

        Example:
            >>> from logic_prover.constructive.resolution.clauses import PrefixedClause
            >>> len(PrefixedClause())
            0
        """
        return len(self.literals)

    def is_empty(self) -> bool:
        """Checks if this clause is the empty contradiction clause.

        Returns:
            bool: True if clause has no literals, False otherwise.

        Example:
            >>> from logic_prover.constructive.resolution.clauses import PrefixedClause
            >>> PrefixedClause().is_empty()
            True
        """
        return len(self.literals) == 0

    def substitute(self, subst: PrefixSubstitution) -> PrefixedClause:
        """Applies a prefix substitution to all literals in the clause.

        Args:
            subst (PrefixSubstitution): The prefix substitution to apply.

        Returns:
            PrefixedClause: Instantiated clause.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.prefix import Prefix, PrefixVariable, PrefixConstant, PrefixSubstitution
            >>> from logic_prover.constructive.resolution.clauses import PrefixedClause, PrefixedLiteral
            >>> v = PrefixVariable("V1")
            >>> c = PrefixConstant("c1")
            >>> lit = PrefixedLiteral(prefix=Prefix((v,)), polarity=1, atom=PredicateApp("P", 0, ()))
            >>> clause = PrefixedClause(frozenset([lit]))
            >>> subst = PrefixSubstitution().bind(v, (c,))
            >>> inst = clause.substitute(subst)
            >>> len(inst)
            1
        """
        return PrefixedClause(frozenset(lit.substitute(subst) for lit in self.literals))

    def substitute_terms(self, term_subst: Dict[Variable, Term]) -> PrefixedClause:
        """Applies a first-order term substitution to all literals in the clause.

        Args:
            term_subst (Dict[Variable, Term]): Mapping from individual variables to replacement terms.

        Returns:
            PrefixedClause: Instantiated clause with term-substituted literals.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Variable, Constant
            >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant
            >>> from logic_prover.constructive.resolution.clauses import PrefixedClause, PrefixedLiteral
            >>> x = Variable(1)
            >>> a = Constant("a")
            >>> lit = PrefixedLiteral(Prefix((PrefixConstant("c0"),)), 1, PredicateApp("P", 1, (x,)))
            >>> cl = PrefixedClause(frozenset([lit]))
            >>> inst = cl.substitute_terms({x: a})
            >>> len(inst)
            1
        """
        if not term_subst:
            return self
        return PrefixedClause(frozenset(lit.substitute_terms(term_subst) for lit in self.literals))

    def variables(self) -> Set[PrefixVariable]:
        """Returns the set of prefix variables occurring across all literals.

        Returns:
            Set[PrefixVariable]: Set of all prefix variables in the clause.

        Example:
            >>> from logic_prover.constructive.resolution.clauses import PrefixedClause
            >>> PrefixedClause().variables() == set()
            True
        """
        res: Set[PrefixVariable] = set()
        for lit in self.literals:
            res.update(lit.variables())
        return res

    def constants(self) -> Set[PrefixConstant]:
        """Returns the set of prefix constants occurring across all literals.

        Returns:
            Set[PrefixConstant]: Set of all prefix constants in the clause.

        Example:
            >>> from logic_prover.constructive.resolution.clauses import PrefixedClause
            >>> PrefixedClause().constants() == set()
            True
        """
        res: Set[PrefixConstant] = set()
        for lit in self.literals:
            res.update(lit.constants())
        return res

    def to_string(self) -> str:
        """Formats the clause as a sorted bracketed string of literals.

        Returns:
            str: String representation of the clause (e.g. '[ P^1:c0, Q^0:c0.c1 ]' or '[]').

        Example:
            >>> from logic_prover.constructive.resolution.clauses import PrefixedClause
            >>> PrefixedClause().to_string()
            '[]'
        """
        if not self.literals:
            return "[]"
        lits_str = sorted(lit.to_string() for lit in self.literals)
        return f"[ {', '.join(lits_str)} ]"

    def __str__(self) -> str:
        """Returns the string representation of the clause.

        Returns:
            str: Bracketed string of clause literals.
        """
        return self.to_string()


@dataclass(frozen=True)
class PrefixedResolutionStep:
    """Represents a single step in a prefixed resolution derivation trace.

    Args:
        id (str): Unique identifier for this proof step.
        rule_name (str): The inference rule applied ('initial', 'resolution', 'factoring', 'falsum_elimination').
        premise_ids (Tuple[str, ...]): IDs of the parent clauses from which this was derived.
        clause (PrefixedClause): The resulting derived prefixed clause.
        substitution (PrefixSubstitution, default=PrefixSubstitution()): Substitution applied during inference.
        parent_literals (Optional[Tuple[PrefixedLiteral, PrefixedLiteral]], default=None): Resolved literal pair.

    Example:
        >>> from logic_prover.constructive.resolution.clauses import PrefixedResolutionStep, PrefixedClause
        >>> step = PrefixedResolutionStep(id="c1", rule_name="initial", premise_ids=(), clause=PrefixedClause())
        >>> step.rule_name
        'initial'
    """

    id: str
    rule_name: str
    premise_ids: Tuple[str, ...]
    clause: PrefixedClause
    substitution: PrefixSubstitution = field(default_factory=PrefixSubstitution)
    parent_literals: Optional[Tuple[PrefixedLiteral, PrefixedLiteral]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the resolution step to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary structure with step metadata and clause.

        Example:
            >>> from logic_prover.constructive.resolution.clauses import PrefixedResolutionStep, PrefixedClause
            >>> step = PrefixedResolutionStep(id="c1", rule_name="initial", premise_ids=(), clause=PrefixedClause())
            >>> step.to_dict()["id"]
            'c1'
        """
        return {
            "id": self.id,
            "rule": self.rule_name,
            "premises": list(self.premise_ids),
            "clause": self.clause.to_string(),
            "substitution": self.substitution.to_dict(),
        }


@dataclass
class PrefixedResolutionProofResult:
    """Container for the results of a prefixed resolution proof search.

    Args:
        is_valid (bool): Whether the formula was proven valid in IPC.
        target (Formula): The target goal formula.
        premises (Tuple[Formula, ...]): Hypothesis premises.
        steps (Tuple[PrefixedResolutionStep, ...]): Ordered sequence of resolution steps.
        empty_clause_id (Optional[str]): ID of the derived empty clause step.
        substitution (PrefixSubstitution): Final global unifying prefix substitution.
        multiplicity (int): Multiplicity bound at which the proof was found.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.prefix import PrefixSubstitution
        >>> from logic_prover.constructive.resolution.clauses import PrefixedResolutionProofResult
        >>> p = PredicateApp("P", 0, ())
        >>> res = PrefixedResolutionProofResult(True, Implies(p, p), (), (), "step_0", PrefixSubstitution(), 1)
        >>> res.is_valid
        True
    """

    is_valid: bool
    target: Formula
    premises: Tuple[Formula, ...]
    steps: Tuple[PrefixedResolutionStep, ...]
    empty_clause_id: Optional[str]
    substitution: PrefixSubstitution
    multiplicity: int

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the prefixed resolution proof result to a JSON-compatible dictionary.

        Returns:
            Dict[str, Any]: Dictionary containing validity, target, premises, steps, and substitution.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.prefix import PrefixSubstitution
            >>> from logic_prover.constructive.resolution.clauses import PrefixedResolutionProofResult
            >>> p = PredicateApp("P", 0, ())
            >>> res = PrefixedResolutionProofResult(True, Implies(p, p), (), (), "s1", PrefixSubstitution(), 1)
            >>> res.to_dict()["is_valid"]
            True
        """
        return {
            "is_valid": self.is_valid,
            "target": to_string(self.target),
            "premises": [to_string(p) for p in self.premises],
            "multiplicity": self.multiplicity,
            "empty_clause_id": self.empty_clause_id,
            "substitution": self.substitution.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
        }

    def to_string(self) -> str:
        """Formats the proof result as a readable multi-line derivation summary.

        Returns:
            str: Multi-line string showing resolution derivation steps.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.prefix import PrefixSubstitution
            >>> from logic_prover.constructive.resolution.clauses import PrefixedResolutionProofResult
            >>> p = PredicateApp("P", 0, ())
            >>> res = PrefixedResolutionProofResult(True, Implies(p, p), (), (), "s1", PrefixSubstitution(), 1)
            >>> "Prefixed Resolution Proof" in res.to_string()
            True
        """
        lines: List[str] = []
        lines.append("=== Prefixed Resolution Proof (IPC) ===")
        lines.append(f"Target: {to_string(self.target)}")
        if self.premises:
            lines.append(f"Premises: {', '.join(to_string(p) for p in self.premises)}")
        lines.append(f"Status: {'VALID (Intuitionistically Proven)' if self.is_valid else 'UNPROVABLE'}")
        lines.append(f"Multiplicity: {self.multiplicity}")
        if self.steps:
            lines.append("Derivation Steps:")
            for s in self.steps:
                prems_str = f" from {', '.join(s.premise_ids)}" if s.premise_ids else ""
                lines.append(f"  [{s.id}] {s.clause.to_string()} ({s.rule_name}{prems_str})")
        if self.substitution.mapping:
            lines.append("Prefix Substitution:")
            for k, v in self.substitution.mapping.items():
                lines.append(f"  sigma({k.name}) = {'.'.join(sym.name for sym in v)}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Returns the default string representation.

        Returns:
            str: Multi-line proof summary string.
        """
        return self.to_string()


def clausify_prefixed(
    target: Formula,
    premises: Optional[Sequence[Formula]] = None,
    multiplicity: int = 1,
) -> Tuple[List[PrefixedClause], FormulaTree]:
    """Decomposes an intuitionistic formula and premises into a set of prefixed initial clauses.

    Constructs a polar FormulaTree and extracts each matrix path as a prefixed clause
    representing an elementary goal to refute.

    Args:
        target (Formula): Goal formula AST.
        premises (Optional[Sequence[Formula]], default=None): Optional hypothesis premises.
        multiplicity (int, default=1): Multiplicity bound for phi-node duplications.

    Returns:
        Tuple[List[PrefixedClause], FormulaTree]: List of initial prefixed clauses and decomposition tree.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.clauses import clausify_prefixed
        >>> p = PredicateApp("P", 0, ())
        >>> clauses, tree = clausify_prefixed(Implies(p, p))
        >>> len(clauses) >= 1
        True
    """
    norm_target = normalize_formula(target)
    norm_premises = [normalize_formula(p) for p in (premises or [])]

    tree = FormulaTree(
        target=norm_target,
        premises=norm_premises,
        multiplicity=max(1, multiplicity),
    )
    paths = tree.get_paths()

    clauses: List[PrefixedClause] = []
    for path in paths:
        lits: Set[PrefixedLiteral] = set()
        for pos in path:
            lits.add(
                PrefixedLiteral(
                    prefix=pos.prefix,
                    polarity=pos.polarity,
                    atom=pos.formula,
                )
            )
        clauses.append(PrefixedClause(frozenset(lits)))

    return clauses, tree


__all__ = [
    "PrefixedLiteral",
    "PrefixedClause",
    "PrefixedResolutionStep",
    "PrefixedResolutionProofResult",
    "clausify_prefixed",
]
