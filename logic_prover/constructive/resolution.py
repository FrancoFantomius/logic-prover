"""Resolution theorem proving with prefixing and relational translation for Intuitionistic Logic.

This module provides two resolution theorem proving methods for Intuitionistic
Propositional Logic (IPC):
1. Prefixed Resolution: Direct clausal resolution over signed prefixed literals
   (p : A^pol) using intuitionistic T-string prefix unification and reduction ordering
   admissibility checks (Wallen 1990; Fitting 1990; Mints 1990; Otten & Kreitz 1996).
2. Relational Translation Resolution: Standard relational S4 translation embedding IPC
   into classical First-Order Logic (FOL) with reflexivity, transitivity, and monotonicity
   frame axioms, delegating refutation proof search to the classical First-Order
   resolution engine (TheoremProver).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Set, FrozenSet, Sequence, Union

from logic_prover.core.ast import (
    Formula,
    Term,
    Variable,
    Constant,
    PredicateApp,
    Equality,
    Not,
    And,
    Or,
    Implies,
    Iff,
    Forall,
)
from logic_prover.core.parser import to_string
from logic_prover.core.sorts import Ind
from logic_prover.core.signature import Signature
from logic_prover.config import SolverConfig
from logic_prover.constructive.common import (
    FALSUM,
    VERUM,
    _is_falsum,
    _is_verum,
    _is_atomic,
    normalize_formula,
)
from logic_prover.constructive.prefix import (
    PrefixSymbol,
    PrefixConstant,
    PrefixVariable,
    Prefix,
    PrefixSubstitution,
    unify_prefixes,
    is_admissible,
)
from logic_prover.constructive.matrix import (
    PositionType,
    Position,
    FormulaTree,
)
from logic_prover.prover.engine import TheoremProver
from logic_prover.prover.proof import ProofDAG


# ==============================================================================
# 1. PREFIXED LITERAL & CLAUSE STRUCTURES
# ==============================================================================


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
        >>> from logic_prover.constructive.resolution import PrefixedLiteral
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
            >>> from logic_prover.constructive.resolution import PrefixedLiteral
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
            >>> from logic_prover.constructive.resolution import PrefixedLiteral
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

    def variables(self) -> Set[PrefixVariable]:
        """Returns the set of prefix variables occurring in this literal.

        Returns:
            Set[PrefixVariable]: Set of prefix variables in the literal.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.prefix import Prefix, PrefixVariable
            >>> from logic_prover.constructive.resolution import PrefixedLiteral
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
            >>> from logic_prover.constructive.resolution import PrefixedLiteral
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
            >>> from logic_prover.constructive.resolution import PrefixedLiteral
            >>> lit = PrefixedLiteral(prefix=Prefix((PrefixConstant("c0"),)), polarity=1, atom=PredicateApp("P", 0, ()))
            >>> lit.to_string()
            'P^1:c0'
        """
        atom_str = to_string(self.atom) if not _is_falsum(self.atom) else "_bot"
        return f"{atom_str}^{self.polarity}:{self.prefix}"

    def __str__(self) -> str:
        """Returns the string representation."""
        return self.to_string()


@dataclass(frozen=True, slots=True)
class PrefixedClause:
    """An immutable disjunction of prefixed signed literals.

    Args:
        literals (FrozenSet[PrefixedLiteral], default=frozenset()): The set of literals.

    Example:
        >>> from logic_prover.constructive.resolution import PrefixedClause
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
            >>> from logic_prover.constructive.resolution import PrefixedClause
            >>> len(PrefixedClause())
            0
        """
        return len(self.literals)

    def is_empty(self) -> bool:
        """Checks if this clause is the empty contradiction clause.

        Returns:
            bool: True if clause has no literals, False otherwise.

        Example:
            >>> from logic_prover.constructive.resolution import PrefixedClause
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
            >>> from logic_prover.constructive.resolution import PrefixedClause, PrefixedLiteral
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

    def variables(self) -> Set[PrefixVariable]:
        """Returns the set of prefix variables occurring across all literals.

        Returns:
            Set[PrefixVariable]: Set of all prefix variables in the clause.

        Example:
            >>> from logic_prover.constructive.resolution import PrefixedClause
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
            >>> from logic_prover.constructive.resolution import PrefixedClause
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
            >>> from logic_prover.constructive.resolution import PrefixedClause
            >>> PrefixedClause().to_string()
            '[]'
        """
        if not self.literals:
            return "[]"
        lits_str = sorted(lit.to_string() for lit in self.literals)
        return f"[ {', '.join(lits_str)} ]"

    def __str__(self) -> str:
        """Returns the string representation of the clause."""
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
        >>> from logic_prover.constructive.resolution import PrefixedResolutionStep, PrefixedClause
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
            >>> from logic_prover.constructive.resolution import PrefixedResolutionStep, PrefixedClause
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
        >>> from logic_prover.constructive.resolution import PrefixedResolutionProofResult
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
            >>> from logic_prover.constructive.resolution import PrefixedResolutionProofResult
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
            >>> from logic_prover.constructive.resolution import PrefixedResolutionProofResult
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
        """Returns the default string representation."""
        return self.to_string()


