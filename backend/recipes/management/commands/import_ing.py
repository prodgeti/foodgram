import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient

# class Command(BaseCommand):
#     """Команда импорта ингридиентов в базу данных."""
#     help = 'Импорт ингридиентов из файла json'

#     BASE_DIR = settings.BASE_DIR

#     def handle(self, *args, **options):
#         try:
#             path = self.BASE_DIR / 'data/ingredients.json'
#             with open(path, 'r', encoding='utf-8-sig') as file:
#                 data = json.load(file)
#                 for item in data:
#                     Ingredient.objects.get_or_create(**item)
#         except CommandError as error:
#             raise CommandError from error

#         self.stdout.write(self.style.SUCCESS('Данные загружены'))
class Command(BaseCommand):
    """Команда для импорта ингредиентов из JSON-файла в базу данных."""
    help = 'Импортирует ингредиенты из указанного JSON-файла'

    def handle(self, *args, **options):
        file_path = Path(settings.BASE_DIR) / 'data' / 'ingredients.json'

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                ingredients = json.load(file)

            for ingredient_data in ingredients:
                Ingredient.objects.get_or_create(
                    name=ingredient_data['name'],
                    defaults={
                        'measurement_unit': ingredient_data['measurement_unit']
                    }
                )

            self.stdout.write(self.style.SUCCESS('Данные успешно загружены'))

        except FileNotFoundError:
            raise CommandError(f'Файл по пути {file_path} не найден.')
        except json.JSONDecodeError:
            raise CommandError('Ошибка при чтении JSON-файла.')
        except Exception as e:
            raise CommandError(f'Произошла ошибка: {e}')
