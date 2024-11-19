from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import login
from .models import *
from django.shortcuts import get_object_or_404
from .forms import *
from django.template.loader import render_to_string
from .forms import RegistroForm
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.core.mail import send_mail 

def es_cliente(user):
    return user.groups.filter(name='Cliente').exists()
def es_admin(user):
    return user.groups.filter(name='Administrador').exists()

#paginas disponibles para cada grupo
class ClienteView(LoginRequiredMixin, TemplateView):
    inicio = 'index.html'
    reservas = 'reserva.html' 
    menu = 'menu.html'
    form = 'form_reserva.html'  
    editar_reserva = 'editar_reserva.html'

class AdminView(LoginRequiredMixin, TemplateView):
    inicio_admin = 'admins/inicioadmin.html'
    inventario = 'admins/plato.html'
    crear = 'admins/agregar.html'
    editar_producto = 'admins/editarplato.html'
    reservas = 'admins/formreserva.html'
    reservas_admin = 'admins/tablareserva.html'

def login_views(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirigir según el grupo del usuario
            if user.groups.filter(name='Administrador').exists():
                return redirect('inicioadmin')  # Redirigir a la página del administrador
            elif user.groups.filter(name='Cliente').exists():
                return redirect('Inicio')  # Redirigir a la página del cliente
        else:
            # Si la autenticación falla
            return render(request, 'login.html', {'error': 'Nombre de usuario o contraseña incorrectos'})
    return render(request, 'login.html')

def registro(request):
    error_message = None 
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()  

            # Asignar el grupo según el tipo de usuario
            if form.cleaned_data['user_type'] == 'Administrador':
                group = Group.objects.get(name='Administrador')
                user.groups.add(group)  # Agregar el usuario al grupo correspondiente
                
                # Autenticar y hacer login del usuario
                user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
                if user is not None:
                    login(request, user)  # Loguear al usuario
                    return redirect('Registronegocio')  # Redirigir a la vista de creación de negocio si es Administrador

            else:
                group = Group.objects.get(name='Cliente')
                user.groups.add(group)  # Agregar el usuario al grupo correspondiente

            return redirect('Login')  # Redirigir al login tras el registro exitoso
        else:
            error_message = "Por favor, corrija los errores en el formulario."  # Mensaje de error

    else:
        form = RegistroForm()
    
    return render(request, 'registro.html', {'form': form, 'error_message': error_message})

@login_required
@user_passes_test(es_cliente)
def inicio(request): 
    platos = plato.objects.all()
    restaurantes = restaurante.objects.all()
    return render(request,'index.html', {'platos':platos,'restaurantes': restaurantes})

@login_required
@user_passes_test(es_cliente)
def reservas(request,plato_id):
    platos = get_object_or_404(plato, Id_plato=plato_id)
    if request.method == 'POST':
        numero_contacto = request.POST['telefono']
        personas = request.POST['personas']
        fecha = request.POST['fecha']
        hora = request.POST.get('hora')

        # Obtener el administrador a partir del producto
        administrador = platos.id_restaurante.usuario_administrador

        # Crear la reserva
        reserva = Reserva(
            cliente=request.user,
            administrador=administrador,
            restaurante=platos.id_restaurante,
            numero_personas=personas,
            fecha=fecha,
            hora=hora,
            correo_cliente=request.user.email,
            telefono_cliente=numero_contacto
        )
        reserva.save()

        # Enviar correo al cliente
        subject_cliente = 'Confirmación de tu reserva'
        context_cliente = {
            'nombre': request.user.username,
            'personas': personas,
            'fecha': fecha,
            'hora': hora,
            'negocio': platos.id_restaurante.nombre_restaurante,
            'numero_local': platos.id_restaurante.numero_de_local,
        }
        html_message_cliente = render_to_string('correo/correocliente.html', context_cliente)
        email_cliente = EmailMultiAlternatives(subject_cliente, "", settings.DEFAULT_FROM_EMAIL, [request.user.email])
        email_cliente.attach_alternative(html_message_cliente, "text/html")
        email_cliente.send()

        # Enviar correo al administrador
        subject_admin = 'Nueva reserva'
        context_admin = {
            'nombre': administrador.username,
            'cliente': request.user.username,
            'personas': personas,
            'fecha': fecha,
            'hora': hora,
            'negocio': platos.id_restaurante.nombre_restaurante,
            'numero_local': platos.id_restaurante.numero_de_local,
        }
        html_message_admin = render_to_string('correo/correoadmin.html', context_admin)
        email_admin = EmailMultiAlternatives(subject_admin, "", settings.DEFAULT_FROM_EMAIL, [administrador.email])
        email_admin.attach_alternative(html_message_admin, "text/html")
        email_admin.send()

        messages.success(request, 'Reserva creada con éxito. Se ha enviado un correo de confirmación.')
        return redirect('Inicio')

    return render(request, 'reserva.html', {'plato': platos}) 

@login_required
@user_passes_test(es_cliente)
def eliminar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id_reserva=reserva_id)

    # Obtener datos necesarios para el correo
    cliente_email = reserva.correo_cliente
    nombre_cliente = reserva.cliente.username
    numero_personas = reserva.numero_personas
    fecha = reserva.fecha
    hora = reserva.hora
    administrador_email = reserva.administrador.email  # Correo del administrador

    # Eliminar la reserva
    reserva.delete()

    # Enviar correo de cancelación al cliente
    subject_cliente = 'Cancelación de reserva'
    context_cliente = {
        'nombre': nombre_cliente,
        'numero_personas': numero_personas,
        'fecha': fecha,
        'hora': hora,
    }
    message_cliente = render_to_string('correo/eliminarcliente.html', context_cliente)
    
    email_cliente = EmailMultiAlternatives(subject_cliente, '', settings.DEFAULT_FROM_EMAIL, [cliente_email])
    email_cliente.attach_alternative(message_cliente, 'text/html')  # Cambiado aquí
    email_cliente.send()

    # Enviar correo de cancelación al administrador
    subject_administrador = 'Reserva Cancelada'
    context_administrador = {
        'nombre_cliente': nombre_cliente,
        'numero_personas': numero_personas,
        'fecha': fecha,
        'hora': hora,
    }
    message_administrador = render_to_string('correo/eliminaradmin.html', context_administrador)

    email_administrador = EmailMultiAlternatives(subject_administrador, '', settings.DEFAULT_FROM_EMAIL, [administrador_email])
    email_administrador.attach_alternative(message_administrador, 'text/html')  # Cambiado aquí
    email_administrador.send()

    messages.success(request, 'Reserva cancelada con éxito. Se han enviado correos de confirmación de cancelación.')
    return redirect('Reserva')  # Redirige a la vista de reservas

