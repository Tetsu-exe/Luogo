from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_views, name="Login"),
    path('registro/', views.registro, name="Registro"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('inicio/', views.inicio, name="Inicio"),
    path('inicioadmin', views.inicioadmin, name='inicioadmin'),
    path('reserva/', views.reservascli, name='Reserva'),
    path('menu/', views.menu, name='Menu'),
    path('platos/', views.adminplatos, name='Plato'),
    path('platos/agregar', views.agregarplato, name='Agregarplato'),
    path('Plato/borrar/<int:Id_plato>/', views.eliminar_plato, name='eliminar_plato'),
    path('adminreservas', views.adminreserva, name='adminreserva'),
    path('Plato/editar/<int:Id_plato>/', views.editar_plato, name='editar'),
    path('registro/registronegocio/', views.registronegocio, name='Registronegocio'),
    path('reservas/<int:plato_id>/', views.reservas, name='Reservas'),
    path('eliminar_reserva/<int:reserva_id>/', views.eliminar_reserva, name='eliminar_reserva'),
    path('editar_reserva/<int:reserva_id>/', views.editar_reserva, name='editarreserva'),
    path('eliminar_reserva_admin/<int:reserva_id>/', views.eliminar_reserva_admin, name='eliminar_reserva_admin'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
