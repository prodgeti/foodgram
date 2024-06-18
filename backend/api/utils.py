import os
from io import BytesIO

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def create_shopping_list_pdf(user, ingredients):
    filename = f'{user.username}_shopping_list.pdf'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    pdfmetrics.registerFont(TTFont('LiberationSerif', os.path.join(
        'data', 'LiberationSerif-Regular.ttf'
    )))
    p.setFont('LiberationSerif', 12)

    p.drawString(100, 750, 'Список покупок')
    y = 700

    for ingredient in ingredients:
        p.drawString(
            100,
            y,
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]}) '
            f'- {ingredient["amount"]}'
        )
        y -= 20
        if y < 40:
            p.showPage()
            y = 700
            p.setFont('LiberationSerif', 12)

    p.showPage()
    p.save()

    buffer.seek(0)
    response.write(buffer.read())
    return response
