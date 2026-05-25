import unittest

from medcode_validator_pipeline import MedCodeValidatorPipeline


class TestMedCodeValidatorPipeline(unittest.TestCase):
    def test_negated_mi_is_excluded_and_gerd_confirmed(self) -> None:
        pipeline = MedCodeValidatorPipeline()
        payload = {
            "clinical_text": (
                "Chief Complaint: Chest pain. "
                "History of Present Illness: Myocardial infarction ruled out. "
                "Discharge Assessment/Plan: Treated for acute GERD. "
                "Final disposition: Stable for discharge."
            )
        }

        result = pipeline.run(payload)

        confirmed_codes = {item["code"] for item in result["confirmed_diagnoses"]}
        excluded_concepts = {item["concept"].lower() for item in result["negated_or_excluded_concepts"]}

        self.assertIn("K21.9", confirmed_codes)
        self.assertNotIn("I21.19", confirmed_codes)
        self.assertIn("acute myocardial infarction", excluded_concepts)


if __name__ == "__main__":
    unittest.main()