def editar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
    if request.method == 'POST':
        # Obtener los nuevos datos del formulario
        numero_contacto = request.POST['telefono']
        personas = request.POST['personas']
        fecha = request.POST['fecha']
        hora = request.POST.get('hora')

        # Actualizar la reserva
        reserva.numero_personas = personas
        reserva.fecha = fecha
        reserva.hora = hora
        reserva.telefono_cliente = numero_contacto
        reserva.save()

        # Enviar correo al cliente
        subject_cliente = 'Actualización de tu reserva'
        context_cliente = {
            'nombre': request.user.username,
            'personas': personas,
            'fecha': fecha,
            'hora': hora,
            'negocio': reserva.restaurante.nombre_restaurante,
            'numero_local': reserva.restaurante.numero_de_local,
        }
        html_message_cliente = render_to_string('correo/actreservacliente.html', context_cliente)
        email_cliente = EmailMultiAlternatives(subject_cliente, "", settings.DEFAULT_FROM_EMAIL, [request.user.email])
        email_cliente.attach_alternative(html_message_cliente, "text/html")
        email_cliente.send()

        # Enviar correo al administrador
        subject_admin = 'Reserva Actualizada'
        context_admin = {
            'nombre': reserva.administrador.username,
            'cliente': request.user.username,
            'personas': personas,
            'fecha': fecha,
            'hora': hora,
            'negocio': reserva.restaurante.nombre_restaurante,
            'numero_local': reserva.restaurante.numero_de_local,
        }
        html_message_admin = render_to_string('correo/actreservaadmin.html', context_admin)
        email_admin = EmailMultiAlternatives(subject_admin, "", settings.DEFAULT_FROM_EMAIL, [reserva.administrador.email])
        email_admin.attach_alternative(html_message_admin, "text/html")
        email_admin.send()

        messages.success(request, 'Reserva actualizada con éxito. Se ha enviado un correo de confirmación.')
        return redirect('Reserva')

    # Para el método GET, muestra el formulario con los datos existentes
    return render(request, 'edireservacli.html', {'reserva': reserva})


def reservascli (request):
    reservas_cliente = Reserva.objects.filter(cliente=request.user)
    return render(request,'reservascli.html',{'reservas': reservas_cliente})

@login_required
@user_passes_test(es_admin)
def adminplatos(request):
    Restaurante = get_object_or_404(restaurante, usuario_administrador=request.user)
    platos = plato.objects.filter(id_restaurante=Restaurante)
    return render(request,'admins/plato.html', {'platos':platos})