# ==============================================================================
# 2. PREFIXED CLAUSIFICATION
# ==============================================================================


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
        >>> from logic_prover.constructive.resolution import clausify_prefixed
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


# ==============================================================================
# 3. PREFIXED RESOLUTION PROVER
# ==============================================================================


def resolve_prefixed_clauses(
    c1: PrefixedClause,
    c2: PrefixedClause,
    subst: Optional[PrefixSubstitution] = None,
    tree: Optional[FormulaTree] = None,
) -> List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
    """Computes all possible binary resolvents between two prefixed clauses under admissible prefix unifiers.

    Args:
        c1 (PrefixedClause): First parent clause.
        c2 (PrefixedClause): Second parent clause.
        subst (Optional[PrefixSubstitution], default=None): Current accumulated prefix substitution.
        tree (Optional[FormulaTree], default=None): Formula tree used for reduction ordering admissibility.

    Returns:
        List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
            List of (resolvent_clause, new_substitution, lit1, lit2) tuples.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant, PrefixVariable
        >>> from logic_prover.constructive.resolution import PrefixedClause, PrefixedLiteral, resolve_prefixed_clauses
        >>> p = PredicateApp("P", 0, ())
        >>> c0 = PrefixConstant("c0")
        >>> v1 = PrefixVariable("V1")
        >>> l1 = PrefixedLiteral(Prefix((c0, v1)), 1, p)
        >>> l2 = PrefixedLiteral(Prefix((c0, c0)), 0, p)
        >>> cl1 = PrefixedClause(frozenset([l1]))
        >>> cl2 = PrefixedClause(frozenset([l2]))
        >>> res = resolve_prefixed_clauses(cl1, cl2)
        >>> len(res)
        1
        >>> res[0][0].is_empty()
        True
    """
    initial_subst = subst.copy() if subst is not None else PrefixSubstitution()
    results: List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]] = []

    for l1 in c1.literals:
        # Check complementary literal in c2
        for l2 in c2.literals:
            if l1.atom == l2.atom and l1.polarity != l2.polarity:
                unifs = unify_prefixes(l1.prefix, l2.prefix, initial_subst)
                for unif in unifs:
                    if tree is None or is_admissible(tree, unif):
                        # Construct resolvent: (c1 \ {l1}) U (c2 \ {l2}) instantiated by unif
                        rem1 = set(c1.literals) - {l1}
                        rem2 = set(c2.literals) - {l2}
                        combined = rem1 | rem2
                        resolvent = PrefixedClause(frozenset(lit.substitute(unif) for lit in combined))
                        results.append((resolvent, unif, l1, l2))

    return results


def factor_prefixed_clause(
    clause: PrefixedClause,
    subst: Optional[PrefixSubstitution] = None,
    tree: Optional[FormulaTree] = None,
) -> List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
    """Computes all possible factors of a prefixed clause by unifying identical literals.

    Args:
        clause (PrefixedClause): The clause to factor.
        subst (Optional[PrefixSubstitution], default=None): Accumulated prefix substitution.
        tree (Optional[FormulaTree], default=None): Formula tree for admissibility validation.

    Returns:
        List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
            List of (factored_clause, new_substitution, lit1, lit2) tuples.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant, PrefixVariable
        >>> from logic_prover.constructive.resolution import PrefixedClause, PrefixedLiteral, factor_prefixed_clause
        >>> p = PredicateApp("P", 0, ())
        >>> c0 = PrefixConstant("c0")
        >>> v1 = PrefixVariable("V1")
        >>> l1 = PrefixedLiteral(Prefix((c0, v1)), 1, p)
        >>> l2 = PrefixedLiteral(Prefix((c0, c0)), 1, p)
        >>> cl = PrefixedClause(frozenset([l1, l2]))
        >>> factors = factor_prefixed_clause(cl)
        >>> len(factors)
        1
        >>> len(factors[0][0])
        1
    """
    initial_subst = subst.copy() if subst is not None else PrefixSubstitution()
    results: List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]] = []
    lits = list(clause.literals)

    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            l1, l2 = lits[i], lits[j]
            if l1.atom == l2.atom and l1.polarity == l2.polarity:
                unifs = unify_prefixes(l1.prefix, l2.prefix, initial_subst)
                for unif in unifs:
                    if tree is None or is_admissible(tree, unif):
                        rem = set(lits) - {l2}
                        factored = PrefixedClause(frozenset(lit.substitute(unif) for lit in rem))
                        results.append((factored, unif, l1, l2))

    return results


