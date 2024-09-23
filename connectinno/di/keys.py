from connectinno.infra.cache.keys import KeysGeneratorBase, prefixed_key


class KeysGenerator(KeysGeneratorBase):
    @prefixed_key
    def dataset_info(self, dataset_id: str):
        return self.sep.join(['dataset-info', dataset_id])

    @prefixed_key
    def file_lock(self, location: str, server_name: str):
        return self.sep.join(['file-lock', location, server_name])
