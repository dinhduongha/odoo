import functools
import typing
import uuid

@functools.total_ordering
class NewId:
    """Pseudo-ids for new records, encapsulating an optional origin id
       (actual record id, can be int or uuid.UUID) and an optional reference.
    """
    __slots__ = ('origin', 'ref', '__hash')  # noqa: RUF023

    def __init__(self, origin=None, ref=None):
        # Convert string UUID to uuid.UUID if needed
        if isinstance(origin, str):
            try:
                origin = uuid.UUID(origin)
            except ValueError:
                pass
        self.origin = origin
        self.ref = ref
        self.__hash = hash(origin or ref or id(self))

    def __bool__(self):
        return False

    def __eq__(self, other):
        if not isinstance(other, NewId):
            return False
        return ((self.origin is not None and other.origin is not None and self.origin == other.origin)
                or (self.ref is not None and other.ref is not None and self.ref == other.ref))

    def __hash__(self):
        return self.__hash

    def __lt__(self, other):
        """Ordering support (int or uuid.UUID origins).

        A NewId(origin=o) sorts just AFTER the real id o; a NewId(origin=None) has
        no anchor and sorts LAST (greater than everything).
        """
        other_origin = other.origin if isinstance(other, NewId) else other
        if self.origin is None:
            # origin-less NewId is the largest: never less than anything
            return False
        if other_origin is None:
            # other is an origin-less NewId (largest) -> self is less
            return isinstance(other, NewId)
        if isinstance(other_origin, type(self.origin)):
            return self.origin < other_origin
        return NotImplemented

    def __repr__(self):
        if self.origin:
            return f"<NewId origin={self.origin!r}>"
        elif self.ref:
            return f"<NewId ref={self.ref!r}>"
        else:
            return f"<NewId 0x{id(self):x}>"

    def __str__(self):
        id_part = self.origin or self.ref or hex(id(self))
        return f"NewId_{id_part}"

# Type alias for ORM fields
# Can be int (legacy), NewId, str (reference), or UUID
IdType: typing.TypeAlias = int | uuid.UUID | NewId | str
