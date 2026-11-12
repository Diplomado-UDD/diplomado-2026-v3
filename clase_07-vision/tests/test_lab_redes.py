from unittest.mock import MagicMock

import pytest
import torch
import torch.nn.functional as F
from nb import load

NB = "clase_07-lab_redes.ipynb"
MEDIA = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
DESV = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


class TestSeis:
    def f(self, labels):
        return load(
            NB, "seis", fotos=[None] * len(labels), etiquetas=torch.tensor(labels)
        )["seis"]

    def test_happy_first_six(self):
        assert self.f([1, 0] * 8)(1) == [0, 2, 4, 6, 8, 10]

    def test_edge_fewer_than_six(self):
        assert self.f([0, 0, 1])(1) == [2]

    def test_edge_missing_class(self):
        assert self.f([0, 0])(1) == []


class TestVer:
    f = staticmethod(lambda: load(NB, "ver", MEDIA=MEDIA, DESV=DESV)["ver"])

    def test_happy_zero_is_mean_color(self):
        out = self.f()(torch.zeros(3, 2, 2))
        assert out.shape == (2, 2, 3) and torch.allclose(out[0, 0], MEDIA.flatten())

    def test_edge_clamps(self):
        out = self.f()(torch.full((3, 1, 1), 100.0))
        assert out.max() == 1 and out.min() == 1


class TestTapar:
    def ns(self):
        X = torch.randn(2, 3, 224, 224)
        clasificador = lambda x: torch.stack(
            [x.mean(dim=(1, 2, 3)), torch.zeros(len(x))], 1
        )
        ver = load(NB, "ver", MEDIA=MEDIA, DESV=DESV)["ver"]
        return load(
            NB,
            "tapar",
            X=X,
            probar=[1],
            clasificador=clasificador,
            F=F,
            torch=torch,
            plt=MagicMock(
                subplots=MagicMock(return_value=(None, [MagicMock(), MagicMock()]))
            ),
            ver=ver,
        )

    def test_happy_does_not_mutate_dataset(self):
        ns = self.ns()
        before = ns["X"].clone()
        ns["tapar"](0, 10, 10, 50)
        assert torch.equal(ns["X"], before)

    def test_edge_patch_beyond_border(self):
        self.ns()["tapar"](0, 200, 200, 160)  # slicing clips; must not raise

    def test_error_photo_out_of_range(self):
        with pytest.raises(IndexError):
            self.ns()["tapar"](5)


class TestCuerpo:
    """Regression: building `cuerpo` on the GPU must not move `red` with it."""

    def test_red_stays_on_cpu(self):
        import copy

        red = torch.nn.Sequential(
            torch.nn.Conv2d(3, 2, 3), torch.nn.Flatten(), torch.nn.Linear(2, 2)
        )
        ns = load(NB, "cuerpo", red=red, torch=torch, copy=copy, DISPOSITIVO="meta")
        assert next(ns["cuerpo"].parameters()).device.type == "meta"
        assert next(red.parameters()).device.type == "cpu"
