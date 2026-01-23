from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets

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
    image = fields.Field(column_name='image', attribute='image', widget=widgets.CharWidget())
    
    # Çeviri alanlarını açıkça tanımla
    code_tr = fields.Field(column_name='code_tr', attribute='code_tr')
    code_en = fields.Field(column_name='code_en', attribute='code_en')
    code_de = fields.Field(column_name='code_de', attribute='code_de')
    code_ru = fields.Field(column_name='code_ru', attribute='code_ru')
    code_es = fields.Field(column_name='code_es', attribute='code_es')
    code_it = fields.Field(column_name='code_it', attribute='code_it')
    code_fr = fields.Field(column_name='code_fr', attribute='code_fr')
    code_ar = fields.Field(column_name='code_ar', attribute='code_ar')
    
    fault_description_tr = fields.Field(column_name='fault_description_tr', attribute='fault_description_tr')
    fault_description_en = fields.Field(column_name='fault_description_en', attribute='fault_description_en')
    fault_description_de = fields.Field(column_name='fault_description_de', attribute='fault_description_de')
    fault_description_ru = fields.Field(column_name='fault_description_ru', attribute='fault_description_ru')
    fault_description_es = fields.Field(column_name='fault_description_es', attribute='fault_description_es')
    fault_description_it = fields.Field(column_name='fault_description_it', attribute='fault_description_it')
    fault_description_fr = fields.Field(column_name='fault_description_fr', attribute='fault_description_fr')
    fault_description_ar = fields.Field(column_name='fault_description_ar', attribute='fault_description_ar')

    class Meta:
        model = FaultCodes
        skip_diff = True  # Diff hesaplamayı atla (Hızlandırır)
        # Tüm alanları (çeviriler dahil) açıkça belirtiyoruz
        fields = (
            'id', 'category', 'brand', 'model', 'active', 'image',
            'code', 
            'code_tr', 'code_en', 'code_de', 'code_ru', 'code_es', 'code_it', 'code_fr', 'code_ar',
            'fault_description', 
            'fault_description_tr', 'fault_description_en', 'fault_description_de', 'fault_description_ru', 'fault_description_es', 'fault_description_it', 'fault_description_fr', 'fault_description_ar'
        )
        export_order = (
            'id', 'category', 'brand', 'model', 'active', 'image',
            'code', 
            'code_tr', 'code_en', 'code_de', 'code_ru', 'code_es', 'code_it', 'code_fr', 'code_ar',
            'fault_description', 
            'fault_description_tr', 'fault_description_en', 'fault_description_de', 'fault_description_ru', 'fault_description_es', 'fault_description_it', 'fault_description_fr', 'fault_description_ar'
        )


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

class FaultCodesAdmin(ImportExportModelAdmin):
    resource_class = FaultCodesResource
    list_display = ("code", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("code", "fault_description", "brand__name", "model__name", "category__name")
    autocomplete_fields = ("category", "brand", "model")
    inlines = [SparePartImageInline]

class ParameterImageInline(admin.TabularInline):
    model = ParameterImage
    extra = 1

class ParameterAdmin(ImportExportModelAdmin):
    list_display = ("name", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("name", "description")
    autocomplete_fields = ("category", "brand", "model")
    inlines = [ParameterImageInline]

class BoilerCardRepairImageInline(admin.TabularInline):
    model = BoilerCardRepairImage
    extra = 1

class BoilerCardRepairAdmin(ImportExportModelAdmin):
    list_display = ("title", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("title", "description")
    autocomplete_fields = ("category", "brand", "model")
    inlines = [BoilerCardRepairImageInline]

class BoilerRepairGuideAdmin(ImportExportModelAdmin):
    list_display = ("__str__", "active",'title')
    list_filter = ("active",)
    search_fields = ("title",)

class BoilerPartImageInline(admin.TabularInline):
    model = BoilerPartImage
    extra = 1

class BoilerPartAdmin(ImportExportModelAdmin):
    list_display = ("name", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("name",)
    autocomplete_fields = ("category", "brand", "model")
    inlines = [BoilerPartImageInline]


class SparePartsDefinitionsImageInline(admin.TabularInline):
    model = SparePartsDefinitionsImage
    extra = 1

class SparePartsDefinitionsAdmin(ImportExportModelAdmin):
    list_display = ("name", "active")
    list_filter = ("active",)
    search_fields = ("name",)
    inlines = [SparePartsDefinitionsImageInline]

class BoilerWorkingPrincipleAdmin(ImportExportModelAdmin):
    list_display = ("title", "active")
    list_filter = ("active",)
    search_fields = ("title", "description")

class BoilerBoardRepairerAdmin(ImportExportModelAdmin):
    list_display = ("name", "business_type", "city", "phone_number", "active")
    list_filter = ("business_type", "city", "active")
    search_fields = ("name", "address", "phone_number", "email", "website")

class InstrumentUsageAdmin(ImportExportModelAdmin):
    list_display = ("__str__", "active")
    list_filter = ("active",)
    search_fields = ("content",)

class VideoAdmin(ImportExportModelAdmin):
    list_display = ("title", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("title", "description")
    autocomplete_fields = ("category", "brand", "model")

class RoomTermostatImageInline(admin.TabularInline):
    model = RoomTermostatImage
    extra = 1

    
class RoomTermostatAdmin(ImportExportModelAdmin):
    list_display = ("title", "active")
    list_filter = ("active",)
    search_fields = ("title", "description")
    inlines = [RoomTermostatImageInline]

class FavoriteBrandAdmin(ImportExportModelAdmin):
    list_display = ("user", "brand")
    list_filter = ("user", "brand")
    search_fields = ("user__username", "brand__name")
    

class FavoriteModelAdmin(ImportExportModelAdmin):
    list_display = ("user", "model")
    list_filter = ("user", "model")
    search_fields = ("user__username", "model__name")

class FavoriteFaultCodeAdmin(ImportExportModelAdmin):
    list_display = ("user", "fault")
    list_filter = ("user", "fault")
    search_fields = ("user__username", "fault__code")
    


admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Model, ModelAdmin_)
admin.site.register(FaultCodes, FaultCodesAdmin)
admin.site.register(Parameter, ParameterAdmin)
admin.site.register(BoilerRepairGuide, BoilerRepairGuideAdmin)
admin.site.register(BoilerPart, BoilerPartAdmin)
admin.site.register(SparePartsDefinitions, SparePartsDefinitionsAdmin)
admin.site.register(BoilerWorkingPrinciple, BoilerWorkingPrincipleAdmin)
admin.site.register(BoilerCardRepair, BoilerCardRepairAdmin)
admin.site.register(BoilerBoardRepairer, BoilerBoardRepairerAdmin)
admin.site.register(InstrumentUsage, InstrumentUsageAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(RoomTermostat, RoomTermostatAdmin)
admin.site.register(FavoriteBrand, FavoriteBrandAdmin)
admin.site.register(FavoriteModel, FavoriteModelAdmin)
admin.site.register(FavoriteFaultCode, FavoriteFaultCodeAdmin)