class PrefixedResolutionProver:
    """Resolution theorem prover operating directly on prefixed clauses for IPC.

    Args:
        max_multiplicity (int, default=3): Maximum multiplicity bound for phi-node duplications.
        max_steps (int, default=1000): Maximum search iterations per multiplicity level.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution import PrefixedResolutionProver
        >>> p = PredicateApp("P", 0, ())
        >>> prover = PrefixedResolutionProver()
        >>> res = prover.prove(Implies(p, p))
        >>> res is not None and res.is_valid
        True
    """

    max_multiplicity: int
    max_steps: int

    def __init__(self, max_multiplicity: int = 3, max_steps: int = 1000) -> None:
        """Initializes the PrefixedResolutionProver with search bounds.

        Args:
            max_multiplicity (int, default=3): Maximum multiplicity limit.
            max_steps (int, default=1000): Maximum search iteration limit.
        """
        self.max_multiplicity = max(1, max_multiplicity)
        self.max_steps = max(1, max_steps)

    def prove(
        self,
        target: Formula,
        premises: Optional[Sequence[Formula]] = None,
    ) -> Optional[PrefixedResolutionProofResult]:
        """Attempts to prove a formula in Intuitionistic Propositional Logic using Prefixed Resolution.

        Args:
            target (Formula): Goal formula AST to prove.
            premises (Optional[Sequence[Formula]], default=None): Optional hypothesis premises.

        Returns:
            Optional[PrefixedResolutionProofResult]: Proof result if proven valid, None otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution import PrefixedResolutionProver
            >>> p = PredicateApp("P", 0, ())
            >>> prover = PrefixedResolutionProver()
            >>> proof = prover.prove(Implies(p, p))
            >>> proof is not None and proof.is_valid
            True
        """
        norm_target = normalize_formula(target)
        norm_premises = tuple(normalize_formula(p) for p in (premises or []))

        for mult in range(1, self.max_multiplicity + 1):
            initial_clauses, tree = clausify_prefixed(
                target=norm_target,
                premises=norm_premises,
                multiplicity=mult,
            )

            if not initial_clauses:
                continue

            proof = self._search_refutation(
                target=norm_target,
                premises=norm_premises,
                initial_clauses=initial_clauses,
                tree=tree,
                multiplicity=mult,
            )
            if proof is not None:
                return proof

        return None

    def _search_refutation(
        self,
        target: Formula,
        premises: Tuple[Formula, ...],
        initial_clauses: List[PrefixedClause],
        tree: FormulaTree,
        multiplicity: int,
    ) -> Optional[PrefixedResolutionProofResult]:
        """Conducts a resolution refutation search closing all initial matrix clauses.

        Args:
            target (Formula): Goal formula.
            premises (Tuple[Formula, ...]): Hypothesis premises.
            initial_clauses (List[PrefixedClause]): Initial decomposed clauses.
            tree (FormulaTree): Decomposition tree for admissibility.
            multiplicity (int): Current multiplicity level.

        Returns:
            Optional[PrefixedResolutionProofResult]: Derived refutation proof or None.
        """
        initial_steps: List[PrefixedResolutionStep] = []
        for i, c in enumerate(initial_clauses, 1):
            initial_steps.append(
                PrefixedResolutionStep(
                    id=f"init_{i}",
                    rule_name="initial",
                    premise_ids=(),
                    clause=c,
                    substitution=PrefixSubstitution(),
                )
            )

        def _find_clause_candidates(
            clause: PrefixedClause,
        ) -> List[Tuple[str, Optional[Tuple[PrefixedLiteral, PrefixedLiteral]], PrefixedLiteral]]:
            candidates = []
            lits = list(clause.literals)
            for i, l1 in enumerate(lits):
                if _is_falsum(l1.atom) and l1.polarity == 1:
                    candidates.append(("falsum_elimination", None, l1))
                for j in range(i + 1, len(lits)):
                    l2 = lits[j]
                    if l1.atom == l2.atom and l1.polarity != l2.polarity:
                        pos = l1 if l1.polarity == 1 else l2
                        neg = l2 if l1.polarity == 1 else l1
                        candidates.append(("resolution", (pos, neg), pos))
            return candidates

        def _backtrack(
            remaining: List[Tuple[PrefixedClause, str]],
            current_subst: PrefixSubstitution,
            accum_steps: List[PrefixedResolutionStep],
            step_counter: int,
        ) -> Optional[Tuple[List[PrefixedResolutionStep], str, PrefixSubstitution]]:
            # Filter already closed clauses
            unclosed: List[Tuple[PrefixedClause, str]] = []
            for clause, init_id in remaining:
                c_inst = clause.substitute(current_subst)
                # Check if this clause is already closed under current substitution
                closed = False
                c_lits = list(c_inst.literals)
                for i, l1 in enumerate(c_lits):
                    if _is_falsum(l1.atom) and l1.polarity == 1:
                        closed = True
                        break
                    for j in range(i + 1, len(c_lits)):
                        l2 = c_lits[j]
                        if l1.atom == l2.atom and l1.polarity != l2.polarity and l1.prefix == l2.prefix:
                            closed = True
                            break
                    if closed:
                        break
                if not closed:
                    unclosed.append((clause, init_id))

            if not unclosed:
                if is_admissible(tree, current_subst):
                    empty_id = f"s{step_counter + 1}"
                    empty_step = PrefixedResolutionStep(
                        id=empty_id,
                        rule_name="empty_clause",
                        premise_ids=tuple(s.id for s in accum_steps[-2:]) if accum_steps else (),
                        clause=PrefixedClause(),
                        substitution=current_subst,
                    )
                    return accum_steps + [empty_step], empty_id, current_subst
                return None

            unclosed.sort(key=lambda item: len(_find_clause_candidates(item[0])))
            target_clause, init_id = unclosed[0]
            rest = unclosed[1:]

            candidates = _find_clause_candidates(target_clause)
            if not candidates:
                return None

            for rule_name, pair, main_lit in candidates:
                if rule_name == "falsum_elimination":
                    step_counter += 1
                    s_id = f"s{step_counter}"
                    step = PrefixedResolutionStep(
                        id=s_id,
                        rule_name="falsum_elimination",
                        premise_ids=(init_id,),
                        clause=PrefixedClause(),
                        substitution=current_subst,
                        parent_literals=(main_lit, main_lit),
                    )
                    res = _backtrack(rest, current_subst, accum_steps + [step], step_counter)
                    if res is not None:
                        return res
                elif rule_name == "resolution" and pair is not None:
                    pos_lit, neg_lit = pair
                    unifs = unify_prefixes(pos_lit.prefix, neg_lit.prefix, current_subst)
                    for unif in unifs:
                        if is_admissible(tree, unif):
                            step_counter += 1
                            s_id = f"s{step_counter}"
                            step = PrefixedResolutionStep(
                                id=s_id,
                                rule_name="resolution",
                                premise_ids=(init_id,),
                                clause=PrefixedClause(),
                                substitution=unif,
                                parent_literals=pair,
                            )
                            res = _backtrack(rest, unif, accum_steps + [step], step_counter)
                            if res is not None:
                                return res

            return None

        indexed_clauses = [(c, f"init_{i}") for i, c in enumerate(initial_clauses, 1)]
        refute_res = _backtrack(
            remaining=indexed_clauses,
            current_subst=PrefixSubstitution(),
            accum_steps=initial_steps,
            step_counter=len(initial_clauses),
        )

        if refute_res is not None:
            all_steps, empty_id, final_subst = refute_res
            return PrefixedResolutionProofResult(
                is_valid=True,
                target=target,
                premises=premises,
                steps=tuple(all_steps),
                empty_clause_id=empty_id,
                substitution=final_subst,
                multiplicity=multiplicity,
            )

        return None



