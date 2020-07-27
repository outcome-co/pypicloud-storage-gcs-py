from outcome.pypicloud_storage_gcs import hello_word


class TestExample:
    def test_hello_world(self):
        assert hello_word() == 'hello world'
