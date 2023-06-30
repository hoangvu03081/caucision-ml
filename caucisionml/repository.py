from sqlalchemy.orm import Session

from . import models
from .database import repository_method
from .models import Project


@repository_method
def get_projects(session: Session):
    return session.query(models.Project).all()


@repository_method
def find_project(session: Session, project_id: str):
    project = session.query(models.Project).filter(models.Project.id == project_id).first()
    session.expunge(project)
    return project


@repository_method
def find_campaign(session: Session, campaign_id: str):
    campaign = session.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    session.expunge(campaign)
    return campaign


@repository_method
def update_project_model(session: Session, project_id: str, model):
    return session.query(models.Project).filter(models.Project.id == project_id).update({'model': model})


@repository_method
def create_default_campaign(session: Session, project_id: str, user_id: str):
    campaign = models.Campaign(
        user_id=user_id,
        project_id=project_id,
        data_imported=True,
        name="Default campaign"
    )
    session.add(campaign)


@repository_method
def update_project_model_trained(session: Session, project_id: str, value):
    return session.query(models.Project).filter(models.Project.id == project_id).update({'model_trained': value})
