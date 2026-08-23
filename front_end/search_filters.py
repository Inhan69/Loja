from decimal import Decimal, InvalidOperation

from django.db.models import Q, CharField
from django.db.models.functions import Cast

CAMPO_PADRAO_PRODUTO = "nome"
CAMPO_PADRAO_CLIENTE = "nome"


def _digitos(termo: str) -> str:
    return "".join(ch for ch in termo if ch.isdigit())


def _decimal(termo: str):
    try:
        return Decimal(termo.replace(".", "").replace(",", "."))
    except (InvalidOperation, AttributeError):
        return None


def _normalizar_campo(campo: str, validos: set, padrao: str) -> str:
    return campo if campo in validos else padrao


def _filtro_numerico_texto(queryset, campo: str, termo: str):
    return queryset.annotate(**{f"{campo}_txt": Cast(campo, CharField())}).filter(
        **{f"{campo}_txt__icontains": termo.replace(",", ".")}
    )


def _filtro_icontains(queryset, **kwargs):
    return queryset.filter(**{f"{k}__icontains": v for k, v in kwargs.items()})


def filtrar_produtos(queryset, campo: str, termo: str):
    termo = (termo or "").strip()
    if not termo:
        return queryset

    campo = _normalizar_campo(
        campo, {"nome", "codigo", "quantidade", "preco"}, CAMPO_PADRAO_PRODUTO
    )

    if campo in ("nome", "codigo"):
        return _filtro_icontains(queryset, **{campo: termo})

    valor = _decimal(termo)
    if valor is not None:
        return queryset.filter(**{campo: valor})
    return _filtro_numerico_texto(queryset, campo, termo)


def filtrar_clientes(queryset, campo: str, termo: str):
    termo = (termo or "").strip()
    if not termo:
        return queryset

    campo = _normalizar_campo(
        campo,
        {"nome", "cpf", "telefone", "bairro", "rua", "numero"},
        CAMPO_PADRAO_CLIENTE,
    )

    if campo in ("nome", "bairro", "rua"):
        return _filtro_icontains(queryset, **{campo: termo})

    if campo == "numero":
        return queryset.filter(numero=int(termo)) if termo.isdigit() else queryset.none()

    filtro = Q(**{f"{campo}__icontains": termo})
    if campo in ("cpf", "telefone") and (d := _digitos(termo)):
        filtro |= Q(**{f"{campo}__icontains": d})
    return queryset.filter(filtro)
