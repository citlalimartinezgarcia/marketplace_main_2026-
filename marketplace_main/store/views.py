from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import RegisterForm, ProductForm
from .models import Product, Cart, CartItem, Category


# ==========================================
# 🏠 Vistas Públicas y Catálogo (Búsqueda + Filtros)
# ==========================================

def home(request):
    query = request.GET.get('q')
    category_id = request.GET.get('category')

    # Base Queryset con optimización select_related y prefetch_related
    products = Product.objects.select_related('owner').prefetch_related('categories').all().order_by('-created_at')

    # =========================
    # 🔎 Búsqueda por texto (Nombre o Descripción)
    # =========================
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    # =========================
    # 🏷️ Filtro por Categoría
    # =========================
    if category_id:
        products = products.filter(categories__id=category_id)

    # =========================
    # 📄 Paginación (6 productos por página)
    # =========================
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Necesitamos todas las categorías para pintar la barra lateral o menú de filtros
    categories = Category.objects.all()

    return render(request, 'store/home.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id
    })


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('home')
            
    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# ==========================================
# 📊 Panel de Control (Dashboard)
# ==========================================

@login_required
def dashboard(request):
    if not request.user.is_seller:
        return HttpResponseForbidden("No tienes permisos de vendedor para acceder aquí.")

    products = Product.objects.filter(owner=request.user)
    return render(request, 'store/dashboard.html', {'products': products})


# ==========================================
# ➕ Productos: CRUD
# ==========================================

@login_required
def product_create(request):
    if not request.user.is_seller:
        return HttpResponseForbidden("Solo los vendedores pueden crear productos.")

    form = ProductForm(request.POST or None)

    if form.is_valid():
        product = form.save(commit=False)
        product.owner = request.user
        product.save()
        form.save_m2m()
        return redirect('dashboard')

    return render(request, 'store/product_form.html', {'form': form})


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if product.owner != request.user:
        return HttpResponseForbidden("No tienes permiso para editar este producto.")

    form = ProductForm(request.POST or None, instance=product)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'store/product_form.html', {'form': form})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if product.owner != request.user:
        return HttpResponseForbidden("No tienes permiso para eliminar este producto.")

    if request.method == 'POST':
        product.delete()
        return redirect('dashboard')

    return render(request, 'store/product_confirm_delete.html', {'product': product})


# ==========================================
# 🛒 Carrito: Operaciones básicas
# ==========================================

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart_detail.html', {'cart': cart})


@login_required
def add_to_cart(request, product_id):
    cart, created_cart = Cart.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)

    cart_item, created_item = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    if not created_item:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart_detail')


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect('cart_detail')


@login_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

        if quantity > 0:
            item.quantity = quantity
            item.save()
        else:
            item.delete()

    return redirect('cart_detail')