from datetime import date
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    def test_demo_filters_and_empty_result(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.run(timeout=30)
        self.assertFalse(app.exception)
        app.date_input[0].set_value(date(2026, 10, 11)).run()
        self.assertEqual([metric.value for metric in app.metric], ["10", "6", "4", "1"])
        app.selectbox[1].select("Próximos 7 días").run()
        self.assertEqual(len(app.dataframe[-1].value), 3)
        app.text_input[0].set_value("mantenimiento").run()
        self.assertEqual(len(app.dataframe[-1].value), 1)
        app.text_input[0].set_value("inexistente").run()
        self.assertTrue(any("No hay expedientes" in message.value for message in app.warning))
        self.assertFalse(app.exception)

    def test_upload_mode_requires_a_file(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.run(timeout=30)
        app.checkbox[0].uncheck().run()
        self.assertTrue(any("Selecciona un archivo" in message.value for message in app.warning))
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
