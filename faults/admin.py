from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
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



class ChildCategoryInline(admin.TabularInline):  # veya admin.StackedInline
    model = Category
    fk_name = "parent"
    extra = 1

class CategoryAdmin(admin.ModelAdmin):
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

class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)
    autocomplete_fields = ("category",)

class ModelAdmin_(admin.ModelAdmin):
    list_display = ("name",'id', "category", "brand", "active")
    list_filter = ("category", "brand", "active")
    search_fields = ("name",)
    autocomplete_fields = ("category", "brand")

class SparePartImageInline(admin.TabularInline):
    model = SparePartImage
    extra = 1

class FaultCodesAdmin(admin.ModelAdmin):
    list_display = ("code", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("code", "fault_description", )
    autocomplete_fields = ("category", "brand", "model")
    inlines = [SparePartImageInline]

class ParameterImageInline(admin.TabularInline):
    model = ParameterImage
    extra = 1

class ParameterAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("name", "description")
    autocomplete_fields = ("category", "brand", "model")
    inlines = [ParameterImageInline]

class BoilerCardRepairImageInline(admin.TabularInline):
    model = BoilerCardRepairImage
    extra = 1

class BoilerCardRepairAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("title", "description")
    autocomplete_fields = ("category", "brand", "model")
    inlines = [BoilerCardRepairImageInline]

class BoilerRepairGuideAdmin(admin.ModelAdmin):
    list_display = ("__str__", "active",'title')
    list_filter = ("active",)
    search_fields = ("title",)

class BoilerPartImageInline(admin.TabularInline):
    model = BoilerPartImage
    extra = 1

class BoilerPartAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("name",)
    autocomplete_fields = ("category", "brand", "model")
    inlines = [BoilerPartImageInline]


class SparePartsDefinitionsImageInline(admin.TabularInline):
    model = SparePartsDefinitionsImage
    extra = 1

class SparePartsDefinitionsAdmin(admin.ModelAdmin):
    list_display = ("name", "active")
    list_filter = ("active",)
    search_fields = ("name",)
    inlines = [SparePartsDefinitionsImageInline]

class BoilerWorkingPrincipleAdmin(admin.ModelAdmin):
    list_display = ("title", "active")
    list_filter = ("active",)
    search_fields = ("title", "description")

class BoilerBoardRepairerAdmin(admin.ModelAdmin):
    list_display = ("name", "business_type", "city", "phone_number", "active")
    list_filter = ("business_type", "city", "active")
    search_fields = ("name", "address", "phone_number", "email", "website")

class InstrumentUsageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "active")
    list_filter = ("active",)
    search_fields = ("content",)

class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "brand", "model", "active")
    list_filter = ("category", "brand", "model", "active")
    search_fields = ("title", "description")
    autocomplete_fields = ("category", "brand", "model")

class RoomTermostatImageInline(admin.TabularInline):
    model = RoomTermostatImage
    extra = 1

    
class RoomTermostatAdmin(admin.ModelAdmin):
    list_display = ("title", "active")
    list_filter = ("active",)
    search_fields = ("title", "description")
    inlines = [RoomTermostatImageInline]

class FavoriteBrandAdmin(admin.ModelAdmin):
    list_display = ("user", "brand")
    list_filter = ("user", "brand")
    search_fields = ("user__username", "brand__name")
    

class FavoriteModelAdmin(admin.ModelAdmin):
    list_display = ("user", "model")
    list_filter = ("user", "model")
    search_fields = ("user__username", "model__name")

class FavoriteFaultCodeAdmin(admin.ModelAdmin):
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

