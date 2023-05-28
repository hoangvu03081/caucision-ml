from fastapi import FastAPI

from .message_queue import initialize_celery
from celery import shared_task

from . import repository as repo
from .scylla import Scylla
from .causal_inference import infer_from_project
import pickle

app = FastAPI()
celery = initialize_celery()


@shared_task(name='train_model')
def train_model(payload):
    project = repo.find_project(payload['project_id'])
    scylla_db = Scylla()

    df = scylla_db.fetch_project_data(project.data_id())
    user_effects, est, encoder, identified_estimand, causal_model = infer_from_project(
        df, project.control_promotion, project.data_schema, project.causal_graph
    )

    model_data = {'est': est, 'encoder': encoder, 'identified_estimand': identified_estimand,
                  'causal_model': causal_model}
    binary_model_data = pickle.dumps(model_data)

    repo.update_project_model(project.id, binary_model_data)
    scylla_db.save_project_estimation(project.estimation_id(), user_effects)
    repo.update_project_model_trained(project.id, True)
    repo.create_default_campaign(project.id, project.user_id)


@app.get("/")
async def root():
    pass
    # from .scylla import Scylla
    # project = repo.find_project("d1984510-614c-4bba-893d-52946c72880b")
    # df = Scylla().fetch_project_data(project.data_id())
    # user_effects, est, encoder, identified_estimand, model = infer_from_project(
    #     df, project.control_promotion, project.data_schema, project.causal_graph
    # )
    # return project
