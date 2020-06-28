from django.urls import path
from . import views

app_name = 'app'
urlpatterns = [
    path('api/scadddata', views.SCAddDataAPI.as_view(), name='sc_add_data_api'),
    path('api/scregister', views.SCRegisterAPI.as_view(), name='scregister'),
    path('api/scprofile', views.SCProfileApi.as_view(), name='sc_profile_api'),
    path('api/scmembers', views.SCMembersApi.as_view(), name='sc_members_api'),
    path('api/scaddmembers', views.SCAddMemberAPI.as_view(), name='sc_add_members_api'),
    path('api/sccreatesystem', views.SCCreteSystemAPI.as_view(), name='sc_create_system_api'),
    path('api/scselectsystem', views.SCSelectSystemAPI.as_view(), name='sc_select_system_api'),
    path('api/scsetsecurity', views.SCSecureStatusDataAPI.as_view(), name='sc_set_security_api'),
    path('api/scdatas', views.SCDatasApi.as_view(), name='sc_datas_api'),
    path('api/scanalysis', views.SCAnalysisApi.as_view(), name='sc_analysis_api'),
]