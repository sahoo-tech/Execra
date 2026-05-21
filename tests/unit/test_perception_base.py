import pytest
from core.perception.base import BasePerceptionEngine

class DummyPerceptionEngine(BasePerceptionEngine):
    def start(self) -> bool:
        super().start()
        self.is_running = True
        return True

    def stop(self) -> bool:
        super().stop()
        self.is_running = False
        return True

    def get_data(self) -> dict:
        super().get_data()
        return {"dummy_key": "dummy_value"}

def test_cannot_instantiate_abstract_class():
    with pytest.raises(TypeError):
        BasePerceptionEngine("abstract_engine")  # type: ignore

def test_concrete_subclass_initialization():
    engine = DummyPerceptionEngine("test_dummy")
    assert engine.name == "test_dummy"
    assert engine.is_running is False

def test_concrete_subclass_methods():
    engine = DummyPerceptionEngine("test_dummy")
    
    assert engine.start() is True
    assert engine.is_running is True
    
    data = engine.get_data()
    assert data == {"dummy_key": "dummy_value"}
    
    status = engine.get_status()
    assert status == {
        "name": "test_dummy",
        "is_running": True
    }
    
    assert engine.stop() is True
    assert engine.is_running is False
    
    status_stopped = engine.get_status()
    assert status_stopped["is_running"] is False
