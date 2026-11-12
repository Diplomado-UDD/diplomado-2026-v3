import base64
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
from nb import load
from PIL import Image
from pydantic import BaseModel, ValidationError

NB = "clase_07-lab_vision.ipynb"


def rut_ns():
    return load(NB, "digito_verificador", "rut_valido")


def factura_cls():
    return load(NB, "Factura", BaseModel=BaseModel)["Factura"]


def make_factura(**over):
    data = {
        "emisor": "X SpA",
        "rut_emisor": "76.086.428-5",
        "numero": 1,
        "fecha": "01-01-2026",
        "neto": 1_000_000,
        "iva": 190_000,
        "total": 1_190_000,
    }
    return factura_cls()(**{**data, **over})


class FakeAPIError(Exception):
    pass


def fake_result(boxes):
    cls, conf, xyxy = zip(*boxes) if boxes else ((), (), ())
    return SimpleNamespace(
        names={0: "person", 5: "bus"},
        boxes=SimpleNamespace(cls=cls, conf=conf, xyxy=xyxy),
        plot=lambda: np.zeros((2, 2, 3)),
    )


class TestBrillo:
    def run(self, cambio):
        plt = MagicMock()
        load(
            NB,
            "brillo",
            np=np,
            plt=plt,
            matriz=np.array([[[0, 128, 250]]], dtype=np.uint8),
        )["brillo"](cambio)
        return plt.imshow.call_args.args[0]

    def test_happy(self):
        assert self.run(5).tolist() == [[[5, 133, 255]]]

    def test_edge_clips_low(self):
        assert self.run(-150).tolist() == [[[0, 0, 100]]]

    def test_keeps_uint8(self):
        assert self.run(0).dtype == np.uint8


class TestConvolucion:
    f = staticmethod(lambda: load(NB, "convolucion", np=np)["convolucion"])

    def test_happy(self):
        out = self.f()(np.ones((5, 5)), np.ones((3, 3)))
        assert out.shape == (3, 3) and (out == 9).all()

    def test_edge_filter_same_size(self):
        assert self.f()(np.arange(9.0).reshape(3, 3), np.ones((3, 3))).shape == (1, 1)

    def test_error_filter_larger(self):
        with pytest.raises(ValueError):
            self.f()(np.ones((2, 2)), np.ones((3, 3)))


class TestProbar:
    def ns(self):
        conv = load(NB, "convolucion", np=np)["convolucion"]
        sobel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
        filtros = {"Bordes verticales": sobel, "Desenfoque": np.ones((3, 3)) / 9}
        gris = np.tile(
            np.arange(5.0)[::-1], (5, 1)
        )  # decreasing ramp -> negative edges
        return load(
            NB,
            "probar",
            np=np,
            plt=MagicMock(),
            filtros=filtros,
            gris=gris,
            convolucion=conv,
        )

    def test_happy_edges_are_absolute(self):
        ns = self.ns()
        ns["probar"]("Bordes verticales")
        assert (ns["plt"].imshow.call_args.args[0] >= 0).all()

    def test_edge_blur_not_absolute(self):
        ns = self.ns()
        ns["probar"]("Desenfoque")
        assert np.allclose(ns["plt"].imshow.call_args.args[0], [[3, 2, 1]] * 3)

    def test_error_unknown_filter(self):
        with pytest.raises(KeyError):
            self.ns()["probar"]("Nada")


class TestDetectar:
    def ns(self, boxes):
        modelo = MagicMock(return_value=[fake_result(boxes)])
        return load(
            NB, "detectar", modelo=modelo, plt=MagicMock(), ASSETS=Path("/assets")
        )

    def test_happy(self):
        ns = self.ns([(0, 0.876, [1.4, 2.6, 3.5, 4.4])])
        assert ns["detectar"]("bus.jpg", 0.3) == [
            {"etiqueta": "person", "confianza": 0.88, "caja": [1, 3, 4, 4]}
        ]
        ns["modelo"].assert_called_once_with(
            Path("/assets/bus.jpg"), conf=0.3, verbose=False
        )

    def test_edge_no_boxes(self):
        assert self.ns([])["detectar"]("x.jpg") == []

    def test_mostrar_false_skips_plot(self):
        ns = self.ns([(5, 0.5, [0, 0, 1, 1])])
        ns["detectar"]("x.jpg", mostrar=False)
        ns["plt"].imshow.assert_not_called()


