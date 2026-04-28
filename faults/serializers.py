from rest_framework import serializers
from .models import (
    
    Category,
    Brand,
    Model,
    FaultCodes,
    SparePartImage,
    Parameter,
    ParameterImage,
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




class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    has_children = serializers.SerializerMethodField()
    brand_count = serializers.SerializerMethodField()
    child_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", 'type','image','active', "parent", "children","has_children", "brand_count", "child_count",)
    def get_children(self, obj)
        return CategorySerializer(obj.children.filter(parent=obj), many=True).data
    def get_has_children(self, obj):
        return obj.children.exists()
    def get_brand_count(self, obj):
        return obj.brands.filter(active=True).count()
    def get_child_count(self, obj):
        return obj.children.filter(active=True).count()


class BrandSerializer(serializers.ModelSerializer):
    category_name=serializers.CharField(source='category.name')
    model_count = serializers.SerializerMethodField()
    class Meta:
        model = Brand
        fields = "__all__"
        extra_fields = ['category_name', 'model_count']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['category_name'] = instance.category.name if instance.category else None
        ret['model_count'] = self.get_model_count(instance)
        return ret

    def get_model_count(self, obj):
        return obj.models.filter(active=True).count()


class ModelSerializer_(serializers.ModelSerializer):
    category_name=serializers.CharField(source='category.name')
    brand_name=serializers.CharField(source='brand.name')
    item_count = serializers.SerializerMethodField()
    class Meta:
        model = Model
        fields = "__all__"
        extra_fields = ['category_name', 'brand_name', 'item_count']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['category_name'] = instance.category.name if instance.category else None
        ret['brand_name'] = instance.brand.name if instance.brand else None
        ret['item_count'] = self.get_item_count(instance)
        return ret

    def get_item_count(self, obj):
        if not obj.category:
            return 0
        cat_type = obj.category.type
        if cat_type == 'Arıza Kodu':
            return obj.fault_codes.filter(active=True).count()
        elif cat_type == 'Parametre':
            return obj.parameters.filter(active=True).count()
        elif cat_type == 'Kombi Kart Tamiri':
            return obj.boiler_card_repairs.filter(active=True).count()
        elif cat_type == 'Kombi Parçaları':
            return obj.boiler_parts.filter(active=True).count()
        elif cat_type == 'Video':
            return obj.videos.filter(active=True).count()
        elif cat_type == 'Oda Termosatı':
            return obj.room_thermostats.filter(active=True).count()
        return 0


class SparePartImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SparePartImage
        fields = ["id","name","image"]


class FaultCodesSerializer(serializers.ModelSerializer):
    spare_part_images = SparePartImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name')
    brand_name = serializers.CharField(source='brand.name')
    model_name = serializers.CharField(source='model.name')


    class Meta:
        model = FaultCodes
        fields = ['id', 'category','brand','model','code','image','fault_description','spare_part_images','active','brand_name','model_name','category_name']


class ParameterImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterImage
        fields = "__all__"


class ParameterSerializer(serializers.ModelSerializer):
    images = ParameterImageSerializer(many=True, read_only=True)

    class Meta:
        model = Parameter
        fields = "__all__"


class BoilerRepairGuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerRepairGuide
        fields = ["id","title","content","active"]

class BoilerPartImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerPartImage
        fields = "__all__"

class BoilerPartSerializer(serializers.ModelSerializer):
    images = BoilerPartImageSerializer(source='boiler_part_images', many=True, read_only=True)
    class Meta:
        model = BoilerPart
        fields = "__all__"

class SparePartsDefinitionsImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SparePartsDefinitionsImage
        fields = "__all__"

class SparePartsDefinitionsSerializer(serializers.ModelSerializer):
    images = SparePartsDefinitionsImageSerializer(source='spare_parts_definitions_images', many=True, read_only=True)
    class Meta:
        model = SparePartsDefinitions
        fields = "__all__"


class BoilerWorkingPrincipleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerWorkingPrinciple
        fields = "__all__"


class BoilerCardRepairImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerCardRepairImage
        fields = "__all__"


class BoilerCardRepairSerializer(serializers.ModelSerializer):
    images = BoilerCardRepairImageSerializer(many=True, read_only=True)

    class Meta:
        model = BoilerCardRepair
        fields = "__all__"


class BoilerBoardRepairerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerBoardRepairer
        fields = "__all__"


class InstrumentUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstrumentUsage
        fields = "__all__"


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = "__all__"

class RoomTermostatImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomTermostatImage
        fields = "__all__"

class RoomTermostatSerializer(serializers.ModelSerializer):
    images = RoomTermostatImageSerializer( many=True, read_only=True)
    class Meta:
        model = RoomTermostat
        fields = ['id','title','category','brand','model','description','active','images']

class FavoriteBrandCreateSerialier(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = FavoriteBrand
        fields = ["id","user","brand"]
    
class FavoriteBrandSerializer(serializers.ModelSerializer):
    brand = BrandSerializer()
    class Meta:
        model = FavoriteBrand
        fields = ["id","user","brand",]

class FavoriteBrandCreateSerialier(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = FavoriteBrand
        fields = ["id","user","brand"]
class FavoriteModelCreateSerialier(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = FavoriteModel
        fields = ["id","user","model"]
class FavoriteModelSerializer(serializers.ModelSerializer):
    model = ModelSerializer_()
    class Meta:
        model = FavoriteModel
        fields = ["id","user","model"]

class FavoriteFaultCodeCreateSerialier(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = FavoriteFaultCode
        fields = ["id","user","fault"]
        
class FavoriteFaultCodeSerializer(serializers.ModelSerializer):
    fault = FaultCodesSerializer()
    
    class Meta:
        model = FavoriteFaultCode
        fields = ["id","user","fault"]

class SearchFaultCodesSerializer(serializers.ModelSerializer):
    spare_part_images = SparePartImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name')
    brand_name = serializers.CharField(source='brand.name')
    model_name = serializers.CharField(source='model.name')
    class Meta:
        model = FaultCodes
        fields = ["id","code","image","category_name","brand_name","model_name","fault_description","spare_part_images"]