# ==============================================================================
# 4. RELATIONAL TRANSLATION RESOLUTION
# ==============================================================================


def translate_ipc_to_fol(
    formula: Formula,
    world_term: Optional[Term] = None,
    var_counter: Optional[List[int]] = None,
) -> Formula:
    """Translates an Intuitionistic Propositional Logic formula into a First-Order Logic formula.

    Implements the standard relational translation (embedding IPC into modal S4 and FOL):
    - tau(P, w) = P(w)
    - tau(_bot, w) = _bot
    - tau(_top, w) = _top
    - tau(~A, w) = forall w'. (R(w, w') => ~tau(A, w'))
    - tau(A & B, w) = tau(A, w) & tau(B, w)
    - tau(A | B, w) = tau(A, w) | tau(B, w)
    - tau(A => B, w) = forall w'. ((R(w, w') & tau(A, w')) => tau(B, w'))

    Args:
        formula (Formula): The IPC formula AST to translate.
        world_term (Optional[Term], default=None): World parameter term (defaults to Constant('w0')).
        var_counter (Optional[List[int]], default=None): Mutable integer counter for unique world variables.

    Returns:
        Formula: The translated First-Order Logic formula AST.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution import translate_ipc_to_fol
        >>> p = PredicateApp("P", 0, ())
        >>> fol_f = translate_ipc_to_fol(Implies(p, p))
        >>> type(fol_f).__name__
        'Forall'
    """
    if world_term is None:
        world_term = Constant(name="w0", sort=Ind)
    if var_counter is None:
        var_counter = [1]

    if _is_falsum(formula):
        return FALSUM
    if _is_verum(formula):
        return VERUM

    if _is_atomic(formula):
        if isinstance(formula, PredicateApp):
            return PredicateApp(pred=formula.pred, arity=1, args=(world_term,))
        elif isinstance(formula, Equality):
            return formula
        return formula

    if isinstance(formula, Not):
        w_var = Variable(id=var_counter[0], sort=Ind)
        var_counter[0] += 1
        r_rel = PredicateApp(pred="R", arity=2, args=(world_term, w_var))
        tau_op = translate_ipc_to_fol(formula.operand, world_term=w_var, var_counter=var_counter)
        return Forall(variable=w_var, body=Implies(left=r_rel, right=Not(operand=tau_op)))

    if isinstance(formula, And):
        return And(
            left=translate_ipc_to_fol(formula.left, world_term=world_term, var_counter=var_counter),
            right=translate_ipc_to_fol(formula.right, world_term=world_term, var_counter=var_counter),
        )

    if isinstance(formula, Or):
        return Or(
            left=translate_ipc_to_fol(formula.left, world_term=world_term, var_counter=var_counter),
            right=translate_ipc_to_fol(formula.right, world_term=world_term, var_counter=var_counter),
        )

    if isinstance(formula, Implies):
        w_var = Variable(id=var_counter[0], sort=Ind)
        var_counter[0] += 1
        r_rel = PredicateApp(pred="R", arity=2, args=(world_term, w_var))
        tau_left = translate_ipc_to_fol(formula.left, world_term=w_var, var_counter=var_counter)
        tau_right = translate_ipc_to_fol(formula.right, world_term=w_var, var_counter=var_counter)
        antecedent = And(left=r_rel, right=tau_left)
        return Forall(variable=w_var, body=Implies(left=antecedent, right=tau_right))

    if isinstance(formula, Iff):
        norm = normalize_formula(formula)
        return translate_ipc_to_fol(norm, world_term=world_term, var_counter=var_counter)

    return formula