class TestUmbral:
    def test_happy(self, capsys):
        detectar = MagicMock(return_value=[{"etiqueta": "person", "confianza": 0.9}])
        load(NB, "umbral", detectar=detectar)["umbral"](0.4)
        detectar.assert_called_once_with("zidane.jpg", 0.4)
        assert "reporta 1 objetos" in capsys.readouterr().out

    def test_edge_nothing_detected(self, capsys):
        load(NB, "umbral", detectar=lambda *a: [])["umbral"](0.95)
        assert "reporta 0 objetos" in capsys.readouterr().out


class TestDigitoVerificador:
    def test_happy(self):
        f = rut_ns()["digito_verificador"]
        assert f(76086428) == "5" and f(11111111) == "1"

    def test_edge_k_and_zero(self):
        f = rut_ns()["digito_verificador"]
        assert f(1000005) == "K" and f(1000013) == "0"

    def test_error_negative(self):
        with pytest.raises(ValueError):
            rut_ns()["digito_verificador"](-5)


class TestRutValido:
    def test_happy(self):
        assert rut_ns()["rut_valido"]("76.086.428-5")

    def test_edge_lowercase_k(self):
        assert rut_ns()["rut_valido"]("1.000.005-k")

    def test_invalid_inputs_return_false(self):
        f = rut_ns()["rut_valido"]
        assert not f("76.086.428-3") and not f("abc-5") and not f("")


class TestMiles:
    f = staticmethod(lambda: load(NB, "miles")["miles"])

    def test_happy(self):
        assert self.f()(1_250_000) == "1.250.000"

    def test_edge_small_and_negative(self):
        assert self.f()(0) == "0" and self.f()(-1000) == "-1.000"


class TestCargarEnv:
    def run(self, monkeypatch, cwd):
        calls = []
        monkeypatch.setitem(
            sys.modules, "dotenv", SimpleNamespace(load_dotenv=calls.append)
        )
        monkeypatch.chdir(cwd)
        return load(NB, "cargar_env", Path=Path)["cargar_env"](), calls

    def test_happy_finds_parent(self, monkeypatch, tmp_path):
        (tmp_path / ".env").write_text("X=1")
        (tmp_path / "a" / "b").mkdir(parents=True)
        ok, calls = self.run(monkeypatch, tmp_path / "a" / "b")
        assert ok and calls == [tmp_path.resolve() / ".env"]

    def test_edge_beyond_five_parents(self, monkeypatch, tmp_path):
        (tmp_path / ".env").write_text("X=1")
        deep = tmp_path.joinpath(*"abcdef")
        deep.mkdir(parents=True)
        ok, calls = self.run(monkeypatch, deep)
        assert not ok and calls == []


class TestFactura:
    def test_happy(self):
        assert make_factura().numero == 1

    def test_edge_coerces_numeric_string(self):
        assert make_factura(neto="1000000").neto == 1_000_000

    def test_error_bad_type(self):
        with pytest.raises(ValidationError):
            make_factura(numero="cuatro")


