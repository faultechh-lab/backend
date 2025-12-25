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
    src_faults = list(FaultCodes.objects.filter(model=source))
    new_faults = []
    for fc in src_faults:
        # Base fields
        fc_kwargs = dict(
            category=fc.category,
            brand=fc.brand,
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
        new_faults.append(FaultCodes(**fc_kwargs))
    created_faults = FaultCodes.objects.bulk_create(new_faults) if new_faults else []

    # Map old fault id -> new fault instance
    fault_map = {old.id: new for old, new in zip(src_faults, created_faults)}

    # Clone SparePartImage for each fault
    if fault_map:
        spares = SparePartImage.objects.filter(fault_code__in=[f.id for f in src_faults]).select_related("fault_code")
        new_spares = []
        for sp in spares:
            sp_kwargs = dict(
                fault_code=fault_map.get(sp.fault_code_id),
                name=getattr(sp, "name", None),
                image=ContentFile(sp.image.read(), name=os.path.basename(sp.image.name)) if sp.image else None,
                active=sp.active,
            )
            # Copy translated name_* if present
            for lang in LANGS:
                nattr = f"name_{lang}"
                if hasattr(sp, nattr):
                    sp_kwargs[nattr] = getattr(sp, nattr)
            new_spares.append(SparePartImage(**sp_kwargs))
        if new_spares:
            SparePartImage.objects.bulk_create(new_spares)

    # Clone Parameters
    src_params = list(Parameter.objects.filter(model=source))
    new_params = []
    for p in src_params:
        # Base fields
        p_kwargs = dict(
            name=(getattr(p, "name", None) or ""),
            category=p.category,
            brand=p.brand,
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
        new_params.append(Parameter(**p_kwargs))
    created_params = Parameter.objects.bulk_create(new_params) if new_params else []

    # Map old param id -> new param instance
    param_map = {old.id: new for old, new in zip(src_params, created_params)}

    # Clone ParameterImage for each parameter
    if param_map:
        pimages = ParameterImage.objects.filter(parameter__in=[p.id for p in src_params]).select_related("parameter")
        new_pimages = []
        for pi in pimages:
            img = ContentFile(pi.image.read(), name=os.path.basename(pi.image.name)) if pi.image else None
            new_pimages.append(ParameterImage(parameter=param_map.get(pi.parameter_id), image=img, active=pi.active))
        if new_pimages:
            ParameterImage.objects.bulk_create(new_pimages)

    # Clone BoilerPart
    src_parts = list(BoilerPart.objects.filter(model=source))
    new_parts = []
    for bp in src_parts:
        bp_kwargs = dict(
            name=getattr(bp, "name", None) or "",
            category=bp.category,
            brand=bp.brand,
            model=new_model,
            active=bp.active,
        )
        for lang in LANGS:
            nattr = f"name_{lang}"
            if hasattr(bp, nattr):
                bp_kwargs[nattr] = getattr(bp, nattr)
        new_parts.append(BoilerPart(**bp_kwargs))
    created_parts = BoilerPart.objects.bulk_create(new_parts) if new_parts else []

    # Map old part id -> new part instance
    part_map = {old.id: new for old, new in zip(src_parts, created_parts)}

    # Clone BoilerPartImage
    if part_map:
        bp_images = BoilerPartImage.objects.filter(boiler_part__in=[p.id for p in src_parts]).select_related("boiler_part")
        new_bp_images = []
        for bpi in bp_images:
            img = ContentFile(bpi.image.read(), name=os.path.basename(bpi.image.name)) if bpi.image else None
            new_bp_images.append(BoilerPartImage(boiler_part=part_map.get(bpi.boiler_part_id), image=img, active=bpi.active))
        if new_bp_images:
            BoilerPartImage.objects.bulk_create(new_bp_images)

    # Clone BoilerCardRepair
    src_repairs = list(BoilerCardRepair.objects.filter(model=source))
    new_repairs = []
    for br in src_repairs:
        br_kwargs = dict(
            title=getattr(br, "title", None) or "",
            category=br.category,
            brand=br.brand,
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
        new_repairs.append(BoilerCardRepair(**br_kwargs))
    created_repairs = BoilerCardRepair.objects.bulk_create(new_repairs) if new_repairs else []

    # Map old repair id -> new repair instance
    repair_map = {old.id: new for old, new in zip(src_repairs, created_repairs)}

    # Clone BoilerCardRepairImage
    if repair_map:
        repair_images = BoilerCardRepairImage.objects.filter(boiler_card_repair__in=[r.id for r in src_repairs]).select_related("boiler_card_repair")
        new_repair_images = []
        for ri in repair_images:
            img = ContentFile(ri.image.read(), name=os.path.basename(ri.image.name)) if ri.image else None
            new_repair_images.append(BoilerCardRepairImage(boiler_card_repair=repair_map.get(ri.boiler_card_repair_id), image=img, active=ri.active))
        if new_repair_images:
            BoilerCardRepairImage.objects.bulk_create(new_repair_images)

    # Clone Video
    src_videos = list(Video.objects.filter(model=source))
    new_videos = []
    for v in src_videos:
        v_kwargs = dict(
            title=getattr(v, "title", None) or "",
            category=v.category,
            brand=v.brand,
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
        new_videos.append(Video(**v_kwargs))
    if new_videos:
        Video.objects.bulk_create(new_videos)

    # Clone RoomTermostat
    src_rooms = list(RoomTermostat.objects.filter(model=source))
    new_rooms = []
    for rt in src_rooms:
        rt_kwargs = dict(
            title=getattr(rt, "title", None) or "",
            category=rt.category,
            brand=rt.brand,
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
        new_rooms.append(RoomTermostat(**rt_kwargs))
    created_rooms = RoomTermostat.objects.bulk_create(new_rooms) if new_rooms else []

    # Map old room id -> new room instance
    room_map = {old.id: new for old, new in zip(src_rooms, created_rooms)}

    # Clone RoomTermostatImage
    if room_map:
        room_images = RoomTermostatImage.objects.filter(room_thermostat__in=[r.id for r in src_rooms]).select_related("room_thermostat")
        new_room_images = []
        for rti in room_images:
            img = ContentFile(rti.image.read(), name=os.path.basename(rti.image.name)) if rti.image else None
            new_room_images.append(RoomTermostatImage(room_thermostat=room_map.get(rti.room_thermostat_id), image=img, active=rti.active))
        if new_room_images:
            RoomTermostatImage.objects.bulk_create(new_room_images)

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