def get_frame_axioms(atomic_predicates: Sequence[str]) -> List[Formula]:
    """Generates the Kripke frame reflexivity, transitivity, and monotonicity axioms in FOL.

    Args:
        atomic_predicates (Sequence[str]): List of proposition names occurring in the target.

    Returns:
        List[Formula]: Frame and monotonicity axioms in FOL.

    Example:
        >>> from logic_prover.constructive.resolution import get_frame_axioms
        >>> axioms = get_frame_axioms(["P"])
        >>> len(axioms)
        3
    """
    x = Variable(id=1, sort=Ind)
    y = Variable(id=2, sort=Ind)
    z = Variable(id=3, sort=Ind)

    # 1. Reflexivity: forall x. R(x, x)
    refl = Forall(variable=x, body=PredicateApp(pred="R", arity=2, args=(x, x)))

    # 2. Transitivity: forall x y z. ((R(x, y) & R(y, z)) => R(x, z))
    r_xy = PredicateApp(pred="R", arity=2, args=(x, y))
    r_yz = PredicateApp(pred="R", arity=2, args=(y, z))
    r_xz = PredicateApp(pred="R", arity=2, args=(x, z))
    trans = Forall(
        variable=x,
        body=Forall(
            variable=y,
            body=Forall(
                variable=z,
                body=Implies(left=And(left=r_xy, right=r_yz), right=r_xz),
            ),
        ),
    )

    axioms: List[Formula] = [refl, trans]

    # 3. Monotonicity for atomic predicates: forall x y. ((P(x) & R(x, y)) => P(y))
    for pred in sorted(set(atomic_predicates)):
        if pred in ("R", "_bot", "_top"):
            continue
        p_x = PredicateApp(pred=pred, arity=1, args=(x,))
        p_y = PredicateApp(pred=pred, arity=1, args=(y,))
        mono = Forall(
            variable=x,
            body=Forall(
                variable=y,
                body=Implies(left=And(left=p_x, right=r_xy), right=p_y),
            ),
        )
        axioms.append(mono)

    return axioms


def _extract_predicate_names(formula: Formula) -> Set[str]:
    """Recursively collects all atomic proposition names in a formula AST.

    Args:
        formula (Formula): Formula to inspect.

    Returns:
        Set[str]: Set of predicate names.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution import _extract_predicate_names
        >>> p = PredicateApp("P", 0, ())
        >>> q = PredicateApp("Q", 0, ())
        >>> _extract_predicate_names(Implies(p, q)) == {"P", "Q"}
        True
    """
    names: Set[str] = set()
    if isinstance(formula, PredicateApp):
        if formula.pred not in ("_bot", "_top"):
            names.add(formula.pred)
    elif isinstance(formula, Not):
        names.update(_extract_predicate_names(formula.operand))
    elif isinstance(formula, (And, Or, Implies, Iff)):
        names.update(_extract_predicate_names(formula.left))
        names.update(_extract_predicate_names(formula.right))
    return names