class TestLeerFactura:
    def ns(self, monkeypatch, hay_clave, parsed=None, stop="end_turn", error=None):
        resp = SimpleNamespace(
            stop_reason=stop,
            parsed_output=parsed,
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )
        client = MagicMock()
        client.messages.parse.return_value = resp
        client.messages.parse.side_effect = error
        monkeypatch.setitem(
            sys.modules,
            "anthropic",
            SimpleNamespace(Anthropic=lambda: client, APIError=FakeAPIError),
        )
        ns = load(
            NB,
            "leer_factura",
            "factura_simulada",
            Factura=factura_cls(),
            hay_clave=hay_clave,
            io=io,
            base64=base64,
            RUT_EMISOR="76.086.428-5",
            NETO=1000,
            IVA=190,
            TOTAL=1190,
        )
        return ns["leer_factura"], client

    def test_simulated_has_planted_error(self, monkeypatch):
        f, client = self.ns(monkeypatch, False)
        assert f(None).total == 190 and not client.messages.parse.called

    def test_happy_api(self, monkeypatch):
        expected = make_factura()
        f, client = self.ns(monkeypatch, True, parsed=expected)
        assert f(Image.new("RGB", (4, 4))) is expected
        kw = client.messages.parse.call_args.kwargs
        assert (
            kw["model"] == "claude-haiku-5-5"
            and kw["output_format"].__name__ == "Factura"
        )

    def test_error_refusal(self, monkeypatch):
        f, _ = self.ns(monkeypatch, True, parsed=None, stop="refusal")
        with pytest.raises(RuntimeError):
            f(Image.new("RGB", (4, 4)))

    def test_error_api_falls_back_to_simulated(self, monkeypatch, capsys):
        f, _ = self.ns(monkeypatch, True, error=FakeAPIError("down"))
        assert f(Image.new("RGB", (4, 4))).total == 190
        assert "modo simulado" in capsys.readouterr().out


class TestIva:
    f = staticmethod(lambda: load(NB, "iva")["iva"])

    def test_happy(self):
        assert self.f()(1_250_000) == 237_500

    def test_edge_half_peso_rounds_up(self):
        assert self.f()(150) == 29  # 28,5: round() would give 28

    def test_edge_zero(self):
        assert self.f()(0) == 0


class TestValidar:
    f = staticmethod(
        lambda: load(NB, "validar", "rut_valido", "digito_verificador", "iva")[
            "validar"
        ]
    )

    def test_happy(self):
        assert self.f()(make_factura())

    def test_total_mismatch(self):
        assert not self.f()(make_factura(total=1_189_000))

    def test_bad_rut(self):
        assert not self.f()(make_factura(rut_emisor="76.086.428-3"))


class TestRevisarZona:
    def run(self, n_personas, aforo, capsys):
        dets = [{"etiqueta": "person"}] * n_personas + [{"etiqueta": "bus"}]
        load(
            NB, "revisar_zona", "AFORO_MAXIMO", detectar=lambda *a, **k: dets, json=json
        )["revisar_zona"]("c.jpg", aforo)
        return json.loads(capsys.readouterr().out.splitlines()[0])

    def test_happy_alert(self, capsys):
        assert self.run(4, 3, capsys) == {
            "camara": "c.jpg",
            "personas": 4,
            "aforo": 3,
            "alerta": True,
        }

    def test_edge_equal_to_limit(self, capsys):
        assert self.run(3, 3, capsys)["alerta"] is False


class TestProbarAforo:
    def test_happy(self):
        revisar = MagicMock()
        load(NB, "probar_aforo", "AFORO_MAXIMO", revisar_zona=revisar)["probar_aforo"](
            2
        )
        assert [c.args for c in revisar.call_args_list] == [
            ("bus.jpg", 2),
            ("zidane.jpg", 2),
        ]

    def test_default_uses_constant(self):
        revisar = MagicMock()
        load(NB, "probar_aforo", "AFORO_MAXIMO", revisar_zona=revisar)["probar_aforo"]()
        assert revisar.call_args_list[0].args[1] == 3


def test_no_env_leak():
    """The notebook must never print or hardcode the API key."""
    src = (Path(__file__).resolve().parents[1] / NB).read_text()
    assert "sk-ant-" not in src and "print(os.environ" not in src
