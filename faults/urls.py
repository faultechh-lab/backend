from django.urls import path
from .views import (CategoryListView,BrandListView,ModelListView,FaultCodesListView,ParameterListView,BoilerBoardRepairerView,
SparePartsDefinitionsView,BoilerWorkingPrincipleView,BoilerCardRepairView,InstrumentUsageView,VideoListView,RoomTermostatView,
FavoriteBrandView,FavoriteModelView,FavoriteFaultCodeView,BoilerRepairGuideView,BoilerPartView,SearchFaultCodesAPIView,
clone_model_view)


urlpatterns = [
    path("category-list/", CategoryListView.as_view(), name="faults-category-list"),
    path("brand-list/", BrandListView.as_view(), name="faults-brand-list"),
    path("model-list/", ModelListView.as_view(), name="faults-model-list"),
    path("fault-codes-list/", FaultCodesListView.as_view(), name="faults-fault-codes-list"),
    path("parameter-list/", ParameterListView.as_view(), name="faults-parameter-list"),
    path("boiler-board-repair/", BoilerBoardRepairerView.as_view(), name="faults-boiler-board-repair"),
    path("spare-parts-definitions/", SparePartsDefinitionsView.as_view(), name="faults-spare-parts-definitions"),
    path("boiler-working-principle/", BoilerWorkingPrincipleView.as_view(), name="faults-boiler-working-principle"),
    path("boiler-card-repair/", BoilerCardRepairView.as_view(), name="faults-boiler-card-repair"),
    path("boiler-parts-list/", BoilerPartView.as_view(), name="faults-boiler-part"),
    path("boiler-repair-guide/", BoilerRepairGuideView.as_view(), name="faults-boiler-repair-guide"),
    path("instrument-usage/", InstrumentUsageView.as_view(), name="faults-instrument-usage"),
    path("video-list/", VideoListView.as_view(), name="faults-video-list"),
    path("room-thermostat/", RoomTermostatView.as_view(), name="faults-room-thermostat"),
    path("favorite-brand/", FavoriteBrandView.as_view(), name="faults-favorite-brand"),
    path("favorite-model/", FavoriteModelView.as_view(), name="faults-favorite-model"),
    path("favorite-fault-code/", FavoriteFaultCodeView.as_view(), name="faults-favorite-fault-code"),
    path("search-fault-codes/", SearchFaultCodesAPIView.as_view(), name="faults-search-fault-codes"),
    path("models/<int:pk>/clone/", clone_model_view, name="faults-clone-model"),
]