@dataclass
class TranslationResolutionResult:
    """Container for the derivation results of Translation-based Resolution.

    Args:
        is_valid (bool): Whether the formula was proven valid in IPC.
        target_ipc (Formula): Original IPC goal formula.
        premises_ipc (Tuple[Formula, ...]): Original IPC hypothesis premises.
        target_fol (Formula): Translated First-Order Logic goal formula.
        premises_fol (Tuple[Formula, ...]): Translated premises including frame axioms.
        frame_axioms (Tuple[Formula, ...]): Generated reflexivity, transitivity, and monotonicity axioms.
        proof_dag (Optional[ProofDAG]): Reconstructed natural deduction / resolution proof DAG.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution import TranslationResolutionResult
        >>> p = PredicateApp("P", 0, ())
        >>> res = TranslationResolutionResult(True, Implies(p, p), (), Implies(p, p), (), (), None)
        >>> res.is_valid
        True
    """

    is_valid: bool
    target_ipc: Formula
    premises_ipc: Tuple[Formula, ...]
    target_fol: Formula
    premises_fol: Tuple[Formula, ...]
    frame_axioms: Tuple[Formula, ...]
    proof_dag: Optional[ProofDAG]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the translation resolution result to a JSON dictionary.

        Returns:
            Dict[str, Any]: Serialized result dictionary.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution import TranslationResolutionResult
            >>> p = PredicateApp("P", 0, ())
            >>> res = TranslationResolutionResult(True, Implies(p, p), (), Implies(p, p), (), (), None)
            >>> res.to_dict()["is_valid"]
            True
        """
        return {
            "is_valid": self.is_valid,
            "target_ipc": to_string(self.target_ipc),
            "premises_ipc": [to_string(p) for p in self.premises_ipc],
            "target_fol": to_string(self.target_fol),
            "premises_fol": [to_string(p) for p in self.premises_fol],
            "frame_axioms": [to_string(a) for a in self.frame_axioms],
            "has_proof_dag": self.proof_dag is not None,
        }

    def to_string(self) -> str:
        """Formats the translation proof result as a multi-line report.

        Returns:
            str: Multi-line description of the translation proof.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution import TranslationResolutionResult
            >>> p = PredicateApp("P", 0, ())
            >>> res = TranslationResolutionResult(True, Implies(p, p), (), Implies(p, p), (), (), None)
            >>> "Translation Resolution Proof" in res.to_string()
            True
        """
        lines: List[str] = []
        lines.append("=== Relational Translation Resolution Proof (IPC -> FOL) ===")
        lines.append(f"Target (IPC): {to_string(self.target_ipc)}")
        if self.premises_ipc:
            lines.append(f"Premises (IPC): {', '.join(to_string(p) for p in self.premises_ipc)}")
        lines.append(f"Target (FOL): {to_string(self.target_fol)}")
        lines.append(f"Status: {'VALID (Proven via FOL Superposition/Resolution)' if self.is_valid else 'UNPROVABLE'}")
        lines.append(f"Frame Axioms Count: {len(self.frame_axioms)}")
        if self.proof_dag is not None:
            lines.append(f"Reconstructed Proof Steps: {len(self.proof_dag.steps)}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Returns the default string representation."""
        return self.to_string()


