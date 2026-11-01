"""Aggregate tweaks must report what they could not restore instead of only logging it."""
import pytest

from backend.tweaks import recommendations_offers, third_party_services, third_party_tasks
from backend.tweaks.base import TweakPartialUndo
from backend.tweaks.recommendations_offers import RecommendationsOffersTweak
from backend.tweaks.third_party_services import ThirdPartyServicesTweak
from backend.tweaks.third_party_tasks import ThirdPartyTasksTweak


def _fail_on(value):
    def write(*args):
        if value in args:
            raise OSError("negado")
    return write


def test_services_report_the_ones_not_restored(monkeypatch):
    monkeypatch.setattr(third_party_services, "set_start_type", _fail_on("B"))
    monkeypatch.setattr(third_party_services, "start_service", lambda name: None)
    items = [{"name": "A", "start_type": "auto"}, {"name": "B", "start_type": "auto"}]

    with pytest.raises(TweakPartialUndo) as exc_info:
        ThirdPartyServicesTweak().undo(items)

    assert exc_info.value.remaining == items[1:]


def test_tasks_report_the_ones_not_restored(monkeypatch):
    monkeypatch.setattr(third_party_tasks, "set_task_enabled", _fail_on(r"\B"))
    items = [{"task": r"\A"}, {"task": r"\B"}]

    with pytest.raises(TweakPartialUndo) as exc_info:
        ThirdPartyTasksTweak().undo(items)

    assert exc_info.value.remaining == items[1:]
    assert r"\B" in str(exc_info.value)


def test_recommendations_report_the_ones_not_restored(monkeypatch):
    monkeypatch.setattr(recommendations_offers, "_write", _fail_on("B"))
    items = [{"path": "p", "name": "A", "previous": 1}, {"path": "p", "name": "B", "previous": 1}]

    with pytest.raises(TweakPartialUndo) as exc_info:
        RecommendationsOffersTweak().undo(items)

    assert exc_info.value.remaining == items[1:]
