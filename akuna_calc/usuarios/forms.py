from django import forms
from django.contrib.auth import get_user_model

from .access_control import ACCESS_CODE_METADATA, build_permission_groups, get_access_profile, normalize_access_codes, requires_staff_flag
from .models import RolSistema

User = get_user_model()

INPUT_CLASS = 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
CHECKBOX_CLASS = 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'


class BaseUserAccessForm(forms.ModelForm):
    rol_sistema = forms.ModelChoiceField(
        queryset=RolSistema.objects.none(),
        required=False,
        empty_label='Sin rol global',
        label='Rol del sistema',
        widget=forms.Select(attrs={
            'class': INPUT_CLASS,
        }),
    )
    access_codes = forms.MultipleChoiceField(
        required=False,
        label='Permisos por módulo y opción',
        choices=(),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': INPUT_CLASS,
            }),
            'email': forms.EmailInput(attrs={
                'class': INPUT_CLASS,
            }),
            'first_name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
            }),
            'last_name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': CHECKBOX_CLASS,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol_sistema'].queryset = RolSistema.objects.filter(activo=True).order_by('nombre')
        self.fields['access_codes'].choices = [
            (code, metadata['label']) for code, metadata in ACCESS_CODE_METADATA.items()
        ]

        profile = get_access_profile(self.instance) if self.instance and self.instance.pk else None
        initial_codes = profile.permisos_normalizados() if profile else []

        if not self.is_bound:
            self.initial['rol_sistema'] = profile.rol_id if profile and profile.rol_id else None
            self.initial['access_codes'] = initial_codes

        if self.is_bound:
            if hasattr(self.data, 'getlist'):
                selected_codes = self.data.getlist('access_codes')
            else:
                raw_codes = self.data.get('access_codes', [])
                selected_codes = raw_codes if isinstance(raw_codes, list) else [raw_codes]
        else:
            selected_codes = initial_codes
        self.permission_groups = build_permission_groups(selected_codes)

    def clean_access_codes(self):
        return normalize_access_codes(self.cleaned_data.get('access_codes'))

    def save_access_profile(self, user):
        role = self.cleaned_data.get('rol_sistema')
        access_codes = self.cleaned_data.get('access_codes', [])
        normalized_codes = [] if role and role.acceso_total else normalize_access_codes(access_codes)

        user.is_staff = user.is_superuser or requires_staff_flag(role, normalized_codes)
        user.save(update_fields=['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff'])

        profile = get_access_profile(user, create=True)
        profile.rol = role
        profile.permisos = normalized_codes
        profile.save()


class UserCreateForm(BaseUserAccessForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
        })
    )

    class Meta(BaseUserAccessForm.Meta):
        fields = BaseUserAccessForm.Meta.fields

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            self.save_access_profile(user)
        return user


class UserUpdateForm(BaseUserAccessForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Dejar vacío para no cambiar'
        })
    )

    class Meta(BaseUserAccessForm.Meta):
        widgets = {
            **BaseUserAccessForm.Meta.widgets,
            'username': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'readonly': 'readonly'
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_access_profile(user)
        return user