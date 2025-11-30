from django import template

register = template.Library()


@register.filter
def add_class(field, class_name: str):
    current_classes: list[str] = field.field.widget.attrs.get("class", "").split()
    classes_to_add = class_name.split()

    classes = current_classes + list(
        filter(lambda cls: cls not in current_classes, classes_to_add)
    )

    field.field.widget.attrs["class"] = " ".join(classes)
    return field
