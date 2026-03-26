# tests/test_tasks.py

import pytest
from jailbreak_arena.tasks import (
    get_all_tasks,
    get_task_by_id,
    get_tasks_by_difficulty,
    get_tasks_by_category,
    get_seed_prompt,
    Task,
    TASKS,
)


class TestTaskCatalog:

    def test_total_task_count(self):
        """Should have exactly 12 tasks."""
        tasks = get_all_tasks()
        assert len(tasks) == 20

    def test_all_tasks_have_required_fields(self):
        """Every task must have all required fields populated."""
        for task in get_all_tasks():
            assert task.task_id,         f"{task.task_id} missing task_id"
            assert task.name,            f"{task.task_id} missing name"
            assert task.description,     f"{task.task_id} missing description"
            assert task.attack_type,     f"{task.task_id} missing attack_type"
            assert task.category,        f"{task.task_id} missing category"
            assert task.difficulty,      f"{task.task_id} missing difficulty"
            assert task.seed_prompts,    f"{task.task_id} missing seed_prompts"
            assert task.success_criteria,f"{task.task_id} missing success_criteria"
            assert task.canonical_seed,  f"{task.task_id} missing canonical_seed"

    def test_all_task_ids_unique(self):
        """No duplicate task IDs."""
        ids = [t.task_id for t in get_all_tasks()]
        assert len(ids) == len(set(ids))

    def test_difficulty_values_valid(self):
        """All difficulties must be easy, medium, or hard."""
        valid = {"easy", "medium", "hard"}
        for task in get_all_tasks():
            assert task.difficulty in valid, \
                f"{task.task_id} has invalid difficulty: {task.difficulty}"

    def test_each_task_has_minimum_seed_prompts(self):
        """Each task should have at least 3 seed prompts."""
        for task in get_all_tasks():
            assert len(task.seed_prompts) >= 3, \
                f"{task.task_id} has fewer than 3 seed prompts"

    def test_each_task_has_minimum_success_criteria(self):
        """Each task should have at least 3 success criteria."""
        for task in get_all_tasks():
            assert len(task.success_criteria) >= 3, \
                f"{task.task_id} has fewer than 3 success criteria"


class TestTaskLookup:

    def test_get_task_by_valid_id(self):
        task = get_task_by_id("task_001")
        assert task.task_id == "task_001"
        assert task.name == "Role Hijacking"

    def test_get_task_by_invalid_id_raises(self):
        with pytest.raises(ValueError):
            get_task_by_id("task_999")

    def test_get_tasks_by_difficulty_easy(self):
        easy = get_tasks_by_difficulty("easy")
        assert len(easy) >= 1
        assert all(t.difficulty == "easy" for t in easy)

    def test_get_tasks_by_difficulty_hard(self):
        hard = get_tasks_by_difficulty("hard")
        assert len(hard) >= 1
        assert all(t.difficulty == "hard" for t in hard)

    def test_get_tasks_by_category(self):
        cat = get_tasks_by_category("Identity & Role")
        assert len(cat) >= 1
        assert all(t.category == "Identity & Role" for t in cat)

    def test_get_tasks_by_nonexistent_category(self):
        result = get_tasks_by_category("Nonexistent Category")
        assert result == []


class TestSeedPrompts:

    def test_seed_prompt_pool_mode(self):
        """Pool mode returns one of the seed prompts."""
        task = get_task_by_id("task_001")
        seed = get_seed_prompt(task, llm_client=None)
        assert seed in task.seed_prompts

    def test_seed_prompt_is_string(self):
        task = get_task_by_id("task_005")
        seed = get_seed_prompt(task, llm_client=None)
        assert isinstance(seed, str)
        assert len(seed) > 10

    def test_seed_prompt_randomness(self):
        """Multiple calls should not always return the same prompt."""
        task = get_task_by_id("task_001")
        seeds = {get_seed_prompt(task, llm_client=None) for _ in range(20)}
        # With 5 prompts and 20 trials, we expect more than 1 unique result
        assert len(seeds) > 1