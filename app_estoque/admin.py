from django.contrib import admin
from .models import Item, Retirada, ItemRetirado

admin.site.register(Item)
admin.site.register(Retirada)
admin.site.register(ItemRetirado)