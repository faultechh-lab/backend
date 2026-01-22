from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from .models import (
    Category,
    Brand,
    Model,
    Parameter,
    ParameterImage,
    FaultCodes,
    SparePartImage,
    BoilerRepairGuide,
    BoilerPart,
    BoilerPartImage,
    SparePartsDefinitions,
    SparePartsDefinitionsImage,
    BoilerWorkingPrinciple,
    BoilerCardRepair,
    BoilerCardRepairImage,
    BoilerBoardRepairer,
    InstrumentUsage,
    Video,
    RoomTermostat,
    RoomTermostatImage,
    FavoriteBrand,
    FavoriteModel,
    FavoriteFaultCode
)


class FaultCodesResource(resources.ModelResource):
    class Meta:
        model = FaultCodes
        skip_diff = True  # Diff hesaplamayı atla (Hızlandırır)

class ChildCategoryInline(admin.TabularInline):  # veya admin.StackedInline
    model = Category
    fk_name = "parent"
    extra = 1

class CategoryAdmin(ImportExportModelAdmin):
    list_display = ("id","name", "parent", "active", "children_count_display", "has_children","type")
    list_filter = ("active",)
    search_fields = ("name",)
    autocomplete_fields = ("parent",)
    

    def children_count_display(self, obj):
        return obj.children.count()
    children_count_display.short_description = "Alt Kategori Sayısı"

    def has_children(self, obj):
        return obj.children.exists()
    has_children.boolean = True

class BrandAdmin(ImportExportModelAdmin):
    list_display = ("name", "category", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)
    autocomplete_fields = ("category",)

class ModelAdmin_(ImportExportModelAdmin):
    list_display = ("name",'id', "category", "brand", "active")
    list_filter = ("category", "brand", "active")
    search_fields = ("name",)
    autocomplete_fields = ("category", "brand")

class SparePartImageInline(admin.TabularInline):
    model = SparePartImage
    extra = 1
