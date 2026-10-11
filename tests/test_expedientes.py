from datetime import date, datetime
from io import BytesIO
from pathlib import Path
import unittest

from expedientes import export_csv, filter_records, read_csv, read_excel

HEADER = "numero,asunto,estado,fecha_ingreso,fecha_vencimiento\n"


def load(body):
    return read_csv((HEADER + body).encode("utf-8"))


class ImportTests(unittest.TestCase):
    def test_demo_accepts_six_and_reports_four_rejected_rows(self):
        content = (Path(__file__).resolve().parents[1] / "data/expedientes_demo.csv").read_bytes()
        result = read_csv(content)
        self.assertEqual((result.total_filas, len(result.expedientes), len(result.incidencias)), (10, 6, 4))
        self.assertEqual([item.fila for item in result.incidencias], [8, 9, 10, 11])

    def test_duplicate_numbers_ignore_case_and_spaces(self):
        result = load("A-1,Uno,pendiente,2026-01-01,2026-02-01\n a-1 ,Dos,pendiente,2026-01-01,2026-02-01\n")
        self.assertEqual(len(result.expedientes), 1)
        self.assertIn("duplicado", result.incidencias[0].detalle)

    def test_invalid_first_row_does_not_block_corrected_record(self):
        result = load("A-1,,pendiente,2026-01-01,2026-02-01\nA-1,Corregido,pendiente,2026-01-01,2026-02-01\n")
        self.assertEqual(len(result.expedientes), 1)

    def test_rejects_impossible_dates_and_reversed_periods(self):
        for start, end in [("2026-02-30", "2026-03-01"), ("2026-03-01", "2026-02-01"), ("01/02/2026", "2026-03-01")]:
            with self.subTest(start=start, end=end):
                result = load(f"A,Uno,pendiente,{start},{end}\n")
                self.assertFalse(result.expedientes)
                self.assertEqual(len(result.incidencias), 1)

    def test_requires_columns_and_unique_headers(self):
        for content in (b"numero,asunto\nA,Uno", (HEADER.replace("asunto", "numero")).encode()):
            with self.assertRaises(ValueError):
                read_csv(content)

    def test_semicolon_bom_blank_lines_and_accents(self):
        content = "\ufeff" + HEADER.replace(",", ";") + "A;Revisión;EN PROCESO;2026-01-01;2026-02-01\n\n"
        result = read_csv(content.encode())
        self.assertEqual(result.total_filas, 1)
        self.assertEqual(result.expedientes[0].estado, "en proceso")

    def test_rejects_extra_cells(self):
        result = load("A,Uno,pendiente,2026-01-01,2026-02-01,extra\n")
        self.assertFalse(result.expedientes)
        self.assertEqual(result.incidencias[0].fila, 2)

    def test_excel_accepts_native_dates(self):
        from openpyxl import Workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(HEADER.strip().split(","))
        sheet.append(["X-1", "Prueba Excel", "pendiente", datetime(2026, 1, 1), datetime(2026, 2, 1)])
        content = BytesIO()
        workbook.save(content)
        result = read_excel(content.getvalue())
        self.assertEqual(result.expedientes[0].fecha_vencimiento, date(2026, 2, 1))

    def test_export_neutralizes_spreadsheet_formulas(self):
        result = load("A,=1+1,pendiente,2026-01-01,2026-02-01\n")
        self.assertIn("'=1+1", export_csv(result.expedientes).decode("utf-8-sig"))


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.records = load(
            "A,Revisión,pendiente,2026-01-01,2026-01-09\n"
            "B,Revisión final,finalizado,2026-01-01,2026-01-08\n"
            "C,Informe,en proceso,2026-01-01,2026-01-10\n"
            "D,Informe,observado,2026-01-01,2026-01-17\n"
            "E,Informe,pendiente,2026-01-01,2026-01-18\n"
        ).expedientes
        self.today = date(2026, 1, 10)

    def test_finalized_and_due_today_are_not_overdue(self):
        self.assertEqual([item.numero for item in filter_records(self.records, due="Vencidos", today=self.today)], ["A"])

    def test_next_seven_days_include_today_and_seventh_day(self):
        self.assertEqual([item.numero for item in filter_records(self.records, due="Próximos 7 días", today=self.today)], ["C", "D"])

    def test_combined_filters_and_accent_insensitive_search(self):
        found = filter_records(self.records, query="revision", state="pendiente", today=self.today)
        self.assertEqual([item.numero for item in found], ["A"])
        self.assertEqual(filter_records(self.records, query="inexistente"), [])


if __name__ == "__main__":
    unittest.main()
