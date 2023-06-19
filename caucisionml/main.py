from fastapi import FastAPI, File, Form
from fastapi.responses import StreamingResponse

from typing import Annotated

from .message_queue import initialize_celery
from celery import shared_task

from . import repository as repo
from .scylla import Scylla
from .causal_inference import infer_from_project, infer_from_campaign_data
import pickle
import pandas as pd
import io

app = FastAPI()
celery = initialize_celery()


@shared_task(name='train_model')
def train_model(payload):
    project = repo.find_project(payload['project_id'])
    scylla_db = Scylla()

    df = scylla_db.fetch_project_data(project.data_id())
    user_effects, est, encoder, identified_estimand, causal_model, categories = infer_from_project(
        df, project.control_promotion, project.data_schema, project.causal_graph
    )

    model_data = {'est': est, 'encoder': encoder, 'identified_estimand': identified_estimand,
                  'causal_model': causal_model, 'categories': categories}
    binary_model_data = pickle.dumps(model_data)

    repo.update_project_model(project.id, binary_model_data)

    scylla_db.save_project_estimation(project.campaign_data_id(), user_effects)
    repo.update_project_model_trained(project.id, True)
    repo.create_default_campaign(project.id, project.user_id)


@app.get("/")
async def root():
    pass
    # project = repo.find_project('7572ec20-27b9-4bc4-ad69-81ca21562c73')
    # scylla_db = Scylla()
    #
    # df = scylla_db.fetch_project_data(project.data_id())
    # user_effects, est, encoder, identified_estimand, causal_model = infer_from_project(
    #     df, project.control_promotion, project.data_schema, project.causal_graph
    # )
    # from .scylla import Scylla
    # project = repo.find_project("d1984510-614c-4bba-893d-52946c72880b")
    # df = Scylla().fetch_project_data(project.data_id())
    # user_effects, est, encoder, identified_estimand, model = infer_from_project(
    #     df, project.control_promotion, project.data_schema, project.causal_graph
    # )
    # return project


@app.post("/campaign_data")
async def upload_campaign_data(
        file: Annotated[bytes, File()],
        project_id: Annotated[str, Form()],
        campaign_data_id: Annotated[str, Form()]
):
    project = repo.find_project(project_id)

    csv_io = io.BytesIO(file)
    df = pd.read_csv(csv_io)

    model_data = pickle.loads(project.model)
    identified_estimand = model_data['identified_estimand']
    categories = model_data['categories']
    causal_model = model_data['causal_model']
    est = model_data['est']

    user_effects = infer_from_campaign_data(df, identified_estimand, categories, causal_model, est)
    scylla_db = Scylla()
    scylla_db.save_project_estimation(campaign_data_id, user_effects)

    csv_data = io.StringIO()
    user_effects.to_csv(csv_data, index=False)
    csv_data.seek(0)  # Move the file pointer to the beginning of the file

    # Create a StreamingResponse to return the CSV file
    response = StreamingResponse(iter([csv_data.getvalue()]),
                                 media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=data.csv"

    return response
