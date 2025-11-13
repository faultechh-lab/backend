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

    class Meta:
        model = Category
        fields = ("id", "name", 'type','image','active', "parent", "children","has_children")
    def get_children(self, obj):
        return CategorySerializer(obj.children.filter(parent=obj), many=True).data
    def get_has_children(self, obj):
        return obj.children.exists()


class BrandSerializer(serializers.ModelSerializer):
    category_name=serializers.CharField(source='category.name')
    class Meta:
        model = Brand
        fields = "__all__"


class ModelSerializer_(serializers.ModelSerializer):
    category_name=serializers.CharField(source='category.name')
    brand_name=serializers.CharField(source='brand.name')
    class Meta:
        model = Model
        fields = "__all__"


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