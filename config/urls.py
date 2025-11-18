from django.urls import path,include
from .views import (
    OnboardView,
    ConfigView,UserView,UserListView,CompanyView,DefinedDeviceView,DeviceRenewalView,AdminLoginView,
    CategoryView,BrandView,ModelView,FaultCodesView,ParameterView,BoilerPartView,BoilerCardRepairView,
    BoilerWorkingPrincipleView,VideoView,RoomTermostatView,InstrumentUsageView,SparePartsDefinitionsView,
    BoilerRepairGuideView,BoilerBoardRepairerView,FormView,NewsView,NotificationView,ProductView,OrderNotificationView,
    ExpoPushSendView
)


urlpatterns=[
    path('', ConfigView.as_view(), name='config'),
    path('user-list/', UserListView.as_view(), name='user-list'),
    path('user-list/<uuid:pk>/', UserView.as_view(), name='user-detail'),
    path('company-list/', CompanyView.as_view(), name='company-list'),
    path('company-list/<uuid:pk>/', CompanyView.as_view(), name='company-detail'),
    path('defined-device-list/', DefinedDeviceView.as_view(), name='defined-device-list'),
    path('defined-device-list/<uuid:pk>/', DefinedDeviceView.as_view(), name='defined-device-detail'),
    path('device-renewal-list/', DeviceRenewalView.as_view(), name='device-renewal-list'),
    path('device-renewal-list/<int:pk>/', DeviceRenewalView.as_view(), name='device-renewal-detail'),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
    
    path('categories/', CategoryView.as_view(), name='category-list'),
    path('brands/', BrandView.as_view(), name='brand-list'),
    path('models/', ModelView.as_view(), name='model-list'),
    path('fault-codes/', FaultCodesView.as_view(), name='fault-codes-list'),
    path('parameters/', ParameterView.as_view(), name='parameters-list'),
    path('onboard/', OnboardView.as_view(), name='onboard-list'),

    path('boiler-part/', BoilerPartView.as_view(), name='boiler-part'),
    path('boiler-card-repair/', BoilerCardRepairView.as_view(), name='boiler-card-repair'),
    path('video-list/', VideoView.as_view(), name='video-list'),
    path('room-termostat/', RoomTermostatView.as_view(), name='room-termostat'),
    path('boiler-working-principle/', BoilerWorkingPrincipleView.as_view(), name='boiler-working-principle'),
    
    path('instrument-usage/', InstrumentUsageView.as_view(), name='instrument-usage'),
    path('spare-parts-definitions/', SparePartsDefinitionsView.as_view(), name='spare-parts-definitions'),
    path('boiler-repair-guide/', BoilerRepairGuideView.as_view(), name='boiler-repair-guide'),  
    path('boiler-board-repairer/', BoilerBoardRepairerView.as_view(), name='boiler-board-repairer'),

    path('forms/', FormView.as_view(), name='form-list'),
    path('news/', NewsView.as_view(), name='news-list'),
    path('notification/', NotificationView.as_view(), name='notification-list'),
    path('notification/<int:id>/', NotificationView.as_view(), name='notification-delete'),
    path('expo-push-send/', ExpoPushSendView.as_view(), name='expo-push-send'),
    path('product/', ProductView.as_view(), name='product-list'),
    path('order-notification/', OrderNotificationView.as_view(), name='order-notification-list'),
]