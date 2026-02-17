from celery_once_task.utils import generate_lock_key


class TestGenerateLockKey:
    def test_same_args_same_key(self):
        key1 = generate_lock_key("myapp.tasks.foo", (1, 2), {"a": "b"}, "queue")
        key2 = generate_lock_key("myapp.tasks.foo", (1, 2), {"a": "b"}, "queue")
        assert key1 == key2

    def test_different_args_different_key(self):
        key1 = generate_lock_key("myapp.tasks.foo", (1,), {}, "queue")
        key2 = generate_lock_key("myapp.tasks.foo", (2,), {}, "queue")
        assert key1 != key2

    def test_different_lock_type_different_key(self):
        key1 = generate_lock_key("myapp.tasks.foo", (1,), {}, "queue")
        key2 = generate_lock_key("myapp.tasks.foo", (1,), {}, "running")
        assert key1 != key2

    def test_key_format(self):
        key = generate_lock_key("myapp.tasks.foo", (1,), {}, "queue")
        assert key.startswith("once_task:myapp.tasks.foo:")
        assert key.endswith(":queue")

    def test_no_lock_type(self):
        key = generate_lock_key("myapp.tasks.foo", (1,), {})
        assert not key.endswith(":")

    def test_none_args(self):
        key1 = generate_lock_key("myapp.tasks.foo", None, None, "queue")
        key2 = generate_lock_key("myapp.tasks.foo", (), {}, "queue")
        assert key1 == key2

    def test_list_args_treated_as_tuple(self):
        key1 = generate_lock_key("myapp.tasks.foo", [1, 2], {}, "queue")
        key2 = generate_lock_key("myapp.tasks.foo", (1, 2), {}, "queue")
        assert key1 == key2

    def test_kwargs_order_independent(self):
        key1 = generate_lock_key("myapp.tasks.foo", (), {"a": 1, "b": 2}, "queue")
        key2 = generate_lock_key("myapp.tasks.foo", (), {"b": 2, "a": 1}, "queue")
        assert key1 == key2
