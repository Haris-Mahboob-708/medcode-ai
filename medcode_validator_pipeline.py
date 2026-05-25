from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class ConceptDefinition:
    """Deterministic concept-to-code definition."""

    concept: str
    code: str
    description: str
    keywords: Tuple[str, ...]
    is_symptom: bool = False


@dataclass
class SectionBlock:
    """A parsed clinical section with deterministic priority weight."""

    name: str
    text: str
    weight: int
    is_discharge_priority: bool


@dataclass
class ExtractedConcept:
    """Intermediate extracted concept before validation/filtering."""

    concept: str
    code: str
    description: str
    evidence: str
    section_name: str
    section_weight: int
    is_symptom: bool


class MedCodeValidatorPipeline:
    """
    Deterministic Extract-Validate-Filter pipeline for ICD-10 diagnosis extraction.

    Architecture:
    1) Extract: broad concept candidates from sectioned clinical text (LLM pluggable).
    2) Validate: deterministic negation + section-priority validation.
    3) Filter: guideline-based symptom pruning (ICD-10-CM I.B.18 heuristic).
    """

    _SECTION_HEADERS: Dict[str, int] = {
        "chief complaint": 2,
        "history of present illness": 3,
        "hpi": 3,
        "assessment": 5,
        "plan": 5,
        "assessment/plan": 7,
        "discharge assessment": 10,
        "discharge plan": 10,
        "discharge assessment/plan": 10,
        "final diagnosis": 10,
        "final disposition": 10,
    }

    _NEGATION_TRIGGERS: Tuple[str, ...] = (
        "ruled out",
        "rule out",
        "r/o",
        "ro",
        "negative for",
        "denies",
        "no evidence of",
        "without",
        "not",
    )

    _SEPARATE_CONDITION_MARKERS: Tuple[str, ...] = (
        "separate condition",
        "co-existing",
        "coexisting",
        "independent of",
        "unrelated",
        "chronic",
    )

    _IMPLICIT_SYMPTOM_MAP: Dict[str, Tuple[str, ...]] = {
        "K21.9": ("R07.9", "R06.02"),
        "I21.19": ("R07.9", "R06.02"),
    }

    def __init__(
        self,
        llm_extractor: Optional[Callable[[str, Sequence[ConceptDefinition]], List[str]]] = None,
        concept_catalog: Optional[Sequence[ConceptDefinition]] = None,
    ) -> None:
        self._catalog: Tuple[ConceptDefinition, ...] = tuple(concept_catalog or self._default_catalog())
        self._llm_extractor: Callable[[str, Sequence[ConceptDefinition]], List[str]] = (
            llm_extractor or self._keyword_llm_stub
        )
        self._nlp = self._init_spacy()

    def run(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Return the validated JSON payload for clinical ICD extraction."""
        clinical_text: str = self._validate_payload(payload)
        sections: List[SectionBlock] = self._parse_sections(clinical_text)
        extracted: List[ExtractedConcept] = self._extract_candidates(sections)

        confirmed: List[ExtractedConcept] = []
        excluded: List[Dict[str, str]] = []

        for candidate in extracted:
            negated, reason = self._is_negated(candidate)
            if negated:
                excluded.append({"concept": candidate.concept, "reason": reason})
                continue
            confirmed.append(candidate)

        confirmed = self._apply_section_priority(confirmed)
        confirmed, pruned = self._enforce_icd_symptom_guideline(confirmed)
        excluded.extend(pruned)

        deduped_confirmed = self._dedupe_confirmed(confirmed)
        deduped_excluded = self._dedupe_excluded(excluded)

        return {
            "input_summary": self._build_summary(clinical_text),
            "confirmed_diagnoses": [
                {
                    "code": c.code,
                    "description": c.description,
                    "clinical_evidence": c.evidence,
                }
                for c in deduped_confirmed
            ],
            "negated_or_excluded_concepts": deduped_excluded,
        }

    def _validate_payload(self, payload: Mapping[str, Any]) -> str:
        if not isinstance(payload, Mapping):
            raise TypeError("Input payload must be a mapping with a 'clinical_text' field.")

        clinical_text: Any = payload.get("clinical_text")
        if clinical_text is None:
            raise ValueError("Missing required field: 'clinical_text'.")
        if not isinstance(clinical_text, str):
            raise TypeError("Field 'clinical_text' must be a string.")
        cleaned = clinical_text.strip()
        if not cleaned:
            raise ValueError("Field 'clinical_text' cannot be empty.")
        return cleaned

    def _parse_sections(self, text: str) -> List[SectionBlock]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return [SectionBlock(name="clinical_note", text=text, weight=1, is_discharge_priority=False)]

        blocks: List[SectionBlock] = []
        current_name = "clinical_note"
        current_weight = 1
        current_priority = False
        current_text_parts: List[str] = []

        for line in lines:
            detected_name, detected_weight = self._match_header(line)
            if detected_name is not None:
                if current_text_parts:
                    blocks.append(
                        SectionBlock(
                            name=current_name,
                            text=" ".join(current_text_parts),
                            weight=current_weight,
                            is_discharge_priority=current_priority,
                        )
                    )
                current_name = detected_name
                current_weight = detected_weight
                current_priority = detected_weight >= 10
                headerless_line = re.sub(r"^[A-Za-z\s/]+:\s*", "", line).strip()
                current_text_parts = [headerless_line] if headerless_line else []
            else:
                current_text_parts.append(line)

        if current_text_parts:
            blocks.append(
                SectionBlock(
                    name=current_name,
                    text=" ".join(current_text_parts),
                    weight=current_weight,
                    is_discharge_priority=current_priority,
                )
            )

        return blocks or [SectionBlock(name="clinical_note", text=text, weight=1, is_discharge_priority=False)]

    def _match_header(self, line: str) -> Tuple[Optional[str], int]:
        lowered = line.lower()
        for header, weight in self._SECTION_HEADERS.items():
            if lowered.startswith(f"{header}:"):
                return header, weight
        return None, 1

    def _extract_candidates(self, sections: Sequence[SectionBlock]) -> List[ExtractedConcept]:
        extracted: List[ExtractedConcept] = []
        for block in sections:
            concepts = self._llm_extractor(block.text, self._catalog)
            for concept_name in concepts:
                definition = self._definition_by_concept(concept_name)
                if definition is None:
                    continue
                evidence = self._best_evidence_sentence(block.text, definition.keywords)
                extracted.append(
                    ExtractedConcept(
                        concept=definition.concept,
                        code=definition.code,
                        description=definition.description,
                        evidence=evidence,
                        section_name=block.name,
                        section_weight=block.weight,
                        is_symptom=definition.is_symptom,
                    )
                )
        return extracted

    def _apply_section_priority(self, confirmed: Sequence[ExtractedConcept]) -> List[ExtractedConcept]:
        priority_items = [c for c in confirmed if c.section_weight >= 10]
        if not priority_items:
            return list(confirmed)

        prioritized_codes = {c.code for c in priority_items}
        resolved: List[ExtractedConcept] = list(priority_items)

        for item in confirmed:
            if item.code in prioritized_codes:
                continue
            if item.is_symptom:
                continue
            if any(marker in item.evidence.lower() for marker in self._SEPARATE_CONDITION_MARKERS):
                resolved.append(item)

        return resolved

    def _enforce_icd_symptom_guideline(
        self,
        confirmed: Sequence[ExtractedConcept],
    ) -> Tuple[List[ExtractedConcept], List[Dict[str, str]]]:
        definitive_codes = {c.code for c in confirmed if not c.is_symptom}
        implied_symptoms: set[str] = set()
        for code in definitive_codes:
            implied_symptoms.update(self._IMPLICIT_SYMPTOM_MAP.get(code, ()))

        kept: List[ExtractedConcept] = []
        removed: List[Dict[str, str]] = []

        for item in confirmed:
            if item.code not in implied_symptoms:
                kept.append(item)
                continue

            separate = any(marker in item.evidence.lower() for marker in self._SEPARATE_CONDITION_MARKERS)
            if separate:
                kept.append(item)
                continue

            removed.append(
                {
                    "concept": item.concept,
                    "reason": "Excluded by ICD-10-CM I.B.18: symptom integral to confirmed definitive diagnosis.",
                }
            )

        return kept, removed

    def _is_negated(self, candidate: ExtractedConcept) -> Tuple[bool, str]:
        evidence = candidate.evidence.lower()

        # Lexical trigger check (deterministic fallback and phrase-level negation).
        for trigger in self._NEGATION_TRIGGERS:
            if trigger in evidence:
                if self._trigger_scopes_concept(trigger, evidence, candidate.concept.lower()):
                    return True, f"Negation trigger '{trigger}' scoped to concept in sentence."

        # Optional spaCy dependency check when parser is available.
        if self._nlp is not None:
            doc = self._nlp(candidate.evidence)
            for token in doc:
                if token.text.lower() in candidate.concept.lower().split():
                    if any(child.dep_ == "neg" for child in token.children):
                        return True, "Dependency negation modifier detected by spaCy parser."
                    if token.dep_ == "neg":
                        return True, "Dependency negation modifier detected by spaCy parser."

        return False, ""

    def _trigger_scopes_concept(self, trigger: str, sentence: str, concept: str) -> bool:
        trigger_pos = sentence.find(trigger)
        if trigger_pos < 0:
            return False

        concept_terms = concept.split()
        for term in concept_terms:
            term_pos = sentence.find(term)
            if term_pos < 0:
                continue
            if 0 <= term_pos - trigger_pos <= 80:
                return True
            if 0 <= trigger_pos - term_pos <= 25:
                return True
        return False

    def _definition_by_concept(self, concept: str) -> Optional[ConceptDefinition]:
        for definition in self._catalog:
            if definition.concept == concept:
                return definition
        return None

    def _best_evidence_sentence(self, text: str, keywords: Iterable[str]) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        lowered_keywords = tuple(k.lower() for k in keywords)
        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in lowered_keywords):
                return sentence.strip()
        return text[:200].strip()

    def _dedupe_confirmed(self, confirmed: Sequence[ExtractedConcept]) -> List[ExtractedConcept]:
        by_code: Dict[str, ExtractedConcept] = {}
        for item in confirmed:
            current = by_code.get(item.code)
            if current is None or item.section_weight > current.section_weight:
                by_code[item.code] = item
        return sorted(by_code.values(), key=lambda c: (-c.section_weight, c.code))

    def _dedupe_excluded(self, excluded: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
        seen: set[Tuple[str, str]] = set()
        result: List[Dict[str, str]] = []
        for item in excluded:
            key = (item["concept"].lower(), item["reason"])
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    def _build_summary(self, text: str) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        return compact[:180] + ("..." if len(compact) > 180 else "")

    @staticmethod
    def _keyword_llm_stub(text: str, concepts: Sequence[ConceptDefinition]) -> List[str]:
        lowered = text.lower()
        found: List[str] = []
        for concept in concepts:
            if any(keyword in lowered for keyword in concept.keywords):
                found.append(concept.concept)
        return found

    @staticmethod
    def _init_spacy() -> Any:
        try:
            import spacy  # type: ignore

            try:
                return spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "textcat"])
            except Exception:
                blank = spacy.blank("en")
                if "sentencizer" not in blank.pipe_names:
                    blank.add_pipe("sentencizer")
                return blank
        except Exception:
            return None

    @staticmethod
    def _default_catalog() -> Sequence[ConceptDefinition]:
        return (
            ConceptDefinition(
                concept="acute myocardial infarction",
                code="I21.19",
                description="STEMI of inferior wall, other coronary artery",
                keywords=("myocardial infarction", "stemi", "heart attack", "mi"),
            ),
            ConceptDefinition(
                concept="acute gerd",
                code="K21.9",
                description="Gastro-esophageal reflux disease without esophagitis",
                keywords=("gerd", "acid reflux", "gastroesophageal reflux", "acute gerd"),
            ),
            ConceptDefinition(
                concept="chest pain",
                code="R07.9",
                description="Chest pain, unspecified",
                keywords=("chest pain", "substernal pain"),
                is_symptom=True,
            ),
            ConceptDefinition(
                concept="shortness of breath",
                code="R06.02",
                description="Shortness of breath",
                keywords=("shortness of breath", "dyspnea", "sob"),
                is_symptom=True,
            ),
        )
