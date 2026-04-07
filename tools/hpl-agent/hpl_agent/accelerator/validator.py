from __future__ import annotations
import ast as ast_mod
from dataclasses import dataclass
from .generator import GeneratedImpl
from .gap_analyzer import StubReport

@dataclass
class ValidationOutcome:
    impl: GeneratedImpl
    syntax_ok: bool
    imports_resolvable: bool
    contract_checks: list[tuple[str, bool]]
    overall: str  # "pass" | "fail" | "partial"

class ImplValidator:
    def validate(self, impl: GeneratedImpl, report: StubReport) -> ValidationOutcome:
        syntax_ok = self._check_syntax(impl.python_source)
        imports_ok = self._check_imports(impl.python_source)
        contract_checks = [
            (contract, contract.lower()[:20] in impl.python_source.lower())
            for contract in report.spec_contracts[:5]
        ]
        passes = sum(1 for _, ok in contract_checks if ok)
        if not syntax_ok:
            overall = "fail"
        elif passes == len(contract_checks):
            overall = "pass"
        elif passes > 0:
            overall = "partial"
        else:
            overall = "fail"
        return ValidationOutcome(
            impl=impl,
            syntax_ok=syntax_ok,
            imports_resolvable=imports_ok,
            contract_checks=contract_checks,
            overall=overall,
        )

    def _check_syntax(self, source: str) -> bool:
        try:
            ast_mod.parse(source)
            return True
        except SyntaxError:
            return False

    def _check_imports(self, source: str) -> bool:
        try:
            compile(source, "<generated>", "exec")
            return True
        except Exception:
            return False
