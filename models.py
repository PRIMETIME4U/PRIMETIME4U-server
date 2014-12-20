from google.appengine.ext import db


class DictModel(db.Model):
    def to_dict(self):
        return dict([(p, unicode(getattr(self, p))) for p in self.properties()])


class User(DictModel):
    name = db.StringProperty(required=True)