class TranslationResolutionProver:
    """Resolution prover utilizing Relational S4 Translation to First-Order Logic.

    Args:
        max_steps (int, default=1000): Maximum given-clause loop iterations in the FOL prover.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution import TranslationResolutionProver
        >>> p = PredicateApp("P", 0, ())
        >>> prover = TranslationResolutionProver()
        >>> res = prover.prove(Implies(p, p))
        >>> res is not None and res.is_valid
        True
    """

    max_steps: int
    timeout_sec: float

    def __init__(self, max_steps: int = 1000, timeout_sec: float = 10.0) -> None:
        """Initializes the TranslationResolutionProver with limits.

        Args:
            max_steps (int, default=1000): Maximum search steps.
            timeout_sec (float, default=10.0): Search timeout in seconds.
        """
        self.max_steps = max(1, max_steps)
        self.timeout_sec = max(0.1, timeout_sec)

    def prove(
        self,
        target: Formula,
        premises: Optional[Sequence[Formula]] = None,
    ) -> Optional[TranslationResolutionResult]:
        """Attempts to prove an IPC formula by translating to FOL and running the First-Order resolution prover.

        Args:
            target (Formula): The IPC formula AST to prove.
            premises (Optional[Sequence[Formula]], default=None): Optional hypothesis premises.

        Returns:
            Optional[TranslationResolutionResult]: Proof result if proven valid, None if unprovable.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution import TranslationResolutionProver
            >>> p = PredicateApp("P", 0, ())
            >>> prover = TranslationResolutionProver()
            >>> res = prover.prove(Implies(p, p))
            >>> res is not None and res.is_valid
            True
        """
        norm_target = normalize_formula(target)
        norm_premises = tuple(normalize_formula(p) for p in (premises or []))

        # Collect atomic predicates
        atoms: Set[str] = set()
        atoms.update(_extract_predicate_names(norm_target))
        for p in norm_premises:
            atoms.update(_extract_predicate_names(p))

        # Build Signature
        sig = Signature()
        sig.register_predicate("R", 2, (Ind, Ind))
        for pred in atoms:
            sig.register_predicate(pred, 1, (Ind,))
        sig.register_constant("w0", Ind)

        w0 = Constant("w0", sort=Ind)
        target_fol = translate_ipc_to_fol(norm_target, world_term=w0)
        premises_fol_list = [translate_ipc_to_fol(p, world_term=w0) for p in norm_premises]

        frame_axioms = get_frame_axioms(sorted(atoms))
        all_fol_premises = frame_axioms + premises_fol_list

        config = SolverConfig(
            prover_max_steps=self.max_steps,
            prover_timeout_sec=self.timeout_sec,
        )
        fol_prover = TheoremProver(signature=sig, config=config)

        try:
            proof_dag = fol_prover.prove(
                target=target_fol,
                premises=all_fol_premises,
                max_steps=self.max_steps,
                timeout_sec=self.timeout_sec,
            )
            return TranslationResolutionResult(
                is_valid=True,
                target_ipc=norm_target,
                premises_ipc=norm_premises,
                target_fol=target_fol,
                premises_fol=tuple(all_fol_premises),
                frame_axioms=tuple(frame_axioms),
                proof_dag=proof_dag,
            )
        except Exception:
            return None


# ==============================================================================
# 5. UNIFIED CONSTRUCTIVE RESOLUTION PROVER
# ==============================================================================


class ConstructiveResolutionProver:
    """Unified resolution theorem prover supporting both Prefixed and Translation methods for IPC.

    Args:
        method (str, default='prefixed'): Proof search strategy ('prefixed', 'translation', or 'auto').
        max_multiplicity (int, default=3): Multiplicity bound for prefixed resolution.
        max_steps (int, default=1000): Maximum search iterations.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution import ConstructiveResolutionProver
        >>> p = PredicateApp("P", 0, ())
        >>> prover = ConstructiveResolutionProver(method="prefixed")
        >>> res = prover.prove(Implies(p, p))
        >>> res is not None and res.is_valid
        True
    """

    method: str
    max_multiplicity: int
    max_steps: int
    timeout_sec: float

    def __init__(
        self,
        method: str = "prefixed",
        max_multiplicity: int = 3,
        max_steps: int = 1000,
        timeout_sec: float = 10.0,
    ) -> None:
        """Initializes the unified constructive resolution prover.

        Args:
            method (str, default='prefixed'): Resolution method ('prefixed', 'translation', 'auto').
            max_multiplicity (int, default=3): Multiplicity limit for prefixed resolution.
            max_steps (int, default=1000): Maximum resolution steps limit.
            timeout_sec (float, default=10.0): Wall-clock timeout limit in seconds.
        """
        self.method = method.lower()
        self.max_multiplicity = max(1, max_multiplicity)
        self.max_steps = max(1, max_steps)
        self.timeout_sec = max(0.1, timeout_sec)

    def prove(
        self,
        target: Formula,
        premises: Optional[Sequence[Formula]] = None,
    ) -> Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]:
        """Attempts to prove an IPC formula using the configured resolution strategy.

        Args:
            target (Formula): Formula AST to prove.
            premises (Optional[Sequence[Formula]], default=None): Optional hypothesis premises.

        Returns:
            Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]:
                Proof result if valid, None otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution import ConstructiveResolutionProver
            >>> p = PredicateApp("P", 0, ())
            >>> prover = ConstructiveResolutionProver()
            >>> res = prover.prove(Implies(p, p))
            >>> res is not None and res.is_valid
            True
        """
        if self.method == "prefixed":
            p_prover = PrefixedResolutionProver(
                max_multiplicity=self.max_multiplicity,
                max_steps=self.max_steps,
            )
            return p_prover.prove(target=target, premises=premises)

        elif self.method == "translation":
            t_prover = TranslationResolutionProver(
                max_steps=self.max_steps,
                timeout_sec=self.timeout_sec,
            )
            return t_prover.prove(target=target, premises=premises)

        elif self.method == "auto":
            # Try prefixed resolution first
            p_prover = PrefixedResolutionProver(
                max_multiplicity=self.max_multiplicity,
                max_steps=self.max_steps,
            )
            p_res = p_prover.prove(target=target, premises=premises)
            if p_res is not None:
                return p_res

            # Fall back to translation resolution
            t_prover = TranslationResolutionProver(
                max_steps=self.max_steps,
                timeout_sec=self.timeout_sec,
            )
            return t_prover.prove(target=target, premises=premises)

        else:
            raise ValueError(f"Unknown constructive resolution method: {self.method}")