@login_required
@user_passes_test(es_cliente)
def menu(request):
    platos = plato.objects.all()
    return render(request,'menu.html', {'platos':platos})

@login_required
@user_passes_test(es_admin)
def inicioadmin(request):
    return render(request, 'admins/inicioadmin.html')

@login_required
@user_passes_test(es_admin)
def agregarplato(request):
    if request.method == 'POST':
        form = platoForm(request.POST, request.FILES)
        if form.is_valid():
            plato = form.save(commit=False)
            # Obtener el restaurante relacionado al usuario autenticado
            restaurante_obj = get_object_or_404(restaurante, usuario_administrador=request.user)  # Usa 'restaurante' como nombre del modelo
            plato.id_restaurante = restaurante_obj
            plato.save()
            return redirect('Plato')
    else:
        form = platoForm()
    return render(request, 'admins/agregarplato.html', {'form': form})

@login_required
@user_passes_test(es_admin)
def editar_plato(request, Id_plato=None):
    # Obtenemos el plato a editar o devolvemos un 404 si no existe
    plato_obj = get_object_or_404(plato, Id_plato=Id_plato)
    
    if request.method == 'POST':
        # Instanciamos el formulario con los datos enviados
        form = platoForm(request.POST, request.FILES, instance=plato_obj)
        
        if form.is_valid():
            form.save()  # Guardamos los cambios
            return redirect('Plato')  # Redirigimos al listado de platos
        
    else:
        # Si la solicitud no es POST, cargamos el formulario con los datos del plato existente
        form = platoForm(instance=plato_obj)

    return render(request, 'admins/editarplato.html', {'form': form})

@login_required
@user_passes_test(es_admin)
def eliminar_plato(request, Id_plato):
    plato_obj = get_object_or_404(plato, Id_plato=Id_plato)
    plato_obj.delete()
    messages.success(request, 'Plato eliminado con éxito.')
    return redirect('Plato')

@login_required
@user_passes_test(es_admin)
def adminreserva(request):
    reservas_admin = Reserva.objects.filter(administrador=request.user)
    return render(request, 'admins/tablareserva.html', {'reservas':reservas_admin})

@login_required
def eliminar_reserva_admin(request, reserva_id):
    reserva = get_object_or_404(Reserva, id_reserva=reserva_id)

    # Obtener datos necesarios para el correo
    cliente_email = reserva.correo_cliente
    nombre_cliente = reserva.cliente.username
    numero_personas = reserva.numero_personas
    fecha = reserva.fecha
    hora = reserva.hora

    # Eliminar la reserva
    reserva.delete()

    # Enviar correo de cancelación al cliente
    subject_cliente = 'Cancelación de reserva'
    context_cliente = {
        'nombre': nombre_cliente,
        'numero_personas': numero_personas,
        'fecha': fecha,
        'hora': hora,
    }
    message_cliente = render_to_string('correo/eliminarcliente.html', context_cliente)
    
    email_cliente = EmailMultiAlternatives(subject_cliente, '', settings.DEFAULT_FROM_EMAIL, [cliente_email])
    email_cliente.attach_alternative(message_cliente, 'text/html')  # Cambiado aquí
    email_cliente.send()

    # Enviar correo de cancelación al administrador
    subject_administrador = 'Reserva Cancelada'
    context_administrador = {
        'nombre_cliente': nombre_cliente,
        'numero_personas': numero_personas,
        'fecha': fecha,
        'hora': hora,
    }
    message_administrador = render_to_string('correo/eliminaradmin.html', context_administrador)

    email_administrador = EmailMultiAlternatives(subject_administrador, '', settings.DEFAULT_FROM_EMAIL, [request.user.email])
    email_administrador.attach_alternative(message_administrador, 'text/html')  # Cambiado aquí
    email_administrador.send()

    messages.success(request, 'Reserva cancelada con éxito. Se han enviado correos de confirmación de cancelación.')
    return redirect('adminreserva')




def registronegocio(request):
    if request.method == "POST":
        logo_restaurante = request.FILES.get('logo_restaurante')
        nombre_restaurante = request.POST.get('nombre_restaurante')
        telefono = request.POST.get('telefono')
        numero_de_local = request.POST.get('numero_de_local')
        correo_de_local = request.POST.get('correo_de_local')
        
        # Crear el negocio
        Restaurante = restaurante(
            logo_restaurante=logo_restaurante,
            nombre_restaurante=nombre_restaurante,
            telefono=telefono,
            numero_de_local=numero_de_local,
            correo_de_local=correo_de_local,
            usuario_administrador=request.user
        )
        Restaurante.save()  # Guardar el negocio

        return redirect('inicioadmin')  # Redirigir a una vista específica después del registro

    return render(request, 'formnegocio.html')  