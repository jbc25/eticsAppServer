import json

from django.core.management.base import BaseCommand

from currency.models.entity import Entity


class Command(BaseCommand):
    help = 'Export entities profile and etics data to a json file'

    def add_arguments(self, parser):

        parser.add_argument('jsonfile', type=str, help='Indicates the JSON file to export entities')

    def list_categories(entity):
        entity.cate

    def handle(self, *args, **options):

        jsonfile = options['jsonfile']

        entities = Entity.objects.all()

        data = []
        for entity in entities:

            data.append({
                'name': entity.name,
                'email': entity.email,
                'description': entity.description,
                'short_description': entity.short_description,
                'address': entity.address,
                'latitude': entity.latitude,
                'longitude': entity.longitude,
                'categories': list(map(lambda cat: cat.name, entity.categories.all())),
                'bonus_percent_general': entity.bonus_percent_general,
                'bonus_percent_entity': entity.bonus_percent_entity,
                'max_percent_payment': entity.max_percent_payment,
                'facebook_link': entity.facebook_link,
                'twitter_link': entity.twitter_link,
                'instagram_link': entity.instagram_link,
                'telegram_link': entity.telegram_link,
                'webpage_link': entity.webpage_link,

            })

        with open(jsonfile, 'w') as f:
            json_entities = json.dumps(data)
            f.write(json_entities)
            f.close()

