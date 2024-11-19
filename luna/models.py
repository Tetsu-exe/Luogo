from django.db import models
from django.contrib.auth.models import User

#clase para los datos de los negocios

class restaurante(models.Model):
    id_restaurante = models.AutoField(primary_key=True)
    logo_restaurante =models.ImageField(upload_to='imagenes/', height_field=None, width_field=None, max_length=None, verbose_name='logo', null=True)
    nombre_restaurante = models.CharField(max_length=50, verbose_name='Nombre del restaurante')
    telefono = models.CharField(max_length=50, verbose_name='Teléfono')
    numero_de_local = models.CharField(max_length=50, verbose_name='Direccion')
    correo_de_local = models.CharField(max_length=50, verbose_name='Correo')
    usuario_administrador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restaurantes', verbose_name='Usuario Administrador')
    
    def _str_(self):#funcion para mostrar mas informacion en la pagina de administracion
        descripcion =  (f"logo_restaurante: {self.logo_restaurante}--restaurante: {self.nombre_restaurante}--Telfono: {self.telefono}--Local: {self.numero_de_local}--Correo: {self.correo_de_local} " )
        return descripcion
    
class plato(models.Model):
    Id_plato = models.AutoField(primary_key=True)#autoincreentable key 
    imagen = models.ImageField(upload_to='imagenes/', verbose_name='Imagen')#imagen
    nombre = models.CharField(max_length=50, verbose_name='Nombre')#varchar
    precio = models.IntegerField(verbose_name="Precio")#int
    id_restaurante = models.ForeignKey('restaurante', on_delete=models.CASCADE, verbose_name="Id_restaurante")#foranea key
    descripcion = models.CharField(max_length=1000, verbose_name='descripcion')#varchar
    
    def _str_(self):#funcion para mostrar mas informacion en la pagina de administracion
        descripcion =  (f"Plato: {self.nombre}--Precio: {self.precio}" )
        return descripcion
    def eliminar(self, using=None, keep_parents=False):
        self.imagen.storage.delete(self.imagen)
        super().delete()

#tabla de reserva
class Reserva(models.Model):
    id_reserva = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas_cliente', verbose_name='Cliente')
    restaurante = models.ForeignKey(restaurante, on_delete=models.CASCADE, verbose_name='Negocio') 
    administrador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas_administrador', verbose_name='Administrador')
    fecha = models.DateField(verbose_name='Fecha de la reserva')
    hora = models.TimeField(verbose_name='Hora de la reserva')
    numero_personas = models.IntegerField(verbose_name='Número de personas')
    correo_cliente = models.EmailField(verbose_name='Correo del cliente')
    telefono_cliente = models.CharField(max_length=15, verbose_name='Teléfono del cliente')
    
    def _str_(self):
        return f"Reserva de {self.cliente.username} para {self.numero_personas} personas el {self.fecha} a las {self.hora}"