# ==============================================================================
# 6. CONVENIENCE API FUNCTIONS
# ==============================================================================


def prove_prefixed_resolution(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    max_multiplicity: int = 3,
    max_steps: int = 1000,
) -> Optional[PrefixedResolutionProofResult]:
    """Proves an intuitionistic propositional formula using Prefixed Resolution.

    Args:
        formula (Formula): Goal formula to prove.
        premises (Optional[List[Formula]], default=None): Optional hypothesis premises.
        max_multiplicity (int, default=3): Multiplicity bound for phi-node duplications.
        max_steps (int, default=1000): Maximum search iterations.

    Returns:
        Optional[PrefixedResolutionProofResult]: Derivation proof result if valid, None if unprovable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution import prove_prefixed_resolution
        >>> p = PredicateApp("P", 0, ())
        >>> proof = prove_prefixed_resolution(Implies(p, p))
        >>> proof is not None and proof.is_valid
        True
    """
    prover = PrefixedResolutionProver(
        max_multiplicity=max_multiplicity,
        max_steps=max_steps,
    )
    return prover.prove(target=formula, premises=premises)


def prove_translation_resolution(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    max_steps: int = 1000,
    timeout_sec: float = 10.0,
) -> Optional[TranslationResolutionResult]:
    """Proves an intuitionistic propositional formula using Relational S4 Translation Resolution.

    Args:
        formula (Formula): Goal formula to prove.
        premises (Optional[List[Formula]], default=None): Optional hypothesis premises.
        max_steps (int, default=1000): Maximum resolution steps in the FOL prover.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Returns:
        Optional[TranslationResolutionResult]: Proof result if valid, None if unprovable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution import prove_translation_resolution
        >>> p = PredicateApp("P", 0, ())
        >>> proof = prove_translation_resolution(Implies(p, p))
        >>> proof is not None and proof.is_valid
        True
    """
    prover = TranslationResolutionProver(
        max_steps=max_steps,
        timeout_sec=timeout_sec,
    )
    return prover.prove(target=formula, premises=premises)


def prove_resolution(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    method: str = "prefixed",
    max_multiplicity: int = 3,
    max_steps: int = 1000,
    timeout_sec: float = 10.0,
) -> Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]:
    """Proves an intuitionistic propositional formula using resolution (prefixed or translation).

    Args:
        formula (Formula): Formula AST to prove.
        premises (Optional[List[Formula]], default=None): Optional hypothesis premises.
        method (str, default='prefixed'): Resolution method ('prefixed', 'translation', 'auto').
        max_multiplicity (int, default=3): Maximum multiplicity limit for prefixed resolution.
        max_steps (int, default=1000): Maximum search iterations.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Returns:
        Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]:
            Proof result if valid, None if unprovable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution import prove_resolution
        >>> p = PredicateApp("P", 0, ())
        >>> proof = prove_resolution(Implies(p, p), method="prefixed")
        >>> proof is not None and proof.is_valid
        True
    """
    prover = ConstructiveResolutionProver(
        method=method,
        max_multiplicity=max_multiplicity,
        max_steps=max_steps,
        timeout_sec=timeout_sec,
    )
    return prover.prove(target=formula, premises=premises)


__all__ = [
    # Prefixed resolution structures
    "PrefixedLiteral",
    "PrefixedClause",
    "PrefixedResolutionStep",
    "PrefixedResolutionProofResult",
    # Prefixed operations & prover
    "clausify_prefixed",
    "resolve_prefixed_clauses",
    "factor_prefixed_clause",
    "PrefixedResolutionProver",
    "prove_prefixed_resolution",
    # Translation resolution
    "translate_ipc_to_fol",
    "get_frame_axioms",
    "TranslationResolutionResult",
    "TranslationResolutionProver",
    "prove_translation_resolution",
    # Unified resolution prover & API
    "ConstructiveResolutionProver",
    "prove_resolution",
]
