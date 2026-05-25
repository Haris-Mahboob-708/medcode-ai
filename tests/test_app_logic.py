import importlib
import sys
import types
import unittest


class _SessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _install_streamlit_stub():
    st = types.ModuleType("streamlit")
    st.session_state = _SessionState()
    st.sidebar = _Context()
    st.set_page_config = lambda **kwargs: None
    st.markdown = lambda *args, **kwargs: None
    st.button = lambda *args, **kwargs: False
    st.multiselect = lambda *args, **kwargs: []
    st.tabs = lambda labels: [_Context() for _ in labels]
    st.columns = lambda spec, **kwargs: [_Context() for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.text_area = lambda *args, **kwargs: kwargs.get("value", "")
    st.caption = lambda *args, **kwargs: None
    st.rerun = lambda *args, **kwargs: None
    st.expander = lambda *args, **kwargs: _Context()
    st.download_button = lambda *args, **kwargs: None
    st.warning = lambda *args, **kwargs: None
    st.info = lambda *args, **kwargs: None
    st.text_input = lambda *args, **kwargs: ""
    st.radio = lambda *args, **kwargs: "All"
    sys.modules["streamlit"] = st


def _load_app_module():
    _install_streamlit_stub()
    sys.modules.pop("app", None)
    return importlib.import_module("app")


class AppLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _load_app_module()

    def test_match_codes_groups_types_and_sorts_confidence_desc(self):
        note = (
            "Established patient follow-up for type 2 diabetes mellitus with hyperglycemia. "
            "HbA1c and comprehensive metabolic panel ordered."
        )
        icd10, cpt, hcpcs = self.app.match_codes(note)

        self.assertGreaterEqual(len(icd10), 2)
        self.assertTrue(all(code["type"] == "icd10" for code in icd10))
        self.assertTrue(all(code["type"] == "cpt" for code in cpt))
        self.assertTrue(all(code["type"] == "hcpcs" for code in hcpcs))
        self.assertEqual(
            [code["confidence"] for code in icd10],
            sorted((code["confidence"] for code in icd10), reverse=True),
        )
        self.assertIn("E11.9", {code["code"] for code in icd10})
        self.assertIn("E11.65", {code["code"] for code in icd10})
        self.assertIn("83036", {code["code"] for code in cpt})
        self.assertIn("80053", {code["code"] for code in cpt})

    def test_match_codes_enforces_minimum_confidence_floor(self):
        note = "Patient has dysuria."
        icd10, cpt, hcpcs = self.app.match_codes(note)
        all_hits = icd10 + cpt + hcpcs

        self.assertTrue(all_hits)
        self.assertEqual(
            min(code["confidence"] for code in all_hits),
            20,
        )

    def test_conf_html_maps_thresholds_to_expected_labels_and_classes(self):
        high_html = self.app.conf_html(70)
        medium_html = self.app.conf_html(40)
        low_html = self.app.conf_html(39)

        self.assertIn("conf-high", high_html)
        self.assertIn("High match", high_html)
        self.assertIn("conf-medium", medium_html)
        self.assertIn("Medium match", medium_html)
        self.assertIn("conf-low", low_html)
        self.assertIn("Low match", low_html)

    def test_risk_html_outputs_expected_symbol_for_each_risk_level(self):
        self.assertIn("⚠ High risk", self.app.risk_html("high"))
        self.assertIn("● Medium risk", self.app.risk_html("medium"))
        self.assertIn("✓ Low risk", self.app.risk_html("low"))

    def test_code_row_html_includes_tag_code_and_rendered_helpers(self):
        code = {
            "code": "99214",
            "desc": "E&M, established patient – moderate medical decision making",
            "note": "Most common audit target.",
            "risk": "high",
            "confidence": 83,
        }
        html = self.app.code_row_html(code, "cpt")

        self.assertIn("tag-cpt", html)
        self.assertIn("99214", html)
        self.assertIn("Most common audit target.", html)
        self.assertIn("⚠ High risk", html)
        self.assertIn("conf-high", html)

    def test_generate_query_letter_returns_empty_when_no_icd10_codes(self):
        letter = self.app.generate_query_letter([], [], "snippet")
        self.assertEqual(letter, "")

    def test_generate_query_letter_includes_only_medium_high_risk_issues(self):
        icd10_codes = [
            {"code": "E11.65", "risk": "high", "comp": "Provider must document hyperglycemia explicitly."},
            {"code": "I10", "risk": "low", "comp": "Document BP readings and medication compliance."},
        ]
        cpt_codes = [
            {"code": "99214", "risk": "high", "comp": "Document MDM elements clearly."},
            {"code": "83036", "risk": "low", "comp": "Document result value."},
        ]

        letter = self.app.generate_query_letter(icd10_codes, cpt_codes, "snippet")

        self.assertIn("Date:", letter)
        self.assertIn("codes for assignment: E11.65, I10", letter)
        self.assertIn("• E11.65 – Provider must document hyperglycemia explicitly.", letter)
        self.assertIn("• 99214 – Document MDM elements clearly.", letter)
        self.assertNotIn("• I10 –", letter)
        self.assertNotIn("• 83036 –", letter)

    def test_generate_query_letter_uses_fallback_when_no_risk_issues(self):
        icd10_codes = [{"code": "I10", "risk": "low", "comp": "Document BP readings."}]
        letter = self.app.generate_query_letter(icd10_codes, [], "snippet")

        self.assertIn(
            "• Please confirm all diagnoses and procedures documented above.",
            letter,
        )


if __name__ == "__main__":
    unittest.main()
