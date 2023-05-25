from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Uuid
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, BYTEA
from sqlalchemy.orm import relationship
import inflection

from .database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Uuid, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    user_id = Column(String)
    data_imported = Column(Boolean)
    model_trained = Column(Boolean)
    control_promotion = Column(String)
    causal_graph = Column(String)
    data_schema = Column(JSONB)
    graph_order = Column(ARRAY(String))
    promotions = Column(ARRAY(String))
    model = Column(BYTEA)

    def data_id(self):
        return f"p_{inflection.underscore(str(self.id))}_data"

    def estimation_id(self):
        return f"p_{inflection.underscore(str(self.id))}_est"
