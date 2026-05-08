import importlib.util
from pathlib import Path


def _load_validator_module():
    path = Path("scripts/validate-mobile-stack.py")
    spec = importlib.util.spec_from_file_location("validate_mobile_stack", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = _load_validator_module()
REQUIRED_ENDPOINTS = validator.REQUIRED_ENDPOINTS
validate = validator.validate


def _minimal_config():
    return {
        "stack_name": "hestia-mobile",
        "repos": {
            "hestia-mobile": {
                "path": "/tmp/hestia-mobile",
                "remote": "git@github.com:Code4me2/hestia-mobile.git",
                "branch": "main",
                "owner": "integration",
            }
        },
        "endpoints": {
            "orchestrator_health": "http://tiny-emerson:8000/health",
            "orchestrator_models": "http://tiny-emerson:8000/v1/models",
            "unmute_health": "http://tiny-emerson/v1/health",
            "unmute_realtime": "ws://tiny-emerson:80/v1/realtime",
            "bridge_health": "http://127.0.0.1:8765/health",
            "bridge_mobile_capabilities": "http://127.0.0.1:8765/mobile_capabilities",
            "bridge_mobile_state": "http://127.0.0.1:8765/mobile_state",
        },
        "phone": {
            "ai_socket": "$XDG_RUNTIME_DIR/hestia-shell/ai.sock",
            "assistant_socket": "$XDG_RUNTIME_DIR/hestia-shell/assistant.sock",
            "voice_service": "hestia-unmute-voice.service",
            "bridge_service": "hestia-ai-bridge.service",
        },
        "health_policy": {
            "unmute_required_true": [],
            "bridge_required_true": [],
        },
    }


def test_bridge_mobile_capabilities_and_state_are_required_endpoints():
    assert "bridge_mobile_capabilities" in REQUIRED_ENDPOINTS
    assert "bridge_mobile_state" in REQUIRED_ENDPOINTS


def test_validate_accepts_bridge_mobile_capabilities_endpoint():
    assert validate(_minimal_config()) == []


def test_validate_rejects_missing_bridge_mobile_capabilities_endpoint():
    config = _minimal_config()
    del config["endpoints"]["bridge_mobile_capabilities"]

    assert "missing endpoint: bridge_mobile_capabilities" in validate(config)


def test_validate_rejects_missing_bridge_mobile_state_endpoint():
    config = _minimal_config()
    del config["endpoints"]["bridge_mobile_state"]

    assert "missing endpoint: bridge_mobile_state" in validate(config)


def test_validate_requires_phone_bridge_endpoints_to_stay_loopback():
    config = _minimal_config()
    config["endpoints"]["bridge_mobile_capabilities"] = "http://tiny-emerson:8765/mobile_capabilities"
    config["endpoints"]["bridge_mobile_state"] = "http://100.64.0.2:8765/mobile_state"

    errors = validate(config)
    assert "bridge_mobile_capabilities must use loopback host" in errors
    assert "bridge_mobile_state must use loopback host" in errors
