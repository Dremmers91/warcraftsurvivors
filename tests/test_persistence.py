import json

from warcraft_survivors.persistence import SaveStore, class_level


def test_roundtrip_and_backup_recovery(tmp_path):
    path = tmp_path / "save.json"
    save = SaveStore(path)
    save.data["gold"] = 123
    assert save.write()
    save.data["gold"] = 456
    assert save.write()
    assert SaveStore(path).data["gold"] == 456
    path.write_text("broken json")
    recovered = SaveStore(path)
    assert recovered.data["gold"] == 123
    assert "backup" in recovered.notice
    assert recovered.write()
    assert json.loads(path.with_suffix(".bak").read_text())["gold"] == 123


def test_corruption_has_safe_defaults_and_preserves_original(tmp_path):
    path = tmp_path / "save.json"
    path.write_text('{"version":2,')
    save = SaveStore(path)
    assert save.data["gold"] == 0
    assert path.with_suffix(".corrupt").exists()


def test_validation_handles_bad_nested_types_and_caps():
    raw = {
        "version": 1,
        "gold": -3,
        "classes": {"mage": {"xp": 120, "talents": {"might": 900, "haste": 900}}},
        "shared": {"choices": 99},
        "settings": {"sound": "false"},
        "achievements": ["first_blood", "first_blood", {}, "unknown"],
        "stats": [],
    }
    data = SaveStore.validate(raw)
    assert data["gold"] == 0
    assert data["shared"]["choices"] == 1
    assert data["settings"]["sound"] is True
    assert data["classes"]["mage"]["talents"] == {"might": 1}
    assert data["achievements"] == ["first_blood"]
    assert SaveStore.validate({"version": 1, "classes": [], "shared": []})["gold"] == 0


def test_failed_runs_award_progress_and_achievements_only_once(tmp_path):
    save = SaveStore(tmp_path / "save.json")
    first = save.reward_run("mage", 100, 0, 120, False, 10, 0)
    second = save.reward_run("mage", 100, 0, 120, False, 10, 0)
    assert first["class_xp"] > 0 and second["class_xp"] > 0
    assert first["gold"] - second["gold"] == 70
    assert second["achievements"] == []
    assert save.data["stats"]["runs"] == 2


def test_talents_purchase_respec_and_shared_costs(tmp_path):
    save = SaveStore(tmp_path / "save.json")
    save.data["gold"] = 500
    save.data["classes"]["mage"]["xp"] = 360
    assert class_level(360) == 3
    assert save.talent_points("mage") == 2
    assert save.buy_talent("mage", "might")
    assert not save.buy_talent("mage", "signature")
    assert save.buy_talent("mage", "health")
    assert not save.buy_talent("mage", "might")
    assert save.respec("mage")
    assert save.talent_points("mage") == 2 and save.data["gold"] == 440
    assert not save.buy_shared("choices")
    assert save.buy_shared("health")
    assert save.data["gold"] == 375
    assert not save.buy_shared("unknown")


def test_write_failure_is_reported_without_crashing(tmp_path):
    parent_file = tmp_path / "file"
    parent_file.write_text("not a directory")
    save = SaveStore(parent_file / "save.json")
    assert not save.write()
    assert "could not be saved" in save.notice
