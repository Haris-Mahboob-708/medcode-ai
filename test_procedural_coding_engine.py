import unittest

from ProceduralCodingEngine import ProceduralCodingEngine


class TestProceduralCodingEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ProceduralCodingEngine()

    def test_dual_code_extraction_with_units(self) -> None:
        note = (
            "Patient received intramuscular injection of 40 mg Depo-Medrol today in clinic. "
            "Drug documented as J2130."
        )
        result = self.engine.extract_procedures(note)
        procedures = {p["code"]: p for p in result["procedures"]}

        self.assertIn("96372", procedures)
        self.assertEqual(procedures["96372"]["type"], "CPT")

        self.assertIn("J2130", procedures)
        self.assertEqual(procedures["J2130"]["type"], "HCPCS_Level_II")
        self.assertEqual(procedures["J2130"]["units"], 2)


if __name__ == "__main__":
    unittest.main()
