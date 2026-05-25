from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict


class ProcedureOutput(TypedDict):
    type: str
    code: str
    description: str
    units: int
    suggested_modifiers: List[str]


@dataclass(frozen=True)
class Procedure:
    type: str
    code: str
    description: str
    units: int = 1
    suggested_modifiers: Optional[List[str]] = None

    def to_output(self) -> ProcedureOutput:
        return {
            "type": self.type,
            "code": self.code,
            "description": self.description,
            "units": max(1, math.ceil(self.units)),
            "suggested_modifiers": self.suggested_modifiers or [],
        }


class ProceduralCodingEngine:
    """Extracts and validates CPT + HCPCS Level II procedural candidates from clinical text."""

    CPT_PATTERN = re.compile(r"\b\d{5}\b")
    HCPCS_PATTERN = re.compile(r"\b([A-Z]\d{4})\b", re.IGNORECASE)
    DOSAGE_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s*(mg|g|mcg|ug|ml)\b", re.IGNORECASE)
    PER_UNIT_PATTERN = re.compile(r"\bper\s*(\d+(?:\.\d+)?)\s*(mg|g|mcg|ug|ml)\b", re.IGNORECASE)

    HCPCS_ALLOWED_PREFIXES = {"A", "E", "G", "J", "L", "P", "Q", "S", "V"}

    DRUG_ADMIN_CPT = {
        "96360": "Intravenous infusion, hydration; initial",
        "96365": "Intravenous infusion, therapeutic; initial",
        "96372": "Therapeutic, prophylactic, or diagnostic injection; subcutaneous or intramuscular",
    }

    HCPCS_REFERENCE: Dict[str, str] = {
        "J2130": "Injection, methylprednisolone acetate (Depo-Medrol), per 20 mg",
        "J3301": "Injection, triamcinolone acetonide, per 10 mg",
        "J0696": "Injection, ceftriaxone sodium, per 250 mg",
    }

    DRUG_KEYWORD_TO_HCPCS = {
        "depo-medrol": "J2130",
        "depomedrol": "J2130",
        "methylprednisolone": "J2130",
        "triamcinolone": "J3301",
        "ceftriaxone": "J0696",
    }

    def extract_procedures(self, clinical_note: str) -> Dict[str, List[ProcedureOutput]]:
        text = clinical_note or ""
        lowered = text.lower()

        procedures: List[Procedure] = []
        seen = set()

        # Direct CPT extraction
        for code in self.CPT_PATTERN.findall(text):
            if self._is_valid_cpt_category_i(code):
                self._push(
                    procedures,
                    seen,
                    Procedure(
                        type="CPT",
                        code=code,
                        description=self.DRUG_ADMIN_CPT.get(code, "CPT Category I procedure"),
                        units=1,
                        suggested_modifiers=self._suggested_modifiers(lowered),
                    ),
                )

        # Direct HCPCS Level II extraction
        for raw_code in self.HCPCS_PATTERN.findall(text):
            hcpcs_code = raw_code.upper()
            if self._is_valid_hcpcs_level_ii(hcpcs_code):
                desc = self.HCPCS_REFERENCE.get(hcpcs_code, "HCPCS Level II procedure/supply/service")
                units = self._calculate_hcpcs_units(text, desc)
                self._push(
                    procedures,
                    seen,
                    Procedure(
                        type="HCPCS_Level_II",
                        code=hcpcs_code,
                        description=desc,
                        units=units,
                        suggested_modifiers=self._suggested_modifiers(lowered),
                    ),
                )

        # Dual extraction logic for injections/infusions
        has_admin_action = self._contains_drug_administration_action(lowered)
        if has_admin_action:
            admin_code = self._infer_admin_cpt(lowered)
            if admin_code:
                self._push(
                    procedures,
                    seen,
                    Procedure(
                        type="CPT",
                        code=admin_code,
                        description=self.DRUG_ADMIN_CPT[admin_code],
                        units=1,
                        suggested_modifiers=self._suggested_modifiers(lowered),
                    ),
                )

            hcpcs_j = self._infer_hcpcs_j_code(lowered, text)
            if hcpcs_j:
                desc = self.HCPCS_REFERENCE.get(hcpcs_j, "HCPCS J-code drug")
                units = self._calculate_hcpcs_units(text, desc)
                self._push(
                    procedures,
                    seen,
                    Procedure(
                        type="HCPCS_Level_II",
                        code=hcpcs_j,
                        description=desc,
                        units=units,
                        suggested_modifiers=self._suggested_modifiers(lowered),
                    ),
                )

        output = {"procedures": [p.to_output() for p in procedures]}
        self._validate_output(output)
        return output

    def to_json(self, clinical_note: str) -> str:
        return json.dumps(self.extract_procedures(clinical_note), indent=2)

    def _push(self, procedures: List[Procedure], seen: set, procedure: Procedure) -> None:
        key = (procedure.type, procedure.code)
        if key in seen:
            return
        procedures.append(procedure)
        seen.add(key)

    def _is_valid_cpt_category_i(self, code: str) -> bool:
        if not code.isdigit() or len(code) != 5:
            return False
        numeric = int(code)
        return 100 <= numeric <= 99999

    def _is_valid_hcpcs_level_ii(self, code: str) -> bool:
        return bool(re.fullmatch(r"[A-Z]\d{4}", code)) and code[0] in self.HCPCS_ALLOWED_PREFIXES

    def _contains_drug_administration_action(self, lowered: str) -> bool:
        return any(
            token in lowered
            for token in [
                "injection",
                "inject",
                "intramuscular",
                "subcutaneous",
                "intravenous",
                "infusion",
                "iv infusion",
                "administered",
                "administration",
            ]
        )

    def _infer_admin_cpt(self, lowered: str) -> Optional[str]:
        if re.search(r"\b(hydration|rehydration)\b", lowered):
            return "96360"
        if re.search(r"\b(infusion|intravenous|iv)\b", lowered):
            return "96365"
        if re.search(r"\b(injection|intramuscular|subcutaneous)\b", lowered):
            return "96372"
        return None

    def _infer_hcpcs_j_code(self, lowered: str, text: str) -> Optional[str]:
        explicit_j = re.search(r"\b(J\d{4})\b", text, re.IGNORECASE)
        if explicit_j:
            return explicit_j.group(1).upper()

        for keyword, code in self.DRUG_KEYWORD_TO_HCPCS.items():
            if keyword in lowered:
                return code
        return None

    def _calculate_hcpcs_units(self, text: str, descriptor: str) -> int:
        dose_mg = self._extract_dose_mg(text)
        base_unit_mg = self._extract_descriptor_unit_mg(descriptor)
        if dose_mg is None or base_unit_mg is None or base_unit_mg <= 0:
            return 1
        return max(1, math.ceil(dose_mg / base_unit_mg))

    def _extract_dose_mg(self, text: str) -> Optional[float]:
        match = self.DOSAGE_PATTERN.search(text)
        if not match:
            return None
        dose = float(match.group(1))
        unit = match.group(2).lower()
        return self._convert_to_mg(dose, unit)

    def _extract_descriptor_unit_mg(self, descriptor: str) -> Optional[float]:
        match = self.PER_UNIT_PATTERN.search(descriptor)
        if not match:
            return None
        dose = float(match.group(1))
        unit = match.group(2).lower()
        return self._convert_to_mg(dose, unit)

    @staticmethod
    def _convert_to_mg(value: float, unit: str) -> Optional[float]:
        """Convert mass units to mg; returns None for volume-only units (e.g., mL)."""
        unit = unit.lower()
        if unit == "mg":
            return value
        if unit == "g":
            return value * 1000.0
        if unit in {"mcg", "ug"}:
            return value / 1000.0
        # volume-only value cannot be safely converted to mass without concentration
        return None

    def _suggested_modifiers(self, lowered: str) -> List[str]:
        has_right_modifier = bool(re.search(r"\bright\b", lowered))
        has_left_modifier = bool(re.search(r"\bleft\b", lowered))
        bilateral = "bilateral" in lowered or (has_right_modifier and has_left_modifier)
        if bilateral:
            return ["50"]
        if has_right_modifier:
            return ["RT"]
        if has_left_modifier:
            return ["LT"]
        return []

    def _validate_output(self, output: Dict[str, List[ProcedureOutput]]) -> None:
        if "procedures" not in output or not isinstance(output["procedures"], list):
            raise ValueError("Output must contain a 'procedures' array.")

        for idx, item in enumerate(output["procedures"]):
            if item["type"] not in {"CPT", "HCPCS_Level_II"}:
                raise ValueError(f"Invalid type at procedures[{idx}].")
            if not isinstance(item["code"], str) or not item["code"]:
                raise ValueError(f"Invalid code at procedures[{idx}].")
            if not isinstance(item["description"], str):
                raise ValueError(f"Invalid description at procedures[{idx}].")
            if not isinstance(item["units"], int) or item["units"] < 1:
                raise ValueError(f"Invalid units at procedures[{idx}].")
            if not isinstance(item["suggested_modifiers"], list):
                raise ValueError(f"Invalid suggested_modifiers at procedures[{idx}].")

            if item["type"] == "CPT" and not self._is_valid_cpt_category_i(item["code"]):
                raise ValueError(f"Invalid CPT code at procedures[{idx}]: {item['code']}")
            if item["type"] == "HCPCS_Level_II" and not self._is_valid_hcpcs_level_ii(item["code"]):
                raise ValueError(f"Invalid HCPCS Level II code at procedures[{idx}]: {item['code']}")


if __name__ == "__main__":
    engine = ProceduralCodingEngine()
    print(engine.to_json("40 mg Depo-Medrol injection administered in clinic, J2130."))
