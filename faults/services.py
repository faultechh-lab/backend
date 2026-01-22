import os
from django.db import transaction
from django.core.files.base import ContentFile
from .models import (
    Model as BoilerModel,
    Brand,
    FaultCodes,
    SparePartImage,
    Parameter,
    ParameterImage,
    BoilerPart,
    BoilerPartImage,
    BoilerCardRepair,
    BoilerCardRepairImage,
    Video,
    RoomTermostat,
    RoomTermostatImage,
)

@transaction.atomic
def clone_model_with_children(source: BoilerModel, *, name_suffix: str = " (kopya)", make_inactive: bool = False, override_brand: Brand | None = None) -> BoilerModel:
    """
    Clone a Model and its children (FaultCodes with SparePartImage, Parameters with ParameterImage)
    - name_suffix: appended to the model name
    - make_inactive: set new model active field to False if True
    """
    # Prepare base fields for model clone
    model_fields = {
        "name": f"{getattr(source, 'name', '')}{name_suffix}",
        "category": source.category,
        "brand": override_brand if override_brand is not None else source.brand,
        "active": (False if make_inactive else getattr(source, "active", True)),
        "image": source.image and ContentFile(source.image.read(), name=os.path.basename(source.image.name)) if source.image else None,
    }
    # Also copy translated name_* fields if they exist on the model
    LANGS = ("tr", "en", "es", "it", "fr", "ru", "de")
    for lang in LANGS:
        attr = f"name_{lang}"
        if hasattr(source, attr):
            val = getattr(source, attr) or ""
            model_fields[attr] = f"{val}" if val else val
    new_model = BoilerModel.objects.create(**model_fields)

    # Clone FaultCodes
    src_faults = FaultCodes.objects.filter(model=source)
    for fc in src_faults:
        # Base fields
        fc_kwargs = dict(
            category=fc.category,
            brand=new_model.brand,
            model=new_model,
            code=fc.code,
            fault_description=getattr(fc, "fault_description", None),
            active=fc.active,
            image=ContentFile(fc.image.read(), name=os.path.basename(fc.image.name)) if fc.image else None,
        )
        # Copy translated code_* and fault_description_* fields if present
        for lang in LANGS:
            code_attr = f"code_{lang}"
            if hasattr(fc, code_attr):
                fc_kwargs[code_attr] = getattr(fc, code_attr)
        for lang in LANGS:
            attr = f"fault_description_{lang}"
            if hasattr(fc, attr):
                fc_kwargs[attr] = getattr(fc, attr)
        new_fc = FaultCodes.objects.create(**fc_kwargs)

        # Clone SparePartImage for this fault
        spares = fc.spare_part_images.all()
        for sp in spares:
            sp_kwargs = dict(
                fault_code=new_fc,
                name=getattr(sp, "name", None),
                image=ContentFile(sp.image.read(), name=os.path.basename(sp.image.name)) if sp.image else None,
                active=sp.active,
            )
            # Copy translated name_* if present
            for lang in LANGS:
                nattr = f"name_{lang}"
                if hasattr(sp, nattr):
                    sp_kwargs[nattr] = getattr(sp, nattr)
            SparePartImage.objects.create(**sp_kwargs)

    # Clone Parameters
    src_params = Parameter.objects.filter(model=source)
    for p in src_params:
        # Base fields
        p_kwargs = dict(
            name=(getattr(p, "name", None) or ""),
            category=p.category,
            brand=new_model.brand,
            model=new_model,
            description=getattr(p, "description", None),
            active=p.active,
        )
        # If translated name_* exists, copy
        for lang in LANGS:
            nattr = f"name_{lang}"
            if hasattr(p, nattr):
                val = getattr(p, nattr) or ""
                p_kwargs[nattr] = val
        # Copy translated description_* if present
        for lang in LANGS:
            dattr = f"description_{lang}"
            if hasattr(p, dattr):
                p_kwargs[dattr] = getattr(p, dattr)
        new_p = Parameter.objects.create(**p_kwargs)

        # Clone ParameterImage for this parameter
        pimages = p.images.all()
        for pi in pimages:
            img = ContentFile(pi.image.read(), name=os.path.basename(pi.image.name)) if pi.image else None
            ParameterImage.objects.create(parameter=new_p, image=img, active=pi.active)

    # Clone BoilerPart
    src_parts = BoilerPart.objects.filter(model=source)
    for bp in src_parts:
        bp_kwargs = dict(
            name=getattr(bp, "name", None) or "",
            category=bp.category,
            brand=new_model.brand,
            model=new_model,
            active=bp.active,
        )
        for lang in LANGS:
            nattr = f"name_{lang}"
            if hasattr(bp, nattr):
                bp_kwargs[nattr] = getattr(bp, nattr)
        new_bp = BoilerPart.objects.create(**bp_kwargs)

        # Clone BoilerPartImage
        bp_images = bp.boiler_part_images.all()
        for bpi in bp_images:
            img = ContentFile(bpi.image.read(), name=os.path.basename(bpi.image.name)) if bpi.image else None
            BoilerPartImage.objects.create(boiler_part=new_bp, image=img, active=bpi.active)

    # Clone BoilerCardRepair
    src_repairs = BoilerCardRepair.objects.filter(model=source)
    for br in src_repairs:
        br_kwargs = dict(
            title=getattr(br, "title", None) or "",
            category=br.category,
            brand=new_model.brand,
            model=new_model,
            description=getattr(br, "description", None),
            video_url=getattr(br, "video_url", None),
            active=br.active,
        )
        for lang in LANGS:
            tattr = f"title_{lang}"
            if hasattr(br, tattr):
                br_kwargs[tattr] = getattr(br, tattr)
        for lang in LANGS:
            dattr = f"description_{lang}"
            if hasattr(br, dattr):
                br_kwargs[dattr] = getattr(br, dattr)
        new_br = BoilerCardRepair.objects.create(**br_kwargs)

        # Clone BoilerCardRepairImage
        repair_images = br.images.all()
        for ri in repair_images:
            img = ContentFile(ri.image.read(), name=os.path.basename(ri.image.name)) if ri.image else None
            BoilerCardRepairImage.objects.create(boiler_card_repair=new_br, image=img, active=ri.active)

    # Clone Video
    src_videos = Video.objects.filter(model=source)
    for v in src_videos:
        v_kwargs = dict(
            title=getattr(v, "title", None) or "",
            category=v.category,
            brand=new_model.brand,
            model=new_model,
            description=getattr(v, "description", None),
            video_url=getattr(v, "video_url", None),
            image=ContentFile(v.image.read(), name=os.path.basename(v.image.name)) if v.image else None,
            active=v.active,
        )
        for lang in LANGS:
            tattr = f"title_{lang}"
            if hasattr(v, tattr):
                v_kwargs[tattr] = getattr(v, tattr)
        for lang in LANGS:
            dattr = f"description_{lang}"
            if hasattr(v, dattr):
                v_kwargs[dattr] = getattr(v, dattr)
        Video.objects.create(**v_kwargs)

    # Clone RoomTermostat
    src_rooms = RoomTermostat.objects.filter(model=source)
    for rt in src_rooms:
        rt_kwargs = dict(
            title=getattr(rt, "title", None) or "",
            category=rt.category,
            brand=new_model.brand,
            model=new_model,
            description=getattr(rt, "description", None),
            active=rt.active,
        )
        for lang in LANGS:
            tattr = f"title_{lang}"
            if hasattr(rt, tattr):
                rt_kwargs[tattr] = getattr(rt, tattr)
        for lang in LANGS:
            dattr = f"description_{lang}"
            if hasattr(rt, dattr):
                rt_kwargs[dattr] = getattr(rt, dattr)
        new_rt = RoomTermostat.objects.create(**rt_kwargs)

        # Clone RoomTermostatImage
        room_images = rt.images.all()
        for rti in room_images:
            img = ContentFile(rti.image.read(), name=os.path.basename(rti.image.name)) if rti.image else None
            RoomTermostatImage.objects.create(room_thermostat=new_rt, image=img, active=rti.active)

    return new_model


@transaction.atomic
def clone_brand_with_children(source: Brand, *, name_suffix: str = " (kopya)", make_inactive: bool = False) -> Brand:
    brand_fields = {
        "name": f"{getattr(source, 'name', '')}{name_suffix}",
        "category": source.category,
        "active": (False if make_inactive else getattr(source, "active", True)),
        "image": source.image and ContentFile(source.image.read(), name=os.path.basename(source.image.name)) if source.image else None,
    }
    LANGS = ("tr", "en", "es", "it", "fr", "ru", "de")
    for lang in LANGS:
        attr = f"name_{lang}"
        if hasattr(source, attr):
            val = getattr(source, attr) or ""
            brand_fields[attr] = f"{val}" if val else val
    new_brand = Brand.objects.create(**brand_fields)

    src_models = list(BoilerModel.objects.filter(brand=source))
    for m in src_models:
        clone_model_with_children(m, name_suffix=name_suffix, make_inactive=make_inactive, override_brand=new_brand)

    return new_brand
