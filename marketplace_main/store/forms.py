from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Product

# --- Formulario de Autenticación ---
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_seller = forms.BooleanField(required=False, label="¿Registrar como vendedor?")

    class Meta:
        model = User
        # Nota: 'password1' y 'password2' se omiten aquí porque UserCreationForm 
        # los maneja e incluye automáticamente en la validación.
        fields = ('username', 'email', 'is_seller')


# --- Formulario de Productos (CRUD) ---
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'categories']
        widgets = {
            'categories': forms.CheckboxSelectMultiple()
        }