from sqlalchemy.ext.declarative import as_declarative


@as_declarative()
class Base:
    def to_dict(self):
        return {field.name: getattr(self, field.name) for field in self.__table__.c}
