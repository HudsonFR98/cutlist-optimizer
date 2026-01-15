from typing import List, Optional
from cutlist_optimizer import models
from cutlist_optimizer.lib.database import DBSession


def get_cutlist(pk: int) -> Optional[models.Cutlist]:
    """Get a cutlist by ID"""
    return models.Cutlist.query.get(pk)


def get_cutlists_by_user(user_id: int) -> List[models.Cutlist]:
    """Get all cutlists for a specific user"""
    return models.Cutlist.query.filter_by(user_id=user_id).order_by(models.Cutlist.created_at.desc()).all()


def create_cutlist(user_id: int, name: Optional[str] = None) -> models.Cutlist:
    """Create a new cutlist"""
    cutlist = models.Cutlist(user_id=user_id, name=name)
    DBSession.add(cutlist)
    DBSession.commit()
    return cutlist


def delete_cutlist(cutlist_id: int) -> bool:
    """Delete a cutlist and its surfaces"""
    cutlist = get_cutlist(cutlist_id)
    if cutlist:
        DBSession.delete(cutlist)
        DBSession.commit()
        return True
    return False


def get_surface(pk: int) -> Optional[models.Surface]:
    """Get a surface by ID"""
    return models.Surface.query.get(pk)


def get_surfaces_by_cutlist(cutlist_id: int) -> List[models.Surface]:
    """Get all surfaces for a specific cutlist"""
    return models.Surface.query.filter_by(cutlist_id=cutlist_id).all()


def create_surface(cutlist_id: int, width: float, height: float, quantity: int = 1) -> models.Surface:
    """Create a new surface"""
    surface = models.Surface(cutlist_id=cutlist_id, width=width, height=height, quantity=quantity)
    DBSession.add(surface)
    DBSession.commit()
    return surface


def delete_surface(surface_id: int) -> bool:
    """Delete a surface"""
    surface = get_surface(surface_id)
    if surface:
        DBSession.delete(surface)
        DBSession.commit()
        return True
    return False


def create_cutlist_with_surfaces(user_id: int, name: Optional[str],
                                 surfaces: List[dict]) -> models.Cutlist:
    """Create a cutlist and its surfaces in a single transaction"""
    cutlist = models.Cutlist(user_id=user_id, name=name)
    DBSession.add(cutlist)
    DBSession.flush()

    for surface in surfaces:
        DBSession.add(models.Surface(
            cutlist_id=cutlist.id,
            width=surface['width'],
            height=surface['height'],
            quantity=surface.get('quantity', 1)
        ))

    DBSession.commit()
    return cutlist
