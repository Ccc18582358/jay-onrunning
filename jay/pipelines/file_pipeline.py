import json

from jay.pipelines.base_pipeline import BasePipeline
from jay.utils import dump2file


class FilePipeline(BasePipeline):
    def process_item(self, item, spider):
        folder_name = self.settings.get('OUT_FOLDER')
        # if not os.path.exists(out_folder):
        #     os.mkdir(out_folder)
        file_name = 'test_out_{}_{}-{}_{}.json'.format(
            item['trace']['crawlid'], item['trace']['bucket_position'], item['trace']['scu_position_in_bucket'],
            item['items'][0]['item_id']
        )

        dump2file(file_name, json.dumps(dict(item), indent=4), folder_name)
        return item
