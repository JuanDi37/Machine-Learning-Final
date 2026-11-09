"""Generar las fuentes sintéticas de integración; no se usan como resultados reales."""

from pathlib import Path

from tests.fixtures import make_fixture

if __name__ == "__main__":
    make_fixture(Path("data/ci_fixture"))
    print("NOTA: datos sintéticos para CI; no representan las ventas del supermercado.")